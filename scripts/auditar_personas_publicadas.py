#!/usr/bin/env python3
"""Comprueba, sobre los Parquet publicados, lo que el aviso de privacidad declara.

`PRIVACIDAD.md` y `DATA_LICENSE.md` describen qué datos personales se publican y
cuáles se suprimen. Hasta ahora esa descripción se revisaba a mano: este script
la convierte en una compuerta que lee los archivos servidos en `docs/outputs/`,
no la intención del pipeline.

Comprueba siete cosas:

  1. `fintech_rpsf_lista_entidades`: 36 personas naturales de 264 filas y
     ninguna columna de correo.
  2. `corredoras_bolsa_lista_entidades`: 11 nombres de personas entre 120.
  3. `seguros_bienes_raices`: `rol`, `ubicacion` y `arrendatario` vacíos en todas
     las filas; `comuna`, `ciudad` y `property_id` presentes; y los conteos de
     tasadores que declara el aviso.
  4. `fi_cartera_nacional`: las filas de persona natural llevan el seudónimo
     `EMI-…` en `rut_emisor` y la bandera `rut_omitido_por_ley` coincide con el
     contenido; ninguna columna publica el nombre del emisor.
  5. `fi_bienes_raices`: publicada vacía, como se declara.
  6. El criterio de persona natural, aplicado a **todas** las columnas de RUT del
     catálogo: un objeto que publique RUT de personas sin declararlo hace fallar
     la compuerta.
  7. Los números escritos en `PRIVACIDAD.md` coinciden con lo medido, y el
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
sys.path.insert(0, str(RAIZ))

from pipelines.auto import privacidad  # noqa: E402

DOCS = RAIZ / "docs"
PRIVACIDAD = RAIZ / "PRIVACIDAD.md"
CATALOGO = DOCS / "api" / "v2" / "catalog.json"

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

# Fuentes directas vigentes que el contrato asigna a los objetos publicados.
# El campo `fuente` no reemplaza la procedencia histórica del catálogo CCAF:
# data_manifest.json y ccaf/README.md registran su semilla desde listados SUSESO
# y el Registro de Valores CMF; los estados financieros CCAF son de la CMF.
FUENTES_ESPERADAS = {"CMF", "BCCh", "SPensiones"}


def conectar() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


def parquet(con, ruta: str, vista: str) -> None:
    con.execute(f"CREATE OR REPLACE VIEW {vista} AS SELECT * FROM read_parquet('{ruta}')")


def columnas(con, vista: str) -> list[str]:
    return [fila[0] for fila in con.execute(f"DESCRIBE {vista}").fetchall()]


def _particiones(con, objeto: str) -> bool:
    """Registra el objeto como vista si tiene archivos publicados."""
    ruta = DOCS / "api" / "v2" / "partitions" / f"{objeto}.json"
    if not ruta.exists():
        return False
    partes = json.loads(ruta.read_text(encoding="utf-8"))["particiones"]
    if not partes:
        return False
    glob = "['" + "','".join(f"docs/{p['archivo']}" for p in partes) + "']"
    try:
        con.execute(f"CREATE OR REPLACE VIEW {objeto} AS SELECT * FROM read_parquet({glob})")
    except Exception:
        return False
    return True


def _valores_atipicos(con, objeto: str, columna: str, entidades) -> set:
    """Valores que el criterio marcaría en una columna ya declarada como relleno."""
    if not _particiones(con, objeto) or columna not in columnas(con, objeto):
        return set()
    valores = [fila[0] for fila in con.execute(
        f'SELECT DISTINCT CAST("{columna}" AS VARCHAR) FROM {objeto} WHERE "{columna}" IS NOT NULL'
    ).fetchall()]
    return {v for v in valores if privacidad.es_probable_persona_natural(v, entidades)}


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
    faltantes_control = [c for c in ("emisor_tipo", "rut_omitido_por_ley") if c not in cols]
    if faltantes_control:
        fallos.append(
            "cartera_fi: faltan " + ", ".join(faltantes_control) +
            "; el criterio de supresión deja de ser auditable y el emisor deja de ser seguible"
        )
    else:
        suprimidas, publicadas, con_seudonimo, con_rut = con.execute(
            """SELECT
                 count(*) FILTER (WHERE rut_omitido_por_ley),
                 count(*) FILTER (WHERE NOT rut_omitido_por_ley
                                    AND emisor_tipo = 'persona_natural_probable'),
                 count(*) FILTER (WHERE rut_emisor LIKE 'EMI-%'),
                 count(*) FILTER (WHERE rut_emisor NOT LIKE 'EMI-%' AND rut_emisor IS NOT NULL)
               FROM cartera_fi"""
        ).fetchone()
        # Una sola columna con dos contenidos: el RUT o el seudónimo. La bandera
        # tiene que decir cuál es, y el seudónimo tiene que ser exactamente el que
        # se emitió (prefijo EMI-), para que nadie lo confunda con un RUT.
        inconsistentes = con.execute(
            """SELECT count(*) FROM cartera_fi
               WHERE (rut_omitido_por_ley AND (rut_emisor IS NULL OR rut_emisor NOT LIKE 'EMI-%'))
                  OR (NOT rut_omitido_por_ley AND rut_emisor LIKE 'EMI-%')
                  OR (NOT rut_omitido_por_ley AND emisor_tipo <> 'sin_rut_informado'
                      AND rut_emisor IS NULL)
                  OR (rut_omitido_por_ley AND emisor_tipo <> 'persona_natural_probable')"""
        ).fetchone()[0]
        if inconsistentes:
            fallos.append(
                f"cartera_fi: {inconsistentes} filas donde rut_omitido_por_ley no coincide con rut_emisor"
            )
        # El esquema anterior publicaba el seudónimo en una columna aparte; si
        # reaparece, hay dos versiones de la regla circulando a la vez.
        if "emisor_id" in cols:
            fallos.append(
                "cartera_fi: conserva la columna emisor_id; el identificador va en rut_emisor"
            )
        if suprimidas and publicadas:
            fallos.append(
                f"cartera_fi: mezcla los dos modos ({suprimidas} filas con RUT omitido y "
                f"{publicadas} con RUT publicado); el modo debe ser único por publicación"
            )
        modo = "RUT omitido" if suprimidas else "RUT publicado"
        notas.append(
            f"cartera_fi: {suprimidas:,} filas de persona natural con seudónimo EMI- en rut_emisor "
            f"({con_seudonimo:,} filas) y {con_rut:,} con el RUT de una persona jurídica "
            f"({publicadas:,} personas naturales con RUT publicado, modo {modo})"
        )
        texto_privacidad = PRIVACIDAD.read_text(encoding="utf-8")
        for termino in ("rut_omitido_por_ley", "EMI-"):
            if termino not in texto_privacidad:
                fallos.append(f"aviso: el aviso de privacidad no menciona {termino}")
    if any("nombre" in c.lower() and "emisor" in c.lower() for c in cols):
        fallos.append("cartera_fi: publica el nombre del emisor, que acompañaría al RUT suprimido")

    # --- 5 · Fondos de inversión: bienes raíces vacío ----------------------
    parquet(con, str(DOCS / "outputs/fi/bienes_raices/vacio.parquet"), "fi_bienes_raices")
    vacias = con.execute("SELECT count(*) FROM fi_bienes_raices").fetchone()[0]
    if vacias:
        fallos.append(f"fi_bienes_raices: {vacias} filas; se declara vacía y oculta")

    # --- 6 · El criterio aplicado a todo el catálogo ----------------------
    # La regla de privacidad no se repite en cada tabla: se comprueba sobre todas
    # las columnas de RUT publicadas. Un objeto que empiece a publicar RUT de
    # personas sin declararlo aquí hace fallar la compuerta.
    entidades = privacidad.cargar_entidades_conocidas()
    declarados = privacidad.OBJETOS_CON_RUT_DE_PERSONAS
    excepciones = set(privacidad.RUT_ENTIDADES_FUERA_DEL_PADRON) | {
        valor
        for (objeto, columna) in privacidad.COLUMNAS_CON_VALORES_ATIPICOS
        for valor in _valores_atipicos(con, objeto, columna, entidades)
    }
    escaneadas, hallazgos = 0, []
    for objeto in sorted(p.stem for p in (DOCS / "api" / "v2" / "schema").glob("*.json")):
        columnas_rut = [c["nombre"] for c in json.loads(
            (DOCS / "api" / "v2" / "schema" / f"{objeto}.json").read_text(encoding="utf-8"))["columnas"]
            if "rut" in c["nombre"].lower()]
        if not columnas_rut or not _particiones(con, objeto):
            continue
        for columna in columnas_rut:
            if columna not in columnas(con, objeto):
                continue
            escaneadas += 1
            valores = [fila[0] for fila in con.execute(
                f'SELECT DISTINCT CAST("{columna}" AS VARCHAR) FROM {objeto} WHERE "{columna}" IS NOT NULL'
            ).fetchall()]
            marcados = {v for v in valores
                        if privacidad.es_probable_persona_natural(v, entidades) and v not in excepciones}
            if marcados and objeto not in declarados:
                hallazgos.append(f"{objeto}.{columna} ({len(marcados)} valores, ej. {sorted(marcados)[:3]})")
    if hallazgos:
        fallos.append(
            "catálogo: publica RUT de posibles personas naturales en objetos no declarados: "
            + "; ".join(hallazgos[:6])
        )
    notas.append(
        f"catálogo: {escaneadas} columnas de RUT revisadas con el mismo criterio; "
        f"{len(declarados)} objetos publican RUT de personas a propósito y "
        f"{len(privacidad.COLUMNAS_CON_VALORES_ATIPICOS)} columnas tienen relleno del origen"
    )

    # --- 7 · El aviso dice lo mismo que los archivos ----------------------
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

    # Separar las tres fuentes directas de archivos financieros/series del
    # antecedente SUSESO que forma parte de la procedencia del catálogo CCAF.
    sitio = (DOCS / "index.html").read_text(encoding="utf-8")
    if "SUSESO no entrega datos" in sitio:
        fallos.append("sitio: conserva la afirmación absoluta incorrecta sobre SUSESO")
    if "Archivos financieros y series actuales" not in sitio or "Superintendencia de Pensiones" not in sitio:
        fallos.append("sitio: no identifica las tres fuentes directas actuales")
    if "universo inicial" not in sitio or "lista de SUSESO" not in sitio or "Registro de Valores" not in sitio:
        fallos.append("sitio: no explica la procedencia mixta del universo CCAF")
    if "Los balances y resultados CCAF también provienen de la CMF" not in sitio:
        fallos.append("sitio: no distingue la fuente de los estados financieros CCAF")

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
