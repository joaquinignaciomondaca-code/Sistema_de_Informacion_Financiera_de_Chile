#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill: aplica las reglas de privacidad (pipelines/auto/privacidad.py) a lo ya publicado.

Dos reglas, sobre dos tablas concretas:

  1. `fi.cartera_nacional`: suprime `rut_emisor` cuando probablemente es una
     persona natural y agrega `emisor_tipo` con el criterio aplicado.
  2. `seguros.bienes_raices`: deja de publicar `ubicacion` (dirección exacta) y
     `rol` (identificador tributario del inmueble); agrega `property_id`, un
     seudónimo estable para seguir el mismo bien entre meses.
  3. `fintech.rpsf_maestro`: retira `email_contacto`. El registro identifica al
     prestador por RUT y razón social; el correo permite contactar a la persona
     y 46 de los 264 correos publicados eran de dominios personales.

No borra tablas, no cambia cantidades de filas ni montos: sólo protege
identificadores exactos. La referencia a la fuente CMF se mantiene intacta.

Idempotente: en una segunda corrida no escribe nada (y lo dice).

Uso:
    python3 scripts/enmascarar_identificadores.py             # dry-run (informe)
    python3 scripts/enmascarar_identificadores.py --apply     # escribe
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pipelines.auto import privacidad  # noqa: E402

DOCS_OUTPUTS = RAIZ / "docs" / "outputs"
RUTAS = {
    "fi.cartera_nacional": DOCS_OUTPUTS / "fi" / "cartera_nacional",
    "seguros.bienes_raices": DOCS_OUTPUTS / "seguros" / "bienes_raices",
    "fintech.rpsf_maestro": DOCS_OUTPUTS / "fintech",
}


def codec_de(ruta: Path) -> str:
    md = pq.ParquetFile(ruta).metadata
    codecs = {md.row_group(0).column(j).compression for j in range(md.row_group(0).num_columns)}
    return (sorted(codecs)[0] or "snappy").lower()


def escribir(ruta: Path, tabla: pa.Table, apply: bool) -> None:
    if not apply:
        return
    tmp = ruta.with_suffix(".parquet.tmp")
    # Sin metadata key-value: el esquema físico es la fuente de verdad y la
    # metadata heredada quedaría obsoleta.
    escritor = pq.ParquetWriter(tmp, tabla.schema.remove_metadata(), compression=codec_de(ruta))
    escritor.write_table(tabla)
    escritor.close()
    tmp.replace(ruta)


def con_columna(tabla: pa.Table, nombre: str, valores, tipo=pa.string()) -> pa.Table:
    """Agrega (o reemplaza) una columna al final, conservando las anteriores."""
    if nombre in tabla.column_names:
        tabla = tabla.drop_columns([nombre])
    return tabla.append_column(nombre, pa.array(valores, type=tipo))


