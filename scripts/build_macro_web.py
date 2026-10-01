#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza la sección Macroeconomía (BCCh) de la web con las tablas temáticas.

Fuente de verdad: macro/scripts/build_tablas_tematicas.TABLAS (id, nombre, frecuencia,
descripción y columnas) + los Parquet publicados en docs/outputs/macro/ (filas y cortes).

Reescribe, entre marcadores, el bloque macro de:
  docs/js/sidebar.js         árbol del explorador (carpetas por tema + consultas sugeridas)
  docs/js/data_viewer.js     catálogo del visor
  docs/js/data_dictionary.js fichas del diccionario (todas las columnas)
  docs/js/erd_graph.js       nodos ERD (todas las columnas) y enlaces
  docs/js/duckdb_client.js   vistas SQL
  docs/vocabulario.json      tipos y tablas del sector macro

Uso:
  python3 scripts/build_macro_web.py           # escribe
  python3 scripts/build_macro_web.py --check   # falla si algo está desactualizado
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from macro.scripts.build_tablas_tematicas import TABLAS, SALIDA, CATALOGO_PQ  # noqa: E402

DOCS = RAIZ / "docs"
SECTOR_LABEL = "Macroeconomía y Tasas (BCCh)"
ORIGEN = "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS)."

# Carpetas temáticas del explorador: (id, etiqueta, ids de tablas, consultas sugeridas).
CARPETAS = [
    ("cat_macro_tasas_interes", "Tasas de interés",
     ["macro_tasas_corto_plazo", "macro_swaps_camara", "macro_curva_bonos_pesos",
      "macro_curva_bonos_uf", "macro_inflacion_implicita"],
     [
         ("TPM y tasa interbancaria: últimos 60 días", "SELECT fecha, tpm_pct, tib_promedio_pct, round(tib_promedio_pct - tpm_pct, 3) AS diferencia_tib_tpm FROM macro_tasas_corto_plazo ORDER BY fecha DESC LIMIT 60;"),
         ("Curva de bonos en pesos: promedio mensual, últimos 24 meses", "SELECT periodo, round(avg(rendimiento_bono_pesos_2_anos_pct), 3) AS bono_2_anos_pct, round(avg(rendimiento_bono_pesos_5_anos_pct), 3) AS bono_5_anos_pct, round(avg(rendimiento_bono_pesos_10_anos_pct), 3) AS bono_10_anos_pct FROM macro_curva_bonos_pesos GROUP BY periodo ORDER BY periodo DESC LIMIT 24;"),
         ("Curva de bonos en UF: último dato disponible por plazo", "SELECT fecha, rendimiento_bono_uf_1_ano_pct, rendimiento_bono_uf_2_anos_pct, rendimiento_bono_uf_5_anos_pct, rendimiento_bono_uf_10_anos_pct, rendimiento_bono_uf_20_anos_pct, rendimiento_bono_uf_30_anos_pct FROM macro_curva_bonos_uf ORDER BY fecha DESC LIMIT 20;"),
         ("Inflación implícita a 5 y 10 años: promedio mensual", "SELECT periodo, round(avg(inflacion_implicita_5_anos_pct), 3) AS implicita_5_anos_pct, round(avg(inflacion_implicita_10_anos_pct), 3) AS implicita_10_anos_pct FROM macro_inflacion_implicita GROUP BY periodo ORDER BY periodo DESC LIMIT 24;"),
         ("Swaps de cámara en pesos: curva 90 días a 2 años", "SELECT fecha, swap_camara_pesos_90_dias_pct, swap_camara_pesos_180_dias_pct, swap_camara_pesos_360_dias_pct, swap_camara_pesos_2_anos_pct, swap_camara_uf_1_ano_pct FROM macro_swaps_camara ORDER BY fecha DESC LIMIT 30;"),
     ]),
    ("cat_macro_tipo_cambio", "Tipo de cambio",
     ["macro_dolar_observado", "macro_euro_observado", "macro_tipo_cambio_multilateral", "macro_tipo_cambio_real"],
     [
         ("Dólar observado: últimos 30 días hábiles", "SELECT fecha, dolar_observado_clp_por_usd FROM macro_dolar_observado ORDER BY fecha DESC LIMIT 30;"),
         ("Dólar observado por mes: promedio, mínimo, máximo y cierre", "SELECT periodo, round(avg(dolar_observado_clp_por_usd), 2) AS promedio_clp, min(dolar_observado_clp_por_usd) AS minimo_clp, max(dolar_observado_clp_por_usd) AS maximo_clp, arg_max(dolar_observado_clp_por_usd, fecha) AS cierre_clp FROM macro_dolar_observado GROUP BY periodo ORDER BY periodo DESC LIMIT 24;"),
         ("Dólar y euro observados en la misma fecha", "SELECT d.fecha, d.dolar_observado_clp_por_usd, e.euro_observado_clp_por_eur, round(e.euro_observado_clp_por_eur / d.dolar_observado_clp_por_usd, 4) AS euro_por_dolar FROM macro_dolar_observado d JOIN macro_euro_observado e USING (fecha) ORDER BY d.fecha DESC LIMIT 30;"),
         ("Tipo de cambio real: TCR general y TCR-5", "SELECT periodo, tipo_cambio_real_general_indice, tipo_cambio_real_5_monedas_indice FROM macro_tipo_cambio_real ORDER BY periodo DESC LIMIT 24;"),
     ]),
    ("cat_macro_precios_reajustes", "Precios y reajustes",
     ["macro_uf", "macro_utm", "macro_inflacion_ipc"],
     [
         ("Inflación IPC: índice y variaciones mensual y anual", "SELECT periodo, ipc_indice, ipc_var_mensual_pct, ipc_var_anual_pct FROM macro_inflacion_ipc ORDER BY periodo DESC LIMIT 24;"),
         ("UF: valor de cierre de cada mes y variación mensual", "SELECT periodo, uf_cierre_clp, round((uf_cierre_clp / lag(uf_cierre_clp) OVER (ORDER BY periodo) - 1) * 100, 2) AS uf_var_mensual_pct FROM (SELECT periodo, arg_max(uf_valor_clp, fecha) AS uf_cierre_clp FROM macro_uf GROUP BY periodo) ORDER BY periodo DESC LIMIT 24;"),
         ("UF y UTM vigentes: último valor de cada mes", "SELECT u.periodo, arg_max(u.uf_valor_clp, u.fecha) AS uf_cierre_clp, max(t.utm_valor_clp) AS utm_valor_clp FROM macro_uf u LEFT JOIN macro_utm t USING (periodo) GROUP BY u.periodo ORDER BY u.periodo DESC LIMIT 24;"),
     ]),
    ("cat_macro_actividad", "Actividad económica",
     ["macro_imacec", "macro_pib_trimestral"],
     [
         ("Imacec total y no minero con variación anual", "SELECT periodo, imacec_empalmado_indice, round((imacec_empalmado_indice / lag(imacec_empalmado_indice, 12) OVER (ORDER BY periodo) - 1) * 100, 2) AS imacec_var_anual_pct, imacec_no_minero_indice, imacec_minero_indice FROM macro_imacec ORDER BY periodo DESC LIMIT 24;"),
         ("Imacec por sector: comercio y servicios", "SELECT periodo, imacec_comercio_indice, imacec_servicios_indice, imacec_no_minero_indice FROM macro_imacec ORDER BY periodo DESC LIMIT 24;"),
         ("PIB trimestral con variación respecto al mismo trimestre del año anterior", "SELECT periodo, pib_encadenado_miles_mm_clp, round((pib_encadenado_miles_mm_clp / lag(pib_encadenado_miles_mm_clp, 4) OVER (ORDER BY periodo) - 1) * 100, 2) AS pib_var_anual_pct FROM macro_pib_trimestral ORDER BY periodo DESC LIMIT 20;"),
     ]),
    ("cat_macro_mercado_laboral", "Mercado laboral",
     ["macro_mercado_laboral"],
     [
         ("Desocupación, ocupados y fuerza de trabajo: últimos 24 meses", "SELECT periodo, desocupacion_pct, ocupados_miles_personas, asalariados_miles_personas, fuerza_trabajo_miles_personas FROM macro_mercado_laboral ORDER BY periodo DESC LIMIT 24;"),
         ("Participación de asalariados sobre ocupados", "SELECT periodo, round(asalariados_miles_personas / ocupados_miles_personas * 100, 2) AS asalariados_sobre_ocupados_pct, desocupacion_pct FROM macro_mercado_laboral ORDER BY periodo DESC LIMIT 24;"),
     ]),
    ("cat_macro_materias_primas", "Materias primas",
     ["macro_cobre", "macro_metales_preciosos"],
     [
         ("Cobre: precio diario BML, últimos 30 días", "SELECT fecha, cobre_refinado_usd_por_libra FROM macro_cobre WHERE cobre_refinado_usd_por_libra IS NOT NULL ORDER BY fecha DESC LIMIT 30;"),
         ("Cobre: promedio mensual y referencia BCCh con variación anual", "SELECT periodo, promedio_diario_usd_lb, referencia_mensual_usd_lb, round((referencia_mensual_usd_lb / lag(referencia_mensual_usd_lb, 12) OVER (ORDER BY periodo) - 1) * 100, 2) AS referencia_var_anual_pct FROM (SELECT periodo, round(avg(cobre_refinado_usd_por_libra), 4) AS promedio_diario_usd_lb, max(cobre_referencial_mensual_usd_por_libra) AS referencia_mensual_usd_lb FROM macro_cobre GROUP BY periodo) ORDER BY periodo DESC LIMIT 24;"),
         ("Oro y plata: últimos 30 días", "SELECT fecha, oro_usd_por_onza_troy, plata_usd_por_onza_troy, round(oro_usd_por_onza_troy / plata_usd_por_onza_troy, 2) AS relacion_oro_plata FROM macro_metales_preciosos ORDER BY fecha DESC LIMIT 30;"),
     ]),
    ("cat_macro_sector_externo_fiscal", "Sector externo y fiscal",
     ["macro_reservas_internacionales", "macro_tasa_referencia_fed", "macro_deuda_publica_pct_pib"],
     [
         ("Reservas internacionales: últimos 24 meses", "SELECT periodo, reservas_internacionales_millones_usd FROM macro_reservas_internacionales ORDER BY periodo DESC LIMIT 24;"),
         ("Tasa de la Fed frente a la TPM de Chile: promedio mensual", "SELECT f.periodo, round(avg(f.tasa_fed_funds_pct), 2) AS fed_funds_pct, round(avg(t.tpm_pct), 2) AS tpm_chile_pct FROM macro_tasa_referencia_fed f JOIN macro_tasas_corto_plazo t USING (periodo) GROUP BY f.periodo ORDER BY f.periodo DESC LIMIT 24;"),
         ("Deuda pública sobre PIB: serie trimestral", "SELECT periodo, deuda_bruta_gobierno_central_pct_pib FROM macro_deuda_publica_pct_pib ORDER BY periodo DESC LIMIT 20;"),
     ]),
    ("cat_macro_expectativas", "Expectativas",
     ["macro_expectativas_inflacion", "macro_expectativas_tpm", "macro_expectativas_operadores"],
     [
         ("Inflación anual efectiva frente a la esperada (EEE)", "SELECT i.periodo, i.ipc_var_anual_pct, e.expectativa_inflacion_ipc_11_meses_pct, e.expectativa_inflacion_ipc_23_meses_pct, round((e.expectativa_inflacion_ipc_11_meses_pct - 3.0) * 100, 0) AS desvio_11_meses_vs_meta_puntos_basicos FROM macro_inflacion_ipc i JOIN macro_expectativas_inflacion e USING (periodo) ORDER BY i.periodo DESC LIMIT 24;"),
         ("TPM efectiva frente a la esperada por la EEE", "SELECT e.periodo, round(avg(t.tpm_pct), 2) AS tpm_pct, max(e.expectativa_tpm_11_meses_pct) AS expectativa_tpm_11_meses_pct, max(e.expectativa_tpm_23_meses_pct) AS expectativa_tpm_23_meses_pct FROM macro_expectativas_tpm e JOIN macro_tasas_corto_plazo t USING (periodo) GROUP BY e.periodo ORDER BY e.periodo DESC LIMIT 24;"),
         ("Encuesta de Operadores Financieros: últimas 20 encuestas", "SELECT fecha, expectativa_inflacion_12_meses_pct, expectativa_tpm_12_meses_pct FROM macro_expectativas_operadores ORDER BY fecha DESC LIMIT 20;"),
     ]),
    ("cat_macro_series_catalogo", "Catálogo de series",
     ["macro_series_catalogo"],
     [
         ("Catálogo: series, frecuencia, unidad y última fecha", "SELECT grupo, nombre, frecuencia, unidad, primera_fecha, ultima_fecha, observaciones, estado FROM macro_series_catalogo ORDER BY grupo, nombre;"),
         ("Estado de la última consulta al BCCh por grupo", "SELECT grupo, count(*) AS series, sum(CASE WHEN estado = 'ok' THEN 1 ELSE 0 END) AS series_ok, max(ultima_fecha) AS dato_mas_reciente, max(ultima_consulta_utc) AS ultima_consulta_utc FROM macro_series_catalogo GROUP BY grupo ORDER BY grupo;"),
     ]),
]

