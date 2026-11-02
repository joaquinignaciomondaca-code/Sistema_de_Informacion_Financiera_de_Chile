#!/usr/bin/env python3
"""Publica los *marts* de Looker Studio (CSV estático) derivados del Parquet publicado.

Looker Studio no lee Parquet y este sitio no tiene un motor SQL remoto: GitHub
Pages sirve archivos y no ejecuta consultas. Así que la conexión se resuelve
donde sí cabe, igual que los resultados de la API: se calculan las agregaciones
**en el build** y cada *mart* se publica como un CSV con grano declarado.

    docs/looker/marts/{id}.csv     una tabla por dashboard, en grano mensual o trimestral
    docs/looker/catalogo.json      qué hay, con qué columnas, en qué unidad y con qué huella

Un *mart* es una tabla pensada para graficar: una fila por período y dimensión,
sin columnas de control interno, con una columna `fecha` real (primer día del
período) para que Looker Studio la reconozca como eje temporal. No reemplaza al
Parquet —que sigue siendo el detalle instrumento por instrumento— y no admite
SQL arbitrario: para eso está el catálogo API v2.

Los CSV son deliberadamente chicos: el catálogo completo pesa ~500 MB, y estos
marts suman unos pocos MB porque cada uno agrega. Así caben en las rutas que
Looker Studio sí soporta (carga de CSV, Google Sheets, conector comunitario).

Uso:
    python3 scripts/build_marts_looker.py             # escribe docs/looker/
    python3 scripts/build_marts_looker.py --check     # falla si están atrasados
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
sys.path.insert(0, str(RAIZ / "scripts"))

from version_contrato import API_VERSION  # noqa: E402

V2 = DOCS / "api" / API_VERSION
SALIDA = DOCS / "looker"
MARTS = SALIDA / "marts"
BASE = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile"

# --------------------------------------------------------------------------- #
# Series macro que entran en los dos marts de contexto.
#
# (serie, nombre, grupo, unidad, frecuencia, tabla, columna)
# El nombre, el grupo y la unidad son los mismos de `macro_series_catalogo`; se
# escriben acá porque el mapeo tabla/columna no es derivable del catálogo.
# --------------------------------------------------------------------------- #
SERIES_MACRO = [
    ("imacec", "Imacec empalmado", "Actividad", "Índice 2018=100", "Mensual", "macro_imacec", "imacec_empalmado_indice"),
    ("imacec_no_minero", "Imacec no minero", "Actividad", "Índice 2018=100", "Mensual", "macro_imacec", "imacec_no_minero_indice"),
    ("imacec_mineria", "Imacec minería", "Actividad", "Índice 2018=100", "Mensual", "macro_imacec", "imacec_minero_indice"),
    ("imacec_comercio", "Imacec comercio", "Actividad", "Índice 2018=100", "Mensual", "macro_imacec", "imacec_comercio_indice"),
    ("imacec_servicios", "Imacec servicios", "Actividad", "Índice 2018=100", "Mensual", "macro_imacec", "imacec_servicios_indice"),
    ("pib", "PIB trimestral (volumen)", "Actividad", "Miles de millones CLP encadenados", "Trimestral", "macro_pib_trimestral", "pib_encadenado_miles_mm_clp"),
    ("cobre_diario", "Cobre refinado BML (diario)", "Commodities", "USD por libra", "Diaria", "macro_cobre", "cobre_refinado_usd_por_libra"),
    ("cobre_mensual", "Cobre refinado BML (mensual)", "Commodities", "USD por libra", "Mensual", "macro_cobre", "cobre_referencial_mensual_usd_por_libra"),
    ("oro", "Oro", "Commodities", "USD por onza troy", "Diaria", "macro_metales_preciosos", "oro_usd_por_onza_troy"),
    ("plata", "Plata", "Commodities", "USD por onza troy", "Diaria", "macro_metales_preciosos", "plata_usd_por_onza_troy"),
    ("eee_ipc_11m", "Encuesta de expectativas (EEE): inflación a 11 meses", "Expectativas", "%", "Mensual", "macro_expectativas_inflacion", "expectativa_inflacion_ipc_11_meses_pct"),
    ("eee_ipc_23m", "Encuesta de expectativas (EEE): inflación a 23 meses", "Expectativas", "%", "Mensual", "macro_expectativas_inflacion", "expectativa_inflacion_ipc_23_meses_pct"),
    ("eee_tpm_11m", "Encuesta de expectativas (EEE): TPM a 11 meses", "Expectativas", "%", "Mensual", "macro_expectativas_tpm", "expectativa_tpm_11_meses_pct"),
    ("eee_tpm_23m", "Encuesta de expectativas (EEE): TPM a 23 meses", "Expectativas", "%", "Mensual", "macro_expectativas_tpm", "expectativa_tpm_23_meses_pct"),
    ("eof_ipc_12m", "Encuesta de operadores financieros (EOF): inflación a 12 meses", "Expectativas", "%", "Diaria", "macro_expectativas_operadores", "expectativa_inflacion_12_meses_pct"),
    ("eof_tpm_12m", "Encuesta de operadores financieros (EOF): TPM a 12 meses", "Expectativas", "%", "Diaria", "macro_expectativas_operadores", "expectativa_tpm_12_meses_pct"),
    ("deuda_publica_pib", "Deuda bruta del Gobierno Central", "Fiscal", "% del PIB", "Trimestral", "macro_deuda_publica_pct_pib", "deuda_bruta_gobierno_central_pct_pib"),
    ("asalariados", "Asalariados", "Mercado laboral", "Miles de personas", "Mensual", "macro_mercado_laboral", "asalariados_miles_personas"),
    ("desocupacion", "Tasa de desocupación nacional", "Mercado laboral", "%", "Mensual", "macro_mercado_laboral", "desocupacion_pct"),
    ("fuerza_trabajo", "Fuerza de trabajo", "Mercado laboral", "Miles de personas", "Mensual", "macro_mercado_laboral", "fuerza_trabajo_miles_personas"),
    ("ocupados", "Ocupados", "Mercado laboral", "Miles de personas", "Mensual", "macro_mercado_laboral", "ocupados_miles_personas"),
    ("ipc_indice", "IPC general", "Precios y reajustes", "Índice 2023=100", "Mensual", "macro_inflacion_ipc", "ipc_indice"),
    ("ipc_var_anual", "IPC, variación en 12 meses", "Precios y reajustes", "%", "Mensual", "macro_inflacion_ipc", "ipc_var_anual_pct"),
    ("ipc_var_mensual", "IPC, variación mensual", "Precios y reajustes", "%", "Mensual", "macro_inflacion_ipc", "ipc_var_mensual_pct"),
    ("uf", "Unidad de fomento", "Precios y reajustes", "CLP", "Diaria", "macro_uf", "uf_valor_clp"),
    ("utm", "Unidad tributaria mensual", "Precios y reajustes", "CLP", "Mensual", "macro_utm", "utm_valor_clp"),
    ("fed_funds", "Tasa de política monetaria de EE.UU.", "Sector externo", "%", "Diaria", "macro_tasa_referencia_fed", "tasa_fed_funds_pct"),
    ("reservas", "Reservas internacionales", "Sector externo", "Millones de USD", "Mensual", "macro_reservas_internacionales", "reservas_internacionales_millones_usd"),
    ("bcp_10y", "Bonos en pesos 10 años (BCP/BTP)", "Tasas", "%", "Diaria", "macro_curva_bonos_pesos", "rendimiento_bono_pesos_10_anos_pct"),
    ("bcp_2y", "Bonos en pesos 2 años (BCP/BTP)", "Tasas", "%", "Diaria", "macro_curva_bonos_pesos", "rendimiento_bono_pesos_2_anos_pct"),
    ("bcp_5y", "Bonos en pesos 5 años (BCP/BTP)", "Tasas", "%", "Diaria", "macro_curva_bonos_pesos", "rendimiento_bono_pesos_5_anos_pct"),
    ("bcu_10y", "Bonos en UF 10 años (BCU/BTU)", "Tasas", "%", "Diaria", "macro_curva_bonos_uf", "rendimiento_bono_uf_10_anos_pct"),
    ("bcu_1y", "Bonos en UF 1 año (BCU/BTU)", "Tasas", "%", "Diaria", "macro_curva_bonos_uf", "rendimiento_bono_uf_1_ano_pct"),
    ("bcu_20y", "Bonos en UF 20 años (BCU/BTU)", "Tasas", "%", "Diaria", "macro_curva_bonos_uf", "rendimiento_bono_uf_20_anos_pct"),
    ("bcu_2y", "Bonos en UF 2 años (BCU/BTU)", "Tasas", "%", "Diaria", "macro_curva_bonos_uf", "rendimiento_bono_uf_2_anos_pct"),
    ("bcu_30y", "Bonos en UF 30 años (BCU/BTU)", "Tasas", "%", "Diaria", "macro_curva_bonos_uf", "rendimiento_bono_uf_30_anos_pct"),
    ("bcu_5y", "Bonos en UF 5 años (BCU/BTU)", "Tasas", "%", "Diaria", "macro_curva_bonos_uf", "rendimiento_bono_uf_5_anos_pct"),
    ("spc_clp_180d", "Swap promedio cámara pesos 180 días", "Tasas", "%", "Diaria", "macro_swaps_camara", "swap_camara_pesos_180_dias_pct"),
    ("spc_clp_2y", "Swap promedio cámara pesos 2 años", "Tasas", "%", "Diaria", "macro_swaps_camara", "swap_camara_pesos_2_anos_pct"),
    ("spc_clp_360d", "Swap promedio cámara pesos 360 días", "Tasas", "%", "Diaria", "macro_swaps_camara", "swap_camara_pesos_360_dias_pct"),
    ("spc_clp_90d", "Swap promedio cámara pesos 90 días", "Tasas", "%", "Diaria", "macro_swaps_camara", "swap_camara_pesos_90_dias_pct"),
    ("spc_uf_1y", "Swap promedio cámara UF 1 año", "Tasas", "%", "Diaria", "macro_swaps_camara", "swap_camara_uf_1_ano_pct"),
    ("tib", "Tasa interbancaria promedio (diaria)", "Tasas", "%", "Diaria", "macro_tasas_corto_plazo", "tib_promedio_pct"),
    ("tpm", "Tasa de política monetaria (diaria)", "Tasas", "%", "Diaria", "macro_tasas_corto_plazo", "tpm_pct"),
    ("eur_clp", "Euro observado", "Tipo de cambio", "CLP por EUR", "Diaria", "macro_euro_observado", "euro_observado_clp_por_eur"),
    ("tcm", "Tipo de cambio multilateral (TCM)", "Tipo de cambio", "Índice", "Diaria", "macro_tipo_cambio_multilateral", "tipo_cambio_nominal_multilateral_indice"),
    ("tcm_5", "Tipo de cambio multilateral 5 monedas (TCM-5)", "Tipo de cambio", "Índice", "Diaria", "macro_tipo_cambio_multilateral", "tipo_cambio_nominal_multilateral_5_monedas_indice"),
    ("tcm_x", "Tipo de cambio multilateral sin EE.UU. (TCM-X)", "Tipo de cambio", "Índice", "Diaria", "macro_tipo_cambio_multilateral", "tipo_cambio_nominal_multilateral_x_indice"),
    ("tcr", "Tipo de cambio real", "Tipo de cambio", "Índice", "Mensual", "macro_tipo_cambio_real", "tipo_cambio_real_general_indice"),
    ("tcr_5", "Tipo de cambio real 5 monedas", "Tipo de cambio", "Índice", "Mensual", "macro_tipo_cambio_real", "tipo_cambio_real_5_monedas_indice"),
    ("usd_clp", "Dólar observado", "Tipo de cambio", "CLP por USD", "Diaria", "macro_dolar_observado", "dolar_observado_clp_por_usd"),
]

# Serie diaria que se publica día por día: las que un dashboard de mercado usa de
# verdad. Las demás quedan en el mart mensual (cierre de mes), que es el grano
# común del resto de los marts.
DIARIAS_CORE = [
    "tpm", "tib", "usd_clp", "eur_clp", "uf", "cobre_diario", "bcp_10y", "bcu_10y",
]

FECHA_DESDE_PERIODO = (
    "make_date(CAST(substr(periodo, 1, 4) AS INTEGER), "
    "CAST(substr(periodo, 6, 2) AS INTEGER), 1)"
)


def _ramas_macro(series: list[tuple]) -> str:
    """UNION ALL de una rama por serie, con su nombre, grupo y unidad a la vista."""
    ramas = []
    for serie, nombre, grupo, unidad, frecuencia, tabla, columna in series:
        ramas.append(
            f"  SELECT '{serie}' AS serie, '{nombre}' AS nombre, '{grupo}' AS grupo,\n"
            f"         '{unidad}' AS unidad, '{frecuencia}' AS frecuencia,\n"
            f"         TRY_CAST(fecha AS DATE) AS fecha, periodo,\n"
            f"         CAST({columna} AS DOUBLE) AS valor\n"
            f"  FROM {tabla}\n"
            f"  WHERE {columna} IS NOT NULL"
        )
    return "\n  UNION ALL\n".join(ramas)


# --------------------------------------------------------------------------- #
# Los marts. Cada uno declara su grano, su unidad y sus columnas; el catálogo se
# arma con eso y el conector de Looker Studio lo lee tal cual.
# --------------------------------------------------------------------------- #
DEFINICIONES = [
    {
        "id": "directorio_entidades",
        "titulo": "Directorio de entidades",
        "descripcion": "Una fila por entidad de cada sector del catálogo, para usar como dimensión y como filtro de los demás marts.",
        "sector": "transversal",
        "nivel": "nucleo",
        "periodicidad": "Vigente",
        "grano": "entidad",
        "unidad": "Sin cifras",
        "objetos": ["bancos_lista_entidades", "seguros_lista_entidades", "ffmm_lista_entidades",
                    "fi_lista_entidades", "agf_lista_entidades", "afp_lista_entidades",
                    "ccaf_lista_entidades", "cooperativas_lista_entidades",
                    "corredoras_bolsa_lista_entidades", "factoring_leasing_lista_entidades",
                    "fintech_rpsf_lista_entidades", "patrimonios_separados_lista_entidades",
                    "securitizadoras_lista_entidades", "sistemas_pago_lista_entidades"],
        "columnas": [
            ("sector", "TEXT", "dimension"),
            ("sector_label", "TEXT", "dimension"),
            ("tipo_entidad", "TEXT", "dimension"),
            ("id", "TEXT", "dimension"),
            ("nombre", "TEXT", "dimension"),
            ("nombre_fantasia", "TEXT", "dimension"),
            ("estado_vigencia", "TEXT", "dimension"),
            ("primer_periodo", "TEXT", "dimension"),
            ("ultimo_periodo", "TEXT", "dimension"),
            ("reporta_ultimo_periodo", "BOOLEAN", "dimension"),
            ("objeto_origen", "TEXT", "dimension"),
        ],
        "sql": """
