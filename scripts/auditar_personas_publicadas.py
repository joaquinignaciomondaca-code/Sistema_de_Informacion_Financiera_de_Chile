#!/usr/bin/env python3
"""Comprueba, sobre los Parquet publicados, lo que el aviso de privacidad declara.

`PRIVACIDAD.md` y `DATA_LICENSE.md` describen qué datos personales se publican y
cuáles se suprimen. Hasta ahora esa descripción se revisaba a mano: este script
la convierte en una compuerta que lee los archivos servidos en `docs/outputs/`,
no la intención del pipeline.

Comprueba seis cosas:

  1. `fintech_rpsf_lista_entidades`: 36 personas naturales de 264 filas y
     ninguna columna de correo.
  2. `corredoras_bolsa_lista_entidades`: 11 nombres de personas entre 120.
  3. `seguros_bienes_raices`: `rol`, `ubicacion` y `arrendatario` vacíos en todas
     las filas; `comuna`, `ciudad` y `property_id` presentes; y los conteos de
     tasadores que declara el aviso.
  4. `fi_cartera_nacional`: ningún RUT en las filas clasificadas como persona
     natural probable y ninguna columna con el nombre del emisor.
  5. `fi_bienes_raices`: publicada vacía, como se declara.
  6. Los números escritos en `PRIVACIDAD.md` coinciden con lo medido, y el
     catálogo sólo declara fuentes que efectivamente entregan datos.

Uso:
    python3 scripts/auditar_personas_publicadas.py            # informe
    python3 scripts/auditar_personas_publicadas.py --verbose  # con el detalle
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
PRIVACIDAD = RAIZ / "PRIVACIDAD.md"
CATALOGO = DOCS / "api" / "v1" / "catalog.json"

# Palabras que delatan a una sociedad. Sirven para separar, en las nóminas
# publicadas, los nombres de personas de las razones sociales. No es una
# clasificación jurídica: es el mismo criterio con el que se redactó el aviso.
MARCAS_SOCIEDAD = re.compile(
    r"\bS\.?A\.?\b|\bLTDA\b|\bLIMITADA\b|\bSPA\b|\bCORREDOR\w*\b|\bBOLSA\b|\bSOCIEDAD\b|\bBANCO\b|\bCONSULT\w*\b|"
    r"\bSERVIC\w*\b|\bINMOBILIAR\w*\b|\bTASACION\w*\b|\bPROPIEDAD\w*\b|"
    r"\bCOLLIERS\b|\bC&W\b|\bTINSA\b|\bTRANSSA\b|\bAGENCIA\b|\bCIA\b|"
    r"\bCOMPA\w*\b|\bGEST\w*\b|\bVALOR\b|\bINVERSION\w*\b|"
    r"\bDESARROLLO\b|\bNEGOCIOS\b|\bINGENIER\w*\b|\bARQUITECT\w*\b|"
    r"\bASESOR\w*\b|&|\d",
    re.I,
)

# Fuentes que el sistema declara. SUSESO no está: aparece como regulador en la
# lista de cajas de compensación, pero los estados financieros vienen de la CMF.
FUENTES_ESPERADAS = {"CMF", "BCCh", "SPensiones"}


def conectar() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


def parquet(con, ruta: str, vista: str) -> None:
    con.execute(f"CREATE OR REPLACE VIEW {vista} AS SELECT * FROM read_parquet('{ruta}')")


def columnas(con, vista: str) -> list[str]:
    return [fila[0] for fila in con.execute(f"DESCRIBE {vista}").fetchall()]


def main() -> int:
    verbose = "--verbose" in sys.argv
    fallos: list[str] = []
    notas: list[str] = []
    con = conectar()

    # --- 1 · FinTech -------------------------------------------------------
    parquet(con, str(DOCS / "outputs/fintech/fintech_rpsf_maestro.parquet"), "fintech")
    filas, naturales = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE tipo_persona = 'Persona Natural') FROM fintech"
    ).fetchone()
    cols = columnas(con, "fintech")
    if filas != 264:
        fallos.append(f"fintech: {filas} filas; el aviso declara 264 prestadores")
    if naturales != 36:
        fallos.append(f"fintech: {naturales} personas naturales; el aviso declara 36")
    if any("email" in c.lower() or "correo" in c.lower() for c in cols):
        fallos.append("fintech: sigue publicada una columna de correo")
    notas.append(f"fintech: {filas} filas · {naturales} personas naturales · sin correo")

    # --- 2 · Corredoras ----------------------------------------------------
    parquet(con, str(DOCS / "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet"), "corredoras")
    nombres = [n for (n,) in con.execute("SELECT nombre_empresa FROM corredoras").fetchall()]
    personas = [n for n in nombres if not MARCAS_SOCIEDAD.search(n)]
    if len(nombres) != 120:
        fallos.append(f"corredoras: {len(nombres)} filas; el aviso declara 120")
    if len(personas) != 11:
        fallos.append(f"corredoras: {len(personas)} nombres de persona; el aviso declara 11")
    notas.append(f"corredoras: {len(nombres)} filas · {len(personas)} a nombre de persona")

    # --- 3 · Bienes raíces de seguros -------------------------------------
    parquet(con, str(DOCS / "outputs/seguros/bienes_raices/*.parquet"), "bienes_raices")
    cols = columnas(con, "bienes_raices")
    total = con.execute("SELECT count(*) FROM bienes_raices").fetchone()[0]
    for columna in ("rol", "ubicacion", "arrendatario"):
        if columna not in cols:
            fallos.append(f"bienes_raices: falta la columna {columna}; no se puede probar la supresión")
            continue
        con_datos = con.execute(f"SELECT count(*) FROM bienes_raices WHERE {columna} IS NOT NULL").fetchone()[0]
        if con_datos:
            fallos.append(f"bienes_raices: {con_datos} filas conservan {columna}")
    for columna in ("comuna", "ciudad", "property_id"):
        if columna not in cols:
            fallos.append(f"bienes_raices: falta {columna}, que el aviso declara publicada")
    t1, t2, union = con.execute(
        """SELECT count(DISTINCT nombre_del_tasador_1), count(DISTINCT nombre_del_tasador_2),
                  (SELECT count(*) FROM (
                     SELECT nombre_del_tasador_1 AS n FROM bienes_raices WHERE nombre_del_tasador_1 IS NOT NULL
                     UNION SELECT nombre_del_tasador_2 FROM bienes_raices WHERE nombre_del_tasador_2 IS NOT NULL))
           FROM bienes_raices"""
    ).fetchone()
    notas.append(
        f"bienes_raices: {total} filas · rol/ubicacion/arrendatario vacíos · "
        f"tasadores {t1} y {t2} ({union} distintos)"
    )

    # --- 4 · Cartera nacional de fondos de inversión -----------------------
    parquet(con, str(DOCS / "outputs/fi/cartera_nacional/*.parquet"), "cartera_fi")
    cols = columnas(con, "cartera_fi")
    faltantes_control = [c for c in ("emisor_tipo", "emisor_id", "rut_omitido_por_ley") if c not in cols]
    if faltantes_control:
        fallos.append(
            "cartera_fi: faltan " + ", ".join(faltantes_control) +
            "; el criterio de supresión deja de ser auditable y el emisor deja de ser seguible"
        )
    else:
        suprimidas, publicadas, con_id = con.execute(
            """SELECT
                 count(*) FILTER (WHERE rut_omitido_por_ley),
                 count(*) FILTER (WHERE NOT rut_omitido_por_ley
                                    AND emisor_tipo = 'persona_natural_probable'),
                 count(*) FILTER (WHERE emisor_id IS NOT NULL)
               FROM cartera_fi"""
        ).fetchone()
        # Las dos caras de la misma moneda: si la bandera dice «omitido», el RUT
        # no puede estar; si dice «publicado», el RUT tiene que estar.
        inconsistentes = con.execute(
            """SELECT count(*) FROM cartera_fi
               WHERE (rut_omitido_por_ley AND rut_emisor IS NOT NULL)
                  OR (NOT rut_omitido_por_ley AND emisor_tipo <> 'sin_rut_informado'
                      AND rut_emisor IS NULL)
                  OR (rut_omitido_por_ley AND emisor_tipo <> 'persona_natural_probable')"""
        ).fetchone()[0]
        if inconsistentes:
            fallos.append(
                f"cartera_fi: {inconsistentes} filas donde rut_omitido_por_ley no coincide con rut_emisor"
            )
        # El seudónimo reemplaza al RUT omitido y sólo a él: en la persona jurídica
        # la clave es el RUT publicado, así que un emisor_id ahí sería redundante.
        desalineados = con.execute(
            """SELECT count(*) FROM cartera_fi
               WHERE (emisor_id IS NOT NULL) <> rut_omitido_por_ley"""
        ).fetchone()[0]
        if desalineados:
            fallos.append(
                f"cartera_fi: {desalineados} filas donde emisor_id no coincide con rut_omitido_por_ley"
            )
        if suprimidas and publicadas:
            fallos.append(
                f"cartera_fi: mezcla los dos modos ({suprimidas} filas con RUT omitido y "
                f"{publicadas} con RUT publicado); el modo debe ser único por publicación"
            )
        modo = "RUT omitido" if suprimidas else "RUT publicado"
        notas.append(
            f"cartera_fi: {suprimidas:,} filas de persona natural con RUT omitido y emisor_id "
            f"({con_id:,} seudónimos); {publicadas:,} con RUT publicado (modo {modo}); las "
            "personas jurídicas conservan su RUT y no llevan seudónimo"
        )
        texto_privacidad = PRIVACIDAD.read_text(encoding="utf-8")
        for termino in ("emisor_id", "rut_omitido_por_ley"):
            if termino not in texto_privacidad:
                fallos.append(f"aviso: el aviso de privacidad no menciona {termino}")
    if any("nombre" in c.lower() and "emisor" in c.lower() for c in cols):
        fallos.append("cartera_fi: publica el nombre del emisor, que acompañaría al RUT suprimido")

    # --- 5 · Fondos de inversión: bienes raíces vacío ----------------------
    parquet(con, str(DOCS / "outputs/fi/bienes_raices/_vacio.parquet"), "fi_bienes_raices")
    vacias = con.execute("SELECT count(*) FROM fi_bienes_raices").fetchone()[0]
    if vacias:
        fallos.append(f"fi_bienes_raices: {vacias} filas; se declara vacía y oculta")

    # --- 6 · El aviso dice lo mismo que los archivos ----------------------
    texto = PRIVACIDAD.read_text(encoding="utf-8")
    esperado = {
        "personas naturales del aviso": (r"(\d+) personas naturales", naturales),
        "corredores del aviso": (r"(\d+) corredores", len(personas)),
        "nombres de tasadores del aviso": (r"(\d+) nombres de tasadores", union),
        "tasadores de la primera tasación": (r"\((\d+) en la tasación 1", t1),
        "tasadores de la segunda tasación": (r"(\d+) en la tasación 2\)", t2),
    }
    for etiqueta, (patron, medido) in esperado.items():
        encontrado = re.search(patron, texto)
        if not encontrado:
            fallos.append(f"aviso: no se encuentra la cifra de {etiqueta}")
        elif int(encontrado.group(1)) != medido:
            fallos.append(
                f"aviso: {etiqueta} dice {encontrado.group(1)} y los archivos publicados tienen {medido}"
            )

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    fuentes = sorted({objeto.get("fuente") for objeto in catalogo["objetos"]})
    sobrantes = set(fuentes) - FUENTES_ESPERADAS
    if sobrantes:
        fallos.append(f"catálogo: declara fuentes que no están verificadas: {', '.join(sorted(sobrantes))}")
    faltantes = FUENTES_ESPERADAS - set(fuentes)
    if faltantes:
        fallos.append(f"catálogo: faltan fuentes verificadas: {', '.join(sorted(faltantes))}")
    notas.append("catálogo: fuentes " + ", ".join(fuentes))

    # El sitio contaba a SUSESO entre las fuentes de datos, cuando sólo aparece
    # como regulador en el catálogo de cajas de compensación.
    sitio = (DOCS / "index.html").read_text(encoding="utf-8")
    if "SUSESO" in sitio and "SUSESO no entrega datos" not in sitio:
        fallos.append("sitio: presenta a SUSESO como fuente de datos")
    if "SUSESO no entrega datos" not in sitio:
        fallos.append("sitio: no aclara que SUSESO no entrega datos")

    print("Privacidad: lo que el aviso declara, comprobado sobre los Parquet publicados")
    if verbose:
        for nota in notas:
            print(f"  · {nota}")
    for fallo in fallos:
        print(f"[FALLA] {fallo}")
    if fallos:
        print(f"\nRESULTADO: {len(fallos)} discrepancia(s) entre el aviso y los archivos publicados")
        return 1
    print(f"\nRESULTADO: el aviso de privacidad coincide con lo publicado ({len(notas)} comprobaciones)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