# Significado de cada columna para el diccionario (todas las columnas de todas las tablas).
SIGNIFICADO = {
    "tpm_pct": "Tasa de Política Monetaria fijada por el Consejo del Banco Central, en porcentaje anual.",
    "tib_promedio_pct": "Tasa interbancaria promedio (TIB): tasa a la que los bancos se prestan a un día, en porcentaje anual.",
    "swap_camara_pesos_90_dias_pct": "Tasa fija del swap promedio de cámara en pesos a 90 días, en porcentaje anual.",
    "swap_camara_pesos_180_dias_pct": "Tasa fija del swap promedio de cámara en pesos a 180 días, en porcentaje anual.",
    "swap_camara_pesos_360_dias_pct": "Tasa fija del swap promedio de cámara en pesos a 360 días, en porcentaje anual.",
    "swap_camara_pesos_2_anos_pct": "Tasa fija del swap promedio de cámara en pesos a 2 años, en porcentaje anual.",
    "swap_camara_uf_1_ano_pct": "Tasa fija del swap promedio de cámara en UF a 1 año, en porcentaje anual.",
    "rendimiento_bono_pesos_2_anos_pct": "Tasa de mercado secundario del bono del Banco Central en pesos a 2 años (BCP-2), en porcentaje anual.",
    "rendimiento_bono_pesos_5_anos_pct": "Tasa de mercado secundario del bono del Banco Central en pesos a 5 años (BCP-5), en porcentaje anual.",
    "rendimiento_bono_pesos_10_anos_pct": "Tasa de mercado secundario del bono del Banco Central en pesos a 10 años (BCP-10), en porcentaje anual.",
    "rendimiento_bono_uf_1_ano_pct": "Tasa de mercado secundario del bono en UF a 1 año (BCU-1), en porcentaje anual sobre UF.",
    "rendimiento_bono_uf_2_anos_pct": "Tasa de mercado secundario del bono en UF a 2 años (BCU-2), en porcentaje anual sobre UF.",
    "rendimiento_bono_uf_5_anos_pct": "Tasa de mercado secundario del bono en UF a 5 años (BCU-5), en porcentaje anual sobre UF.",
    "rendimiento_bono_uf_10_anos_pct": "Tasa de mercado secundario del bono en UF a 10 años (BCU-10), en porcentaje anual sobre UF.",
    "rendimiento_bono_uf_20_anos_pct": "Tasa de mercado secundario del bono en UF a 20 años (BCU-20), en porcentaje anual sobre UF.",
    "rendimiento_bono_uf_30_anos_pct": "Tasa de mercado secundario del bono en UF a 30 años (BCU-30), en porcentaje anual sobre UF.",
    "inflacion_implicita_5_anos_pct": "Rendimiento del bono en pesos a 5 años menos el del bono en UF a 5 años: inflación anual promedio que el mercado espera para ese plazo. Calculada por SIF.",
    "inflacion_implicita_10_anos_pct": "Rendimiento del bono en pesos a 10 años menos el del bono en UF a 10 años: inflación anual promedio que el mercado espera para ese plazo. Calculada por SIF.",
    "dolar_observado_clp_por_usd": "Pesos chilenos por un dólar de los Estados Unidos (dólar observado publicado por el BCCh para el día).",
    "euro_observado_clp_por_eur": "Pesos chilenos por un euro (euro observado publicado por el BCCh para el día).",
    "tipo_cambio_nominal_multilateral_indice": "Índice de tipo de cambio nominal multilateral (TCM): valor del peso frente a una canasta de monedas de socios comerciales.",
    "tipo_cambio_nominal_multilateral_5_monedas_indice": "Índice TCM-5: peso frente a las monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro.",
    "tipo_cambio_nominal_multilateral_x_indice": "Índice TCM-X: variante del TCM que excluye a Estados Unidos.",
    "tipo_cambio_real_general_indice": "Índice de tipo de cambio real general (TCR), promedio 1986=100. Un valor mayor indica un peso más depreciado en términos reales.",
    "tipo_cambio_real_5_monedas_indice": "Índice de tipo de cambio real TCR-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro), promedio 1986=100.",
    "uf_valor_clp": "Valor de la Unidad de Fomento del día, en pesos chilenos.",
    "utm_valor_clp": "Valor de la Unidad Tributaria Mensual del mes, en pesos chilenos.",
    "ipc_indice": "Índice de Precios al Consumidor, serie empalmada base 2023=100.",
    "ipc_var_mensual_pct": "Variación del IPC respecto al mes anterior, en porcentaje.",
    "ipc_var_anual_pct": "Variación del IPC respecto al mismo mes del año anterior, en porcentaje (inflación anual).",
    "imacec_empalmado_indice": "Imacec total, serie empalmada, índice 2018=100.",
    "imacec_no_minero_indice": "Imacec no minero (actividad sin minería), índice 2018=100.",
    "imacec_minero_indice": "Imacec minero, índice 2018=100.",
    "imacec_comercio_indice": "Imacec de comercio, índice 2018=100.",
    "imacec_servicios_indice": "Imacec de servicios, índice 2018=100.",
    "pib_encadenado_miles_mm_clp": "PIB trimestral en volumen a precios del año anterior encadenado (referencia 2018), en miles de millones de pesos encadenados.",
    "desocupacion_pct": "Tasa de desocupación nacional del trimestre móvil terminado en el mes, en porcentaje de la fuerza de trabajo.",
    "ocupados_miles_personas": "Personas ocupadas, en miles.",
    "asalariados_miles_personas": "Personas ocupadas como asalariadas, en miles.",
    "fuerza_trabajo_miles_personas": "Fuerza de trabajo (ocupados más desocupados), en miles de personas.",
    "cobre_refinado_usd_por_libra": "Precio del cobre refinado en la Bolsa de Metales de Londres del día, en dólares por libra.",
    "cobre_referencial_mensual_usd_por_libra": "Precio referencial mensual del cobre publicado por el BCCh, en dólares por libra. Aparece en la fila del primer día de cada mes.",
    "oro_usd_por_onza_troy": "Precio del oro del día, en dólares por onza troy.",
    "plata_usd_por_onza_troy": "Precio de la plata del día, en dólares por onza troy.",
    "reservas_internacionales_millones_usd": "Activos de reserva internacional del Banco Central al cierre del mes, en millones de dólares.",
    "tasa_fed_funds_pct": "Tasa efectiva de fondos federales de la Reserva Federal de los Estados Unidos del día, en porcentaje anual.",
    "deuda_bruta_gobierno_central_pct_pib": "Deuda bruta del Gobierno Central de Chile al cierre del trimestre, como porcentaje del PIB.",
    "expectativa_inflacion_ipc_11_meses_pct": "Mediana de la EEE para la variación anual del IPC dentro de 11 meses, en porcentaje.",
    "expectativa_inflacion_ipc_23_meses_pct": "Mediana de la EEE para la variación anual del IPC dentro de 23 meses, en porcentaje.",
    "expectativa_tpm_11_meses_pct": "Mediana de la EEE para la TPM dentro de 11 meses, en porcentaje.",
    "expectativa_tpm_23_meses_pct": "Mediana de la EEE para la TPM dentro de 23 meses, en porcentaje.",
    "expectativa_inflacion_12_meses_pct": "Mediana de la Encuesta de Operadores Financieros para la inflación anual dentro de 12 meses, en porcentaje.",
    "expectativa_tpm_12_meses_pct": "Mediana de la Encuesta de Operadores Financieros para la TPM dentro de 12 meses, en porcentaje.",
}