WITH partes AS (
  SELECT 'bancos' AS sector, 'Bancos' AS sector_label, 'Banco' AS tipo_entidad,
         rut AS id, razon_social AS nombre, nombre_fantasia AS nombre_fantasia,
         estado AS estado_vigencia,
         CAST(NULL AS VARCHAR) AS primer_periodo, CAST(NULL AS VARCHAR) AS ultimo_periodo,
         CAST(NULL AS BOOLEAN) AS reporta_ultimo_periodo, 'bancos_lista_entidades' AS objeto_origen
  FROM bancos_lista_entidades
  UNION ALL
  SELECT 'seguros', 'Seguros', 'Aseguradora', rut_aseguradora, nombre_aseguradora,
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         primer_periodo, ultimo_periodo, reporta_ultimo_mes, 'seguros_lista_entidades'
  FROM seguros_lista_entidades
  UNION ALL
  SELECT 'ffmm', 'Fondos mutuos', 'Fondo mutuo', run_fondo, nombre_fondo,
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         primer_periodo, ultimo_periodo, reporta_ultimo_mes, 'ffmm_lista_entidades'
  FROM ffmm_lista_entidades
  UNION ALL
  SELECT 'fi', 'Fondos de inversión', 'Fondo de inversión', run_fondo, nombre_fondo,
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         primer_periodo_cartera, ultimo_periodo_cartera, reporta_ultimo_periodo,
         'fi_lista_entidades'
  FROM fi_lista_entidades
  UNION ALL
  SELECT 'agf', 'AGF', 'Administradora general de fondos', rut, razon_social, nombre_fantasia,
         estado_vigencia, CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         CAST(NULL AS BOOLEAN), 'agf_lista_entidades'
  FROM agf_lista_entidades
  UNION ALL
  SELECT 'afp', 'AFP', 'Administradora de fondos de pensiones', rut_administradora,
         nombre_administradora, nombre_fantasia, CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), CAST(NULL AS BOOLEAN),
         'afp_lista_entidades'
  FROM afp_lista_entidades
  UNION ALL
  SELECT 'ccaf', 'Cajas de compensación', 'Caja de compensación', rut, razon_social,
         nombre_fantasia, estado_vigencia, CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         CAST(NULL AS BOOLEAN), 'ccaf_lista_entidades'
  FROM ccaf_lista_entidades
  UNION ALL
  SELECT 'cooperativas', 'Cooperativas', 'Cooperativa de ahorro y crédito', rut,
         nombre_empresa, nombre_fantasia, estado_vigencia, CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR), CAST(NULL AS BOOLEAN), 'cooperativas_lista_entidades'
  FROM cooperativas_lista_entidades
  UNION ALL
  SELECT 'corredoras_bolsa', 'Corredoras de bolsa', 'Corredora de bolsa', rut,
         nombre_empresa, nombre_fantasia, estado_vigencia, CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR), CAST(NULL AS BOOLEAN), 'corredoras_bolsa_lista_entidades'
  FROM corredoras_bolsa_lista_entidades
  UNION ALL
  SELECT 'factoring_leasing', 'Factoring y leasing', 'Sociedad de factoring o leasing', rut,
         razon_social, nombre_fantasia, estado, CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR), CAST(NULL AS BOOLEAN), 'factoring_leasing_lista_entidades'
  FROM factoring_leasing_lista_entidades
  UNION ALL
  SELECT 'fintech', 'Fintech (RPSF)', 'Entidad fintech inscrita', rut, razon_social,
         nombre_fantasia, estado_vigencia, CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         CAST(NULL AS BOOLEAN), 'fintech_rpsf_lista_entidades'
  FROM fintech_rpsf_lista_entidades
  UNION ALL
  SELECT 'patrimonios_separados', 'Patrimonios separados', 'Emisión de patrimonio separado',
         numero_inscripcion, denominacion_emision, CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         CAST(NULL AS BOOLEAN), 'patrimonios_separados_lista_entidades'
  FROM patrimonios_separados_lista_entidades
  UNION ALL
  SELECT 'securitizadoras', 'Securitizadoras', 'Securitizadora', rut, razon_social,
         CAST(NULL AS VARCHAR), estado_vigencia, CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         CAST(NULL AS BOOLEAN), 'securitizadoras_lista_entidades'
  FROM securitizadoras_lista_entidades
  UNION ALL
  SELECT 'sistemas_pago', 'Sistemas de pago', 'Sistema de pago', rut, razon_social,
         nombre_comercial, estado_vigencia, CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         CAST(NULL AS BOOLEAN), 'sistemas_pago_lista_entidades'
  FROM sistemas_pago_lista_entidades
)
SELECT sector, sector_label, tipo_entidad, id, nombre, nombre_fantasia,
       estado_vigencia, primer_periodo, ultimo_periodo, reporta_ultimo_periodo,
       objeto_origen