# ---------------------------------------------------------------------------
# fi.cartera_nacional
# ---------------------------------------------------------------------------
def procesar_cartera_nacional(ruta: Path, entidades: set, apply: bool) -> tuple[bool, str]:
    tabla = pq.read_table(ruta)
    nombres = tabla.column_names
    if "rut_emisor" not in nombres:
        return False, "sin columna rut_emisor"

    rut = tabla.column("rut_emisor").to_pylist()
    enmascarados, tipos = privacidad.enmascarar_columna(rut, entidades)
    # Un RUT ya suprimido no se puede volver a clasificar: el recálculo diría
    # «sin_rut_informado» y borraría la evidencia del criterio. Cuando la fila
    # ya traía su tipo y su seudónimo, se conservan.
    previos_tipo = tabla.column("emisor_tipo").to_pylist() if "emisor_tipo" in nombres else None
    previos_id = (tabla.column(privacidad.COLUMNA_EMISOR_ID).to_pylist()
                  if privacidad.COLUMNA_EMISOR_ID in nombres else None)
    if previos_tipo and previos_id:
        tipos = [previo if valor is None and previo == privacidad.TIPO_NATURAL else tipo
                 for valor, previo, tipo in zip(rut, previos_tipo, tipos)]
    suprimidos = sum(1 for original, nuevo in zip(rut, enmascarados)
                     if privacidad.cuerpo_rut(original) is not None and nuevo is None)
    # «Ya aplicado» no se puede decidir comparando columnas recalculadas: una vez
    # suprimido el RUT, la regla ya no puede reproducirlo y el recálculo diría
    # «sin_rut_informado». El criterio es: la columna que documenta la regla
    # existe y no queda ningún RUT que debiera suprimirse.
    pendientes = sum(1 for valor in rut if privacidad.es_probable_persona_natural(valor, entidades))
    modo = privacidad.modo_publicacion_rut()
    # Las tres columnas se escriben juntas: si falta cualquiera, el archivo se
    # vuelve a procesar para completarlas (el relleno es idempotente).
    completo = all(c in nombres for c in ("emisor_tipo", privacidad.COLUMNA_EMISOR_ID,
                                          privacidad.COLUMNA_RUT_OMITIDO))
    if completo and (pendientes == 0 or modo == privacidad.MODO_PUBLICAR):
        return False, f"ya aplicado (modo {modo})"

    if modo == privacidad.MODO_PUBLICAR and pendientes:
        return False, (f"{pendientes:,} RUT ya suprimidos en el archivo publicado: el modo "
                       "publicar exige reprocesar desde la fuente, no desde el Parquet")

    sal = privacidad.sal_privada()
    tabla = con_columna(tabla, "rut_emisor", rut if modo == privacidad.MODO_PUBLICAR else enmascarados)
    tabla = con_columna(tabla, "emisor_tipo", tipos)
    omitidos = [tipo == privacidad.TIPO_NATURAL and modo == privacidad.MODO_SUPRIMIR
                for tipo in tipos]
    # El seudónimo sólo existe donde falta el RUT: en la persona jurídica la clave
    # es el propio RUT publicado. Si la fila ya venía suprimida, su id se hereda,
    # porque el RUT que lo originó ya no está en el archivo.
    ids = [privacidad.emisor_id(valor, sal) if omitido else None
           for valor, omitido in zip(rut, omitidos)]
    if previos_id:
        ids = [previo if nuevo is None and omitido and previo else nuevo
               for nuevo, omitido, previo in zip(ids, omitidos, previos_id)]
    tabla = con_columna(tabla, privacidad.COLUMNA_EMISOR_ID, ids)
    tabla = con_columna(tabla, privacidad.COLUMNA_RUT_OMITIDO, omitidos, tipo=pa.bool_())
    escribir(ruta, tabla, apply)
    verbo = "publicados" if modo == privacidad.MODO_PUBLICAR else "suprimidos"
    return True, f"{suprimidos:,} RUT {verbo} de {len(rut):,} filas (modo {modo})"