CATALOGO_COLS = [
    ("clave", "VARCHAR", "PK", "Identificador corto de la serie usado por el pipeline."),
    ("serie_id", "VARCHAR", "Atributo", "Código oficial de la serie en la Base de Datos Estadísticos del BCCh."),
    ("nombre", "VARCHAR", "Atributo", "Nombre descriptivo de la serie."),
    ("grupo", "VARCHAR", "Atributo", "Tema: Tasas, Tipo de cambio, Precios y reajustes, Actividad, Mercado laboral, Commodities, Sector externo, Fiscal o Expectativas."),
    ("unidad", "VARCHAR", "Atributo", "Unidad de medida del valor."),
    ("frecuencia", "VARCHAR", "Atributo", "Diaria, Mensual o Trimestral."),
    ("titulo_bcch", "VARCHAR", "Atributo", "Título oficial entregado por la API del BCCh."),
    ("primera_fecha", "VARCHAR", "Fecha", "Primera observación publicada."),
    ("ultima_fecha", "VARCHAR", "Fecha", "Última observación publicada."),
    ("observaciones", "BIGINT", "Métrica", "Número de observaciones publicadas."),
    ("estado", "VARCHAR", "Atributo", "ok, sin datos en el BCCh o el error de la última consulta."),
    ("ultima_consulta_utc", "VARCHAR", "Fecha", "Momento de la última consulta a la API (UTC)."),
]