FROM partes
ORDER BY sector, nombre NULLS LAST, id
""",
    },
    {
        "id": "seguros_inversiones_clase",
        "titulo": "Seguros: inversiones por clase de activo",
        "descripcion": "Cartera de cada compañía de seguros agrupada en cuatro clases de activo, al cierre de cada mes.",
        "sector": "seguros",
        "nivel": "nucleo",
        "periodicidad": "Mensual",
        "grano": "periodo × aseguradora × clase de activo",
        "unidad": "Miles de pesos (M$)",
        "objetos": ["seguros_renta_fija", "seguros_acciones", "seguros_fondos_mutuos", "seguros_extranjeros"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("rut_aseguradora", "TEXT", "dimension"),
            ("nombre_aseguradora", "TEXT", "dimension"),
            ("clase_activo", "TEXT", "dimension"),
            ("posiciones", "NUMBER", "metric"),
            ("valor_final_m_clp", "NUMBER", "metric"),
        ],
        "sql": f"""
WITH clases AS (
  SELECT periodo, rut_aseguradora, max(nombre_aseguradora) AS nombre_aseguradora,
         'Renta fija nacional' AS clase_activo, count(*) AS posiciones,
         sum(valor_final_m_clp) AS valor
  FROM seguros_renta_fija
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, rut_aseguradora
  UNION ALL
  SELECT periodo, rut_aseguradora, max(nombre_aseguradora),
         'Acciones y cuotas de fondos de inversión', count(*), sum(valor_final_m_clp)
  FROM seguros_acciones
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, rut_aseguradora
  UNION ALL
  SELECT periodo, rut_aseguradora, max(nombre_aseguradora),
         'Fondos mutuos', count(*), sum(valor_final_m_clp)
  FROM seguros_fondos_mutuos
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, rut_aseguradora
  UNION ALL
  SELECT periodo, rut_aseguradora, max(nombre_aseguradora),
         'Instrumentos extranjeros', count(*), sum(valor_final_m_clp)
  FROM seguros_extranjeros
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, rut_aseguradora
)
SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha, rut_aseguradora, nombre_aseguradora,
       clase_activo, posiciones, CAST(round(CAST(valor AS DOUBLE), 2) AS DECIMAL(20, 2)) AS valor_final_m_clp