# ---------------------------------------------------------------------------
# seguros.bienes_raices
# ---------------------------------------------------------------------------
def procesar_bienes_raices(ruta: Path, apply: bool, sal: str) -> tuple[bool, str]:
    tabla = pq.read_table(ruta)
    nombres = tabla.column_names
    if not any(c in nombres for c in privacidad.COLUMNAS_RETIRADAS):
        return False, "sin columnas sensibles"

    roles = tabla.column("rol").to_pylist() if "rol" in nombres else [None] * tabla.num_rows
    aseguradoras = (tabla.column("rut_aseguradora").to_pylist()
                    if "rut_aseguradora" in nombres else [None] * tabla.num_rows)
    # El seudónimo se calcula desde el rol, que después deja de existir: si el
    # archivo ya estaba protegido, se conserva el id que tiene en vez de
    # recalcularlo desde un rol vacío (eso lo borraría en la segunda corrida).
    previos = (tabla.column("property_id").to_pylist()
               if "property_id" in nombres else [None] * tabla.num_rows)
    ids = []
    for rut, rol, previo in zip(aseguradoras, roles, previos):
        ids.append(privacidad.property_id(rut, rol, sal) if privacidad.normalizar_rol(rol) else previo)
    with_rol = sum(1 for r in roles if privacidad.normalizar_rol(r))
    # La dirección se llama «ubicacion» (formato desde 2024-12) o «direccion»
    # (archivos anteriores): se cuentan y se retiran todas las que existan.
    direcciones = [c for c in privacidad.COLUMNAS_DIRECCION if c in nombres]
    with_dir = 0
    for columna in direcciones:
        with_dir += sum(1 for u in tabla.column(columna).to_pylist()
                        if u is not None and str(u).strip())

    retiradas = [c for c in privacidad.COLUMNAS_RETIRADAS if c in nombres]
    # Mismo criterio que en cartera: se considera aplicado cuando el seudónimo
    # existe y ya no queda ninguna dirección ni rol por retirar.
    ya_listo = "property_id" in nombres and all(
        all(v is None for v in tabla.column(c).to_pylist()) for c in retiradas)
    if ya_listo:
        return False, "ya aplicado"

    for columna in retiradas:
        tabla = con_columna(tabla, columna, [None] * tabla.num_rows)
    tabla = con_columna(tabla, "property_id", ids)
    escribir(ruta, tabla, apply)
    return True, f"{with_dir:,} direcciones y {with_rol:,} roles retirados; {len(set(i for i in ids if i)):,} property_id"


# ---------------------------------------------------------------------------
# fintech.rpsf_maestro (contacto)
# ---------------------------------------------------------------------------
def procesar_fintech(ruta: Path, apply: bool) -> tuple[bool, str]:
    tabla = pq.read_table(ruta)
    retiradas = [c for c in privacidad.COLUMNAS_CONTACTO if c in tabla.column_names]
    if not retiradas:
        return False, "ya aplicado"
    con_dato = sum(
        1 for columna in retiradas
        for valor in tabla.column(columna).to_pylist()
        if valor is not None and str(valor).strip()
    )
    tabla = tabla.drop_columns(retiradas)
    escribir(ruta, tabla, apply)
    return True, f"{con_dato:,} contactos retirados ({', '.join(retiradas)})"


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica las reglas de privacidad a lo ya publicado.")
    parser.add_argument("--apply", action="store_true", help="escribe los Parquet (por omisión sólo informa)")
    args = parser.parse_args()

    if not args.apply:
        print("Dry-run: no se escribe nada. Agrega --apply para aplicar los cambios.\n")

    entidades = privacidad.cargar_entidades_conocidas()
    sal = privacidad.sal_privada()
    print(f"Entidades jurídicas reconocidas en los registros publicados: {len(entidades):,}")
    print(f"Seudónimos de bienes raíces: {'con sal secreta (SIF_PRIV_SALT)' if sal else 'deterministas (sin sal)'}\n")

    tocados = 0
    for nombre, directorio in RUTAS.items():
        if not directorio.exists():
            print(f"{nombre}: sin directorio {directorio}")
            continue
        archivos = sorted(directorio.glob("*.parquet"))
        print(f"── {nombre}: {len(archivos)} archivos")
        for ruta in archivos:
            if nombre.endswith("cartera_nacional"):
                cambio, detalle = procesar_cartera_nacional(ruta, entidades, args.apply)
            elif nombre.startswith("fintech"):
                cambio, detalle = procesar_fintech(ruta, args.apply)
            else:
                cambio, detalle = procesar_bienes_raices(ruta, args.apply, sal)
            if cambio:
                tocados += 1
            marca = "·" if not cambio else ("✓" if args.apply else "→")
            print(f"   {marca} {ruta.name}: {detalle}")
        print()

    if args.apply:
        print(f"Listo: {tocados} archivos reescritos. Regenera el catálogo con "
              "scripts/build_download_catalog.py y la reproducibilidad con "
              "scripts/construir_reproducibilidad.py.")
    else:
        print(f"Se reescribirían {tocados} archivos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