DETALLE = {  # etiqueta corta por tabla para el visor y el vocabulario
    "macro_tasas_corto_plazo": "TPM y tasa interbancaria",
    "macro_swaps_camara": "Swaps de cámara",
    "macro_curva_bonos_pesos": "Curva de bonos en pesos",
    "macro_curva_bonos_uf": "Curva de bonos en UF",
    "macro_inflacion_implicita": "Inflación implícita",
    "macro_dolar_observado": "Dólar observado",
    "macro_euro_observado": "Euro observado",
    "macro_tipo_cambio_multilateral": "Tipo de cambio multilateral",
    "macro_tipo_cambio_real": "Tipo de cambio real",
    "macro_uf": "Unidad de Fomento",
    "macro_utm": "Unidad Tributaria Mensual",
    "macro_inflacion_ipc": "Inflación (IPC)",
    "macro_imacec": "Imacec",
    "macro_pib_trimestral": "PIB trimestral",
    "macro_mercado_laboral": "Mercado laboral",
    "macro_cobre": "Cobre",
    "macro_metales_preciosos": "Metales preciosos",
    "macro_reservas_internacionales": "Reservas internacionales",
    "macro_tasa_referencia_fed": "Tasa de la Reserva Federal",
    "macro_deuda_publica_pct_pib": "Deuda pública sobre PIB",
    "macro_expectativas_inflacion": "Expectativas de inflación",
    "macro_expectativas_tpm": "Expectativas de TPM",
    "macro_expectativas_operadores": "Encuesta de Operadores Financieros",
    "macro_series_catalogo": "Catálogo de series",
}