FROM clases
ORDER BY periodo, rut_aseguradora, clase_activo
""",
    },
    {
        "id": "seguros_renta_fija_tipo",
        "titulo": "Seguros: renta fija por tipo de instrumento y país",
        "descripcion": "Composición de la renta fija de las aseguradoras por tipo de instrumento y país del emisor.",
        "sector": "seguros",
        "nivel": "contexto",
        "periodicidad": "Mensual",
        "grano": "periodo × tipo de instrumento × país",
        "unidad": "Miles de pesos (M$)",
        "objetos": ["seguros_renta_fija"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("tipo_instrumento", "TEXT", "dimension"),
            ("pais", "TEXT", "dimension"),
            ("aseguradoras", "NUMBER", "metric"),
            ("posiciones", "NUMBER", "metric"),
            ("valor_final_m_clp", "NUMBER", "metric"),
        ],
        "sql": f"""
SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha,
       COALESCE(NULLIF(tipo_instrumento, ''), 'Sin dato') AS tipo_instrumento,
       COALESCE(NULLIF(pais, ''), 'Sin dato') AS pais,
       count(DISTINCT rut_aseguradora) AS aseguradoras,
       count(*) AS posiciones,
       CAST(round(CAST(sum(valor_final_m_clp) AS DOUBLE), 2) AS DECIMAL(20, 2)) AS valor_final_m_clp
