"""Reconstruye la columna `rut_emisor` de fi.cartera_nacional.

La regla es una sola columna: el RUT del emisor si es una persona jurídica y un
seudónimo estable `EMI-…` en su lugar si es una persona natural. El RUT de esas
personas se suprimió en el commit `3b88beb` y desde entonces no está en el
Parquet publicado, así que el seudónimo no se puede recalcular desde el archivo:
este script lee la versión **anterior** al commit de privacidad desde el historial
de git, la cruza fila por fila con la versión publicada y escribe:

  rut_emisor            el RUT original, o el seudónimo EMI-… si esa fila se omitió
  rut_omitido_por_ley   verdadero cuando rut_emisor trae el seudónimo

Es idempotente: si las columnas ya están como deben, no reescribe. Uso:

    python scripts/reconstruir_rut_emisor.py            # informa
    python scripts/reconstruir_rut_emisor.py --apply    # escribe

Si el entorno define `SIF_PRIV_SALT`, el seudónimo deja de ser reproducible por
terceros; sin la variable queda determinista, igual que `property_id`.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pipelines.auto import privacidad  # noqa: E402

DIRECTORIO = RAIZ / "docs" / "outputs" / "fi" / "cartera_nacional"
COMMIT_PRIVACIDAD = "3b88beb"
# Columnas que identifican la fila entre la versión histórica y la publicada.
CLAVES = ("periodo", "run_fondo")


def leer_historico(ruta: Path) -> pa.Table:
    """Versión del archivo en el commit inmediatamente anterior a la privacidad."""
    relativa = ruta.relative_to(RAIZ).as_posix()
    crudo = subprocess.run(
        ["git", "show", f"{COMMIT_PRIVACIDAD}^:{relativa}"],
        cwd=RAIZ, capture_output=True, check=True,
    ).stdout
    return pq.read_table(io.BytesIO(crudo))


def escribir(ruta: Path, tabla: pa.Table) -> None:
    tmp = ruta.with_suffix(".tmp")
    pq.write_table(tabla, tmp, compression="zstd")
    tmp.replace(ruta)


def procesar(ruta: Path, apply: bool) -> tuple[bool, str]:
    publicado = pq.read_table(ruta)
    nombres = publicado.column_names
    if "rut_emisor" not in nombres or "emisor_tipo" not in nombres:
        return False, "sin las columnas de la regla"

    historico = leer_historico(ruta)
    if historico.num_rows != publicado.num_rows:
        return False, f"el histórico tiene {historico.num_rows:,} filas y el publicado {publicado.num_rows:,}"
    for clave in CLAVES:
        if historico.column(clave).to_pylist() != publicado.column(clave).to_pylist():
            return False, f"las filas no están alineadas por «{clave}»"

    rut_original = historico.column("rut_emisor").to_pylist()
    rut_publicado = publicado.column("rut_emisor").to_pylist()
    tipos = publicado.column("emisor_tipo").to_pylist()

    # El RUT publicado, cuando existe, tiene que ser el mismo del histórico:
    # si no, el archivo se regeneró desde otra fuente y no corresponde cruzarlo.
    distintos = sum(1 for actual, original in zip(rut_publicado, rut_original)
                    if actual is not None and not privacidad.es_seudonimo(actual)
                    and str(actual) != str(original))
    if distintos:
        return False, f"{distintos:,} RUT publicados no coinciden con el histórico"

    omitidos = [
        original is not None and tipo == privacidad.TIPO_NATURAL
        and (actual is None or privacidad.es_seudonimo(actual))
        for actual, original, tipo in zip(rut_publicado, rut_original, tipos)
    ]
    seudonimos = [
        privacidad.seudonimo_emisor(valor, privacidad.sal_privada()) if omitido else None
        for valor, omitido in zip(rut_original, omitidos)
    ]

    # Una sola columna de identificador: el RUT si se publica, el seudónimo si no.
    valores = [seudonimo if omitido else original
               for seudonimo, original, omitido in zip(seudonimos, rut_original, omitidos)]
    # La columna conserva el lugar que tenía en el esquema del publicador, para que
    # un archivo reconstruido y uno generado desde la fuente sean idénticos.
    posicion = list(historico.column_names).index("rut_emisor")
    previos = publicado.column("rut_emisor").to_pylist()
    ya_listo = (previos == valores and privacidad.COLUMNA_RUT_OMITIDO in nombres
                and "emisor_id" not in nombres
                and list(nombres).index("rut_emisor") == posicion)
    if ya_listo:
        return False, "ya aplicado"

    tabla = publicado
    for nombre in ("rut_emisor", privacidad.COLUMNA_RUT_OMITIDO, "emisor_id"):
        if nombre in tabla.column_names:
            tabla = tabla.drop_columns([nombre])
    tabla = tabla.append_column("rut_emisor", pa.array(valores, type=pa.string()))
    tabla = tabla.append_column(privacidad.COLUMNA_RUT_OMITIDO, pa.array(omitidos, type=pa.bool_()))
    orden = [c for c in tabla.column_names if c != "rut_emisor"]
    orden.insert(posicion, "rut_emisor")
    tabla = tabla.select(orden)
    escribir(ruta, tabla) if apply else None
    return True, (f"{sum(omitidos):,} filas con seudónimo · "
                  f"{sum(1 for v in valores if v):,} identificadores")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="escribe los Parquet (por omisión sólo informa)")
    args = parser.parse_args()
    if not args.apply:
        print("Dry-run: no se escribe nada. Agrega --apply para aplicar los cambios.\n")

    archivos = sorted(DIRECTORIO.glob("*.parquet"))
    tocados, fallos = 0, 0
    for ruta in archivos:
        try:
            cambio, detalle = procesar(ruta, args.apply)
        except subprocess.CalledProcessError:
            print(f"   ! {ruta.name}: no está en el historial de git, se omite")
            fallos += 1
            continue
        tocados += int(cambio)
        marca = "✓" if cambio and args.apply else ("→" if cambio else "·")
        print(f"   {marca} {ruta.name}: {detalle}")
    print(f"\n{len(archivos)} archivos · {tocados} {'reescritos' if args.apply else 'por reescribir'} · {fallos} omitidos")
    return 0 if not fallos else 1


if __name__ == "__main__":
    raise SystemExit(main())