FRECUENCIA_FILA = {"Diaria": "día", "Mensual": "mes", "Trimestral": "trimestre"}
FRECUENCIA_PLURAL = {"Diaria": "días", "Mensual": "meses", "Trimestral": "trimestres"}
COLOR = {"Diaria": "#E65100", "Mensual": "#F57C00", "Trimestral": "#FF9800"}


def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def fmt_es(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def columnas(spec: dict) -> list[str]:
    return [c for _, c in spec.get("columnas", [])] + [c for c, _, _ in spec.get("derivadas", [])]


def leer_meta() -> dict[str, dict]:
    meta = {}
    for spec in TABLAS:
        ruta = SALIDA / f"{spec['id']}.parquet"
        fechas = pq.read_table(ruta, columns=["fecha"]).column(0).to_pylist()
        meta[spec["id"]] = {"filas": len(fechas), "desde": fechas[0], "hasta": fechas[-1]}
    cat = pq.read_table(CATALOGO_PQ, columns=["primera_fecha", "ultima_fecha"]).to_pydict()
    meta["macro_series_catalogo"] = {
        "filas": len(cat["primera_fecha"]),
        "desde": min(f for f in cat["primera_fecha"] if f),
        "hasta": max(f for f in cat["ultima_fecha"] if f),
    }
    return meta


def badge_tabla(spec: dict | None, m: dict) -> str:
    """Conteo real (badges y ERD)."""
    if spec is None:
        return f"{m['filas']} series"
    return f"{fmt_es(m['filas'])} {FRECUENCIA_PLURAL[spec['frecuencia']]}"


def cobertura_tabla(spec: dict | None) -> str:
    """Texto de cobertura del vocabulario (línea `rows` de la tarjeta)."""
    if spec is None:
        return "Una fila por serie"
    return f"Una fila por {FRECUENCIA_FILA[spec['frecuencia']]}"


def spec_por_id() -> dict[str, dict]:
    return {s["id"]: s for s in TABLAS}


# ----------------------------------------------------------------------------- sidebar
def bloque_sidebar(meta: dict) -> str:
    specs = spec_por_id()
    anio_ini = min(m["desde"][:4] for m in meta.values())
    anio_fin = max(m["hasta"][:4] for m in meta.values())
    n_tablas = len(TABLAS)
    out = []
    out.append("  {")
    out.append('    id: "group_macro",')
    out.append('    type: "group",')
    out.append('    label: "MACROECONOMÍA Y TASAS (BCCh)",')
    out.append("    badges: [")
    out.append(f'      {{ type: "data", text: "{n_tablas} tablas", title: "Una tabla por indicador económico, en la frecuencia en que lo publica el Banco Central (diaria, mensual o trimestral)" }},')
    out.append(f'      {{ type: "data", text: "{anio_ini} → {anio_fin}", title: "Cobertura de las series: desde {anio_ini} hasta la última publicación del BCCh" }}')
    out.append("    ],")
    out.append('    status: "active",')
    out.append("    children: [")
    out.append("      {")
    out.append('        id: "sector_macro_general",')
    out.append('        type: "sector",')
    out.append('        label: "Banco Central de Chile · Base de Datos Estadísticos",')
    out.append('        sector: "macro",')
    out.append("        children: [")
    carpetas = []
    for cid, label, ids, chips in CARPETAS:
        if len(ids) == 1:
            badge = badge_tabla(specs.get(ids[0]), meta[ids[0]])
        else:
            badge = f"{len(ids)} tablas"
        c = []
        c.append("          {")
        c.append(f"            id: {js_str(cid)},")
        c.append('            type: "circular",')
        c.append(f"            label: {js_str(label)},")
        c.append(f"            badge: {js_str(badge)},")
        c.append('            badgeType: "data",')
        c.append('            status: "active",')
        c.append('            sector: "macro",')
        c.append("            chips: [")
        c.append(",\n".join(f"              {{ label: {js_str(l)}, query: {js_str(q)} }}" for l, q in chips))
        c.append("            ],")
        c.append("            tables: [")
        tl = []
        for i in ids:
            spec = specs.get(i)
            nombre = spec["nombre"] if spec else "macro.series_catalogo"
            tl.append(f"              {{ id: {js_str(i)}, name: {js_str(nombre)}, rows: {js_str(cobertura_tabla(spec))}, file: {js_str('outputs/macro/' + i + '.parquet')} }}")
        c.append(",\n".join(tl))
        c.append("            ]")
        c.append("          }")
        carpetas.append("\n".join(c))
    out.append(",\n".join(carpetas))
    out.append("        ]")
    out.append("      }")
    out.append("    ]")
    out.append("  }")
    return "\n".join(out)


# ----------------------------------------------------------------------------- visor
def bloque_viewer() -> str:
    filas = []
    for spec in TABLAS:
        filas.append(f"      {{ id: {js_str(spec['id'])}, name: {js_str(spec['nombre'])}, detalle: {js_str(DETALLE[spec['id']])}, descripcion: {js_str(spec['descripcion'])} }}")
    filas.append('      { id: "macro_series_catalogo", name: "macro.series_catalogo", detalle: "Catálogo de series", descripcion: "Las 51 series del Banco Central que alimentan las tablas macro: código, nombre, unidad, frecuencia, cobertura y estado de la última consulta." }')
    return "  {\n    group: " + js_str(SECTOR_LABEL) + ",\n    tables: [\n" + ",\n".join(filas) + "\n    ]\n  }"


# ----------------------------------------------------------------------------- diccionario
def ficha(spec: dict | None, m: dict, hoy: str) -> str:
    if spec is None:
        tid, nombre, frec = "macro_series_catalogo", "macro.series_catalogo", "Catálogo"
        desc = ("Una fila por serie del Banco Central que alimenta las tablas macro: código SIETE, nombre, "
                "grupo, frecuencia, unidad, título oficial del BCCh, cobertura y estado de la última consulta.")
        cols = [f'      {{ name: {js_str(n)}, type: {js_str(t)}, role: {js_str(r)}, significado: {js_str(s)}, contable: "No aplica" }}'
                for n, t, r, s in CATALOGO_COLS]
        registros = f"{m['filas']} series"
    else:
        tid, nombre, frec, desc = spec["id"], spec["nombre"], spec["frecuencia"], spec["descripcion"]
        unidad_fila = FRECUENCIA_FILA[frec]
        fecha_sig = {"Diaria": "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.",
                     "Mensual": "Primer día del mes al que corresponde el dato (AAAA-MM-01).",
                     "Trimestral": "Primer día del trimestre al que corresponde el dato (AAAA-MM-01)."}[frec]
        cols = [f'      {{ name: "fecha", type: "VARCHAR", role: "PK", significado: {js_str(fecha_sig)}, contable: "No aplica" }}',
                f'      {{ name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" }}']
        for c in columnas(spec):
            cols.append(f'      {{ name: {js_str(c)}, type: "DOUBLE", role: "Métrica", significado: {js_str(SIGNIFICADO[c])}, contable: "No aplica" }}')
        registros = f"{fmt_es(m['filas'])} {FRECUENCIA_PLURAL[frec]}"
    return "\n".join([
        "  {",
        f"    id: {js_str(tid)},",
        f"    name: {js_str(nombre)},",
        f"    viewName: {js_str(tid)},",
        '    sector: "macro",',
        f"    sectorLabel: {js_str(SECTOR_LABEL)},",
        '    norma: "Estadísticas oficiales BCCh",',
        f"    corte: {js_str(m['desde'] + ' a ' + m['hasta'])},",
        f"    frecuencia: {js_str(frec)},",
        '    frescura: "Se actualiza sola a diario",',
        '    modo: "Automático · diario, incremental (cada serie desde su último dato)",',
        f"    ultimaActualizacion: {js_str(hoy)},",
        f"    registros: {js_str(registros)},",
        f"    origen: {js_str(ORIGEN)},",
        f"    descripcion: {js_str(desc)},",
        "    columnas: [",
        ",\n".join(cols),
        "    ]",
        "  }",
    ])


def bloque_dictionary(meta: dict, hoy: str) -> str:
    fichas = [ficha(s, meta[s["id"]], hoy) for s in TABLAS]
    fichas.append(ficha(None, meta["macro_series_catalogo"], hoy))
    return ",\n".join(fichas)


# ----------------------------------------------------------------------------- ERD
def bloque_erd_nodes(meta: dict) -> str:
    nodes = []
    x0, y0, w, colw, gap = 3040, 110, 250, 290, 30
    ys = [y0, y0]
    for spec in TABLAS + [None]:
        if spec is None:
            tid, nombre, cols, color, rows = "macro_series_catalogo", "macro.series_catalogo", \
                [("clave", True, "VARCHAR")] + [(n, False, t) for n, t, _, _ in CATALOGO_COLS[1:7]], \
                "#FF9800", f"{meta['macro_series_catalogo']['filas']} series"
        else:
            tid, nombre = spec["id"], spec["nombre"]
            cols = [("fecha", True, "VARCHAR"), ("periodo", False, "VARCHAR")] + [(c, False, "DOUBLE") for c in columnas(spec)]
            color = COLOR[spec["frecuencia"]]
            rows = badge_tabla(spec, meta[tid])
        h = 44 + 18 * len(cols)
        col = 0 if ys[0] <= ys[1] else 1
        x, y = x0 + col * colw, ys[col]
        ys[col] += h + gap
        lines = ["  {", f"    id: {js_str(tid)},", f"    name: {js_str(nombre)},", '    sector: "macro",',
                 f"    color: {js_str(color)},", f"    x: {x},", f"    y: {y},", f"    w: {w},", f"    h: {h},",
                 f"    rows: {js_str(rows)},", f"    file: {js_str('outputs/macro/' + tid + '.parquet')},", "    cols: ["]
        lines.append(",\n".join(
            f"      {{ name: {js_str(n)}, {'pk: true, ' if pk else ''}type: {js_str(t)} }}" for n, pk, t in cols))
        lines += ["    ]", "  }"]
        nodes.append("\n".join(lines))
    return ",\n".join(nodes)


ERD_LINKS = [
    ("macro_curva_bonos_pesos", "macro_inflacion_implicita", "fecha (bono pesos − bono UF)"),
    ("macro_curva_bonos_uf", "macro_inflacion_implicita", "fecha (bono pesos − bono UF)"),
    ("macro_inflacion_ipc", "macro_expectativas_inflacion", "periodo (inflación efectiva vs esperada)"),
    ("macro_tasas_corto_plazo", "macro_expectativas_tpm", "periodo (TPM efectiva vs esperada)"),
    ("macro_dolar_observado", "macro_euro_observado", "fecha"),
]


def bloque_erd_links() -> str:
    return ",\n".join(f"  {{ from: {js_str(a)}, to: {js_str(b)}, key: {js_str(k)} }}" for a, b, k in ERD_LINKS)


# ----------------------------------------------------------------------------- duckdb
def bloque_duckdb() -> str:
    filas = [f'  {{ name: {js_str(s["id"])}, file: {js_str("outputs/macro/" + s["id"] + ".parquet")} }}' for s in TABLAS]
    filas.append('  { name: "macro_series_catalogo", file: "outputs/macro/macro_series_catalogo.parquet" }')
    return ",\n".join(filas)


# ----------------------------------------------------------------------------- vocabulario
def actualizar_vocabulario(check: bool) -> bool:
    ruta = DOCS / "vocabulario.json"
    v = json.loads(ruta.read_text(encoding="utf-8"))
    for t in ("tasas_rendimientos", "divisas_mercado", "precios_actividad", "series"):
        v["tipos"].pop(t, None)
    for spec in TABLAS:
        v["tipos"][spec["nombre"].split(".", 1)[1]] = DETALLE[spec["id"]]
    v["tipos"]["series_catalogo"] = "Catálogo de series"
    v["tablas"] = [t for t in v["tablas"] if t["sector"] != "macro"]
    for spec in TABLAS:
        v["tablas"].append({"id": spec["id"], "alias": [], "nombre": spec["nombre"],
                            "tipo": spec["nombre"].split(".", 1)[1], "sector": "macro",
                            "descripcion": spec["descripcion"],
                            "cobertura": f"Una fila por {FRECUENCIA_FILA[spec['frecuencia']]}"})
    v["tablas"].append({"id": "macro_series_catalogo", "alias": [], "nombre": "macro.series_catalogo",
                        "tipo": "series_catalogo", "sector": "macro",
                        "descripcion": "Catálogo de las series del Banco Central que alimentan las tablas macro: código, nombre, unidad, frecuencia y cobertura.",
                        "cobertura": "Una fila por serie"})
    retirados = ["macro.series", "macro.tasas_rendimientos", "macro.divisas_mercado", "macro.precios_actividad"]
    for r in retirados:
        if r not in v["nombres_retirados"]:
            v["nombres_retirados"].append(r)
    nuevo = json.dumps(v, ensure_ascii=False, indent=2) + "\n"
    cambia = nuevo != ruta.read_text(encoding="utf-8")
    if cambia and not check:
        ruta.write_text(nuevo, encoding="utf-8")
    return cambia


# ----------------------------------------------------------------------------- reemplazo
def reemplazar(ruta: Path, inicio: str, fin: str, contenido: str, check: bool) -> bool:
    texto = ruta.read_text(encoding="utf-8")
    patron = re.compile(re.escape(inicio) + r"\n(?:.*?\n)?" + re.escape(fin), re.S)
    if not patron.search(texto):
        raise SystemExit(f"{ruta}: no se encontraron los marcadores {inicio!r} … {fin!r}")
    nuevo = patron.sub(lambda _: f"{inicio}\n{contenido},\n{fin}", texto, count=1)
    cambia = nuevo != texto
    if cambia and not check:
        ruta.write_text(nuevo, encoding="utf-8")
    return cambia


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    meta = leer_meta()
    hoy = date.today().isoformat()
    if a.check:
        # En modo check no se altera la fecha para no producir falsos positivos.
        dic = (DOCS / "js" / "data_dictionary.js").read_text(encoding="utf-8")
        m = re.search(r'sector: "macro",\n.*?ultimaActualizacion: "(\d{4}-\d{2}-\d{2})"', dic, re.S)
        if m:
            hoy = m.group(1)
    cambios = {
        "sidebar.js": reemplazar(DOCS / "js" / "sidebar.js", "  // <macro:inicio>", "  // <macro:fin>", bloque_sidebar(meta), a.check),
        "data_viewer.js": reemplazar(DOCS / "js" / "data_viewer.js", "  // <macro:inicio>", "  // <macro:fin>", bloque_viewer(), a.check),
        "data_dictionary.js": reemplazar(DOCS / "js" / "data_dictionary.js", "  // <macro:inicio>", "  // <macro:fin>", bloque_dictionary(meta, hoy), a.check),
        "erd_graph.js (nodos)": reemplazar(DOCS / "js" / "erd_graph.js", "  // <macro:inicio>", "  // <macro:fin>", bloque_erd_nodes(meta), a.check),
        "erd_graph.js (enlaces)": reemplazar(DOCS / "js" / "erd_graph.js", "  // <macro-links:inicio>", "  // <macro-links:fin>", bloque_erd_links(), a.check),
        "duckdb_client.js": reemplazar(DOCS / "js" / "duckdb_client.js", "  // <macro:inicio>", "  // <macro:fin>", bloque_duckdb(), a.check),
        "vocabulario.json": actualizar_vocabulario(a.check),
    }
    desact = [k for k, v in cambios.items() if v]
    if a.check:
        if desact:
            print("Sección macro de la web desactualizada en: " + ", ".join(desact))
            return 1
        print("Sección macro de la web al día.")
        return 0
    print("Sección macro de la web actualizada" + (": " + ", ".join(desact) if desact else " (sin cambios)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