FROM seguros_renta_fija
WHERE periodo IS NOT NULL AND length(periodo) = 7
GROUP BY periodo, fecha,
         COALESCE(NULLIF(tipo_instrumento, ''), 'Sin dato'),
         COALESCE(NULLIF(pais, ''), 'Sin dato')
ORDER BY periodo, valor_final_m_clp DESC, tipo_instrumento, pais
""",
    },
    {
        "id": "ffmm_cartera_nacional_fondo",
        "titulo": "Fondos mutuos: cartera nacional por fondo",
        "descripcion": "Tamaño y diversificación de la cartera nacional de cada fondo mutuo al cierre de cada mes.",
        "sector": "ffmm",
        "nivel": "nucleo",
        "periodicidad": "Mensual",
        "grano": "periodo × fondo",
        "unidad": "Miles de la moneda funcional del fondo (mayoritariamente CLP)",
        "objetos": ["ffmm_cartera_nacional"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("run_fondo", "TEXT", "dimension"),
            ("nombre_fondo", "TEXT", "dimension"),
            ("posiciones", "NUMBER", "metric"),
            ("emisores", "NUMBER", "metric"),
            ("valorizacion_miles_mf", "NUMBER", "metric"),
        ],
        "sql": f"""
SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha, run_fondo,
       max(nombre_fondo) AS nombre_fondo,
       count(*) AS posiciones,
       count(DISTINCT rut_emisor) AS emisores,
       CAST(round(CAST(sum(valorizacion_miles_mf) AS DOUBLE), 2) AS DECIMAL(20, 2)) AS valorizacion_miles_mf
FROM ffmm_cartera_nacional
WHERE periodo IS NOT NULL AND length(periodo) = 7
GROUP BY periodo, fecha, run_fondo
ORDER BY periodo, run_fondo
""",
    },
    {
        "id": "ffmm_cartera_nacional_tipo",
        "titulo": "Fondos mutuos: cartera nacional por tipo de instrumento",
        "descripcion": "Composición agregada de la cartera nacional de los fondos mutuos por tipo de instrumento.",
        "sector": "ffmm",
        "nivel": "nucleo",
        "periodicidad": "Mensual",
        "grano": "periodo × tipo de instrumento",
        "unidad": "Miles de la moneda funcional del fondo (mayoritariamente CLP)",
        "objetos": ["ffmm_cartera_nacional"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("tipo_instrumento", "TEXT", "dimension"),
            ("fondos", "NUMBER", "metric"),
            ("posiciones", "NUMBER", "metric"),
            ("valorizacion_miles_mf", "NUMBER", "metric"),
            ("participacion_pct", "NUMBER", "metric", "avg"),
        ],
        "sql": f"""
WITH base AS (
  SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha,
         COALESCE(NULLIF(tipo_instrumento, ''), 'Sin dato') AS tipo_instrumento,
         count(DISTINCT run_fondo) AS fondos, count(*) AS posiciones,
         sum(valorizacion_miles_mf) AS valor
  FROM ffmm_cartera_nacional
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, fecha, COALESCE(NULLIF(tipo_instrumento, ''), 'Sin dato')
)
SELECT periodo, fecha, tipo_instrumento, fondos, posiciones,
       CAST(round(CAST(valor AS DOUBLE), 2) AS DECIMAL(20, 2)) AS valorizacion_miles_mf,
       CAST(round(100.0 * valor / sum(valor) OVER (PARTITION BY periodo), 4) AS DOUBLE) AS participacion_pct
FROM base
ORDER BY periodo, valor DESC NULLS LAST, tipo_instrumento
""",
    },
    {
        "id": "ffmm_cartera_extranjera_pais",
        "titulo": "Fondos mutuos: cartera extranjera por país",
        "descripcion": "Dónde están invertidos fuera de Chile los fondos mutuos: posiciones y monto por país del emisor.",
        "sector": "ffmm",
        "nivel": "nucleo",
        "periodicidad": "Mensual",
        "grano": "periodo × país del emisor",
        "unidad": "Miles de la moneda funcional del fondo (mayoritariamente CLP)",
        "objetos": ["ffmm_cartera_extranjera"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("pais_emisor", "TEXT", "dimension"),
            ("fondos", "NUMBER", "metric"),
            ("posiciones", "NUMBER", "metric"),
            ("valorizacion_miles_mf", "NUMBER", "metric"),
            ("participacion_pct", "NUMBER", "metric", "avg"),
        ],
        "sql": f"""
WITH base AS (
  SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha,
         COALESCE(NULLIF(pais_emisor, ''), 'Sin dato') AS pais_emisor,
         count(DISTINCT run_fondo) AS fondos, count(*) AS posiciones,
         sum(valorizacion_miles_mf) AS valor
  FROM ffmm_cartera_extranjera
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, fecha, COALESCE(NULLIF(pais_emisor, ''), 'Sin dato')
)
SELECT periodo, fecha, pais_emisor, fondos, posiciones,
       CAST(round(CAST(valor AS DOUBLE), 2) AS DECIMAL(20, 2)) AS valorizacion_miles_mf,
       CAST(round(100.0 * valor / sum(valor) OVER (PARTITION BY periodo), 4) AS DOUBLE) AS participacion_pct
FROM base
ORDER BY periodo, valor DESC NULLS LAST, pais_emisor
""",
    },
    {
        "id": "fi_cartera_nacional_tipo",
        "titulo": "Fondos de inversión: cartera nacional por tipo de instrumento",
        "descripcion": "Composición trimestral de la cartera nacional de los fondos de inversión por tipo de instrumento.",
        "sector": "fi",
        "nivel": "nucleo",
        "periodicidad": "Trimestral",
        "grano": "trimestre × tipo de instrumento",
        "unidad": "Miles de la moneda funcional del fondo",
        "objetos": ["fi_cartera_nacional"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("tipo_instrumento", "TEXT", "dimension"),
            ("fondos", "NUMBER", "metric"),
            ("posiciones", "NUMBER", "metric"),
            ("valorizacion_miles_mf", "NUMBER", "metric"),
            ("participacion_pct", "NUMBER", "metric", "avg"),
        ],
        "sql": f"""
WITH base AS (
  SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha,
         COALESCE(NULLIF(tipo_instrumento, ''), 'Sin dato') AS tipo_instrumento,
         count(DISTINCT run_fondo) AS fondos, count(*) AS posiciones,
         sum(valorizacion_miles_mf) AS valor
  FROM fi_cartera_nacional
  WHERE periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, fecha, COALESCE(NULLIF(tipo_instrumento, ''), 'Sin dato')
)
SELECT periodo, fecha, tipo_instrumento, fondos, posiciones,
       CAST(round(CAST(valor AS DOUBLE), 2) AS DECIMAL(20, 2)) AS valorizacion_miles_mf,
       CAST(round(100.0 * valor / sum(valor) OVER (PARTITION BY periodo), 4) AS DOUBLE) AS participacion_pct
FROM base
ORDER BY periodo, valor DESC NULLS LAST, tipo_instrumento
""",
    },
    {
        "id": "bancos_totales",
        "titulo": "Bancos: activos, pasivos y colocaciones",
        "descripcion": "Totales del balance de cada banco y del sistema, en pesos, al cierre de cada mes.",
        "sector": "bancos",
        "nivel": "instituciones",
        "periodicidad": "Mensual",
        "grano": "periodo × institución",
        "unidad": "Pesos (CLP)",
        "objetos": ["bancos_balance"],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("codigo_institucion", "TEXT", "dimension"),
            ("rut", "TEXT", "dimension"),
            ("razon_social", "TEXT", "dimension"),
            ("es_total_sistema", "BOOLEAN", "dimension"),
            ("activos_clp", "NUMBER", "metric"),
            ("pasivos_clp", "NUMBER", "metric"),
            ("patrimonio_clp", "NUMBER", "metric"),
            ("colocaciones_clp", "NUMBER", "metric"),
        ],
        "sql": f"""
WITH totales AS (
  SELECT periodo, codigo_institucion, rut, razon_social,
         max(CASE WHEN codigo_cuenta = '100000000' THEN importe_clp END) AS activos_clp,
         max(CASE WHEN codigo_cuenta = '200000000' THEN importe_clp END) AS pasivos_clp,
         max(CASE WHEN codigo_cuenta = '510000000' THEN importe_clp END) AS pasivos_patrimonio_clp,
         max(CASE WHEN codigo_cuenta = '500000000' THEN importe_clp END) AS colocaciones_clp
  FROM bancos_balance
  WHERE tipo_linea = 'total'
    AND codigo_cuenta IN ('100000000', '200000000', '500000000', '510000000')
    AND periodo IS NOT NULL AND length(periodo) = 7
  GROUP BY periodo, codigo_institucion, rut, razon_social
)
SELECT periodo, {FECHA_DESDE_PERIODO} AS fecha, codigo_institucion, rut, razon_social,
       razon_social = 'Total Sistema Financiero' AS es_total_sistema,
       activos_clp, pasivos_clp,
       pasivos_patrimonio_clp - pasivos_clp AS patrimonio_clp,
       colocaciones_clp
FROM totales
ORDER BY periodo, es_total_sistema, razon_social
""",
    },
    {
        "id": "macro_series_mensual",
        "titulo": "Macro: series del Banco Central, cierre de mes",
        "descripcion": "Series macro en formato largo, con el último dato disponible de cada mes. Sirve como contexto de los marts sectoriales.",
        "sector": "macro",
        "nivel": "contexto",
        "periodicidad": "Mensual",
        "grano": "periodo × serie",
        "unidad": "La unidad de cada serie está en la columna `unidad`",
        "objetos": [s[5] for s in SERIES_MACRO],
        "columnas": [
            ("periodo", "TEXT", "dimension"),
            ("fecha", "DATE", "dimension"),
            ("serie", "TEXT", "dimension"),
            ("nombre", "TEXT", "dimension"),
            ("grupo", "TEXT", "dimension"),
            ("unidad", "TEXT", "dimension"),
            ("frecuencia", "TEXT", "dimension"),
            ("valor", "NUMBER", "metric", "avg"),
        ],
        "sql": f"""
WITH larga AS (
{_ramas_macro(SERIES_MACRO)}
)
SELECT periodo, fecha, serie, nombre, grupo, unidad, frecuencia,
       CAST(round(valor, 4) AS DOUBLE) AS valor
FROM larga
WHERE fecha IS NOT NULL AND periodo IS NOT NULL AND length(periodo) = 7
QUALIFY row_number() OVER (PARTITION BY serie, periodo ORDER BY fecha DESC) = 1
ORDER BY serie, periodo
""",
    },
    {
        "id": "macro_series_diaria",
        "titulo": "Macro: series diarias del Banco Central",
        "descripcion": "Las ocho series diarias que un dashboard de mercado usa de verdad, día por día.",
        "sector": "macro",
        "nivel": "contexto",
        "periodicidad": "Diaria",
        "grano": "fecha × serie",
        "unidad": "La unidad de cada serie está en la columna `unidad`",
        "objetos": sorted({s[5] for s in SERIES_MACRO if s[0] in DIARIAS_CORE}),
        "columnas": [
            ("fecha", "DATE", "dimension"),
            ("periodo", "TEXT", "dimension"),
            ("serie", "TEXT", "dimension"),
            ("nombre", "TEXT", "dimension"),
            ("grupo", "TEXT", "dimension"),
            ("unidad", "TEXT", "dimension"),
            ("valor", "NUMBER", "metric", "avg"),
        ],
        "sql": f"""
WITH larga AS (
{_ramas_macro([s for s in SERIES_MACRO if s[0] in DIARIAS_CORE])}
)
SELECT fecha, periodo, serie, nombre, grupo, unidad,
       CAST(round(valor, 4) AS DOUBLE) AS valor
FROM larga
WHERE fecha IS NOT NULL AND periodo IS NOT NULL
ORDER BY serie, fecha
""",
    },
]


def _conectar():
    import duckdb

    sql = (V2 / "views.sql").read_text(encoding="utf-8")
    con = duckdb.connect()
    con.execute(sql.replace(f"'{BASE}'", f"'{DOCS}'"))
    con.execute("SET TimeZone='UTC'")
    return con



def _ficha_columna(columna: tuple) -> dict:
    """Ficha de columna para el catálogo: nombre, tipo, rol y agregación.

    `agregacion` sólo tiene sentido en métricas, y no siempre es SUM: sumar
    participaciones o índices da un número que no significa nada. El conector
    de Looker Studio lee este campo para configurar la métrica.
    """
    nombre, tipo, rol = columna[:3]
    ficha = {"nombre": nombre, "tipo": tipo, "rol": rol}
    if rol == "metric":
        ficha["agregacion"] = columna[3] if len(columna) > 3 else "sum"
    return ficha


def _escribir_mart(con, mart: dict, destino: Path) -> dict:
    """Copia el mart a CSV y devuelve su ficha con huella y tamaño."""
    ruta = destino / f"{mart['id']}.csv"
    # `ORDER BY ALL`: sin esto, dos filas empatadas en la última clave de orden
    # salen en distinto orden en cada corrida y el archivo cambia sin que cambie
    # el dato. Mismo criterio que `build_resultados.py`.
    consulta = f"SELECT * FROM ({mart['sql']}) ORDER BY ALL"
    con.execute(
        f"COPY ({consulta}) TO '{ruta}' "
        "(FORMAT CSV, HEADER, DELIMITER ',', QUOTE '\"', NULL '')"
    )
    filas = con.execute(f"SELECT count(*) FROM ({consulta})").fetchone()[0]
    datos = ruta.read_bytes()
    # El catálogo declara las columnas y el conector las usa como esquema: si el
    # CSV y la ficha no dicen lo mismo, Looker Studio muestra una tabla mentirosa.
    cabecera = datos.split(b"\n", 1)[0].decode("utf-8").split(",")
    declaradas = [c[0] for c in mart["columnas"]]
    if cabecera != declaradas:
        raise SystemExit(f"[FALLA] {mart['id']}: el CSV publica {cabecera} y el catálogo declara {declaradas}")
    return {
        "id": mart["id"],
        "titulo": mart["titulo"],
        "descripcion": mart["descripcion"],
        "sector": mart["sector"],
        "nivel": mart["nivel"],
        "periodicidad": mart["periodicidad"],
        "grano": mart["grano"],
        "unidad": mart["unidad"],
        "objetos": mart["objetos"],
        "filas": int(filas),
        "bytes": len(datos),
        "sha256": hashlib.sha256(datos).hexdigest(),
        "url": f"/looker/marts/{mart['id']}.csv",
        "columnas": [_ficha_columna(c) for c in mart["columnas"]],
    }


def construir(destino: Path) -> tuple[dict, dict]:
    """Escribe los marts en `destino` y devuelve `{nombre: bytes}` y el catálogo."""
    catalogo_api = json.loads((V2 / "catalog.json").read_text(encoding="utf-8"))
    con = _conectar()
    destino.mkdir(parents=True, exist_ok=True)

    fichas = [_escribir_mart(con, mart, destino) for mart in DEFINICIONES]

    indice = {
        "contrato": "sif-looker/marts",
        "version": "1.0.0",
        "base": BASE,
        "data_release": catalogo_api["data_release"],
        "generado": catalogo_api["generado"],
        "total": len(fichas),
        "filas": sum(f["filas"] for f in fichas),
        "bytes": sum(f["bytes"] for f in fichas),
        "nota": (
            "Tablas agregadas para Looker Studio, calculadas en el build sobre el mismo "
            "Parquet que publica el sitio. No son el detalle instrumento por instrumento: "
            "para eso está el catálogo API v2. Cada mart declara grano y unidad; los montos "
            "de seguros están en miles de pesos (M$) y los de fondos, en miles de la moneda "
            "funcional del fondo."
        ),
        "como_se_genera": "python3 scripts/build_marts_looker.py",
        "documentacion": f"{BASE}/looker/",
        "marts": fichas,
    }
    archivos = {f"{f['id']}.csv": (destino / f"{f['id']}.csv").read_bytes() for f in fichas}
    return archivos, indice


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si los marts están atrasados")
    args = ap.parse_args()

    if args.check:
        problemas: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            archivos, indice = construir(Path(tmp))
            for nombre, esperado in archivos.items():
                ruta = MARTS / nombre
                if not ruta.exists():
                    problemas.append(f"falta {nombre}")
                elif ruta.read_bytes() != esperado:
                    problemas.append(f"atrasado: {nombre}")
            texto = json.dumps(indice, ensure_ascii=False, indent=1) + "\n"
            ruta_indice = SALIDA / "catalogo.json"
            if not ruta_indice.exists():
                problemas.append("falta catalogo.json")
            elif ruta_indice.read_text(encoding="utf-8") != texto:
                problemas.append("atrasado: catalogo.json")
            if MARTS.exists():
                sobran = {p.name for p in MARTS.glob("*.csv")} - set(archivos)
                for nombre in sorted(sobran):
                    problemas.append(f"sobra {nombre}")
        for p in problemas[:15]:
            print(f"[FALLA] {p}")
        if problemas:
            print(f"\nMARTS LOOKER: {len(problemas)} archivo(s) fuera de fecha. "
                  f"Ejecuta: python3 scripts/build_marts_looker.py")
            return 1
        print(f"MARTS LOOKER: {indice['total']} marts · {indice['filas']} filas · "
              f"{indice['bytes']} B al día")
        return 0

    MARTS.mkdir(parents=True, exist_ok=True)
    for viejo in MARTS.glob("*.csv"):
        viejo.unlink()
    archivos, indice = construir(MARTS)
    texto = json.dumps(indice, ensure_ascii=False, indent=1) + "\n"
    (SALIDA / "catalogo.json").write_text(texto, encoding="utf-8")
    print(f"Marts: {indice['total']} archivos · {indice['filas']} filas · "
          f"{indice['bytes'] / 1024:.0f} KB")
    for f in indice["marts"]:
        print(f"  {f['id']:<34} {f['filas']:>7} filas  {f['bytes'] / 1024:>7.0f} KB")
    print(f"Catálogo: {(SALIDA / 'catalogo.json').relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
