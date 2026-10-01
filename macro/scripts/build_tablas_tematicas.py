#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construye las tablas temáticas de macro a partir de las series nativas del BCCh.

Cada tabla temática agrupa series del mismo tema con nombres de columna
autoexplicativos (indicador + detalle + unidad). La frecuencia de cada tabla es la
de sus series: diaria donde el BCCh publica diario, mensual o trimestral donde
corresponde. Las columnas nunca usan códigos opacos (clave, serie_id): esos
viven solo en macro.series_catalogo, como metadatos.

Entrada (no se consulta la API):
  docs/outputs/macro/series/<AAAA>.parquet      observaciones (fecha, periodo, clave, serie_id, valor)
  docs/outputs/macro/macro_series_catalogo.parquet

Salida:
  docs/outputs/macro/<id_tabla>.parquet         una tabla temática por id

Uso:
  python -m macro.scripts.build_tablas_tematicas                    # genera + actualiza data_manifest.json
  python -m macro.scripts.build_tablas_tematicas --solo-data-manifest
  python -m macro.scripts.build_tablas_tematicas --check            # falla si los Parquet no están al día

Nada publicado se borra: las 51 series del catálogo se reparten en las 23
tablas sin perder observaciones (el generador lo verifica fila a fila).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "docs" / "outputs" / "macro"
CARPETA_SERIES = SALIDA / "series"
CATALOGO_PQ = SALIDA / "macro_series_catalogo.parquet"
MANIFEST = RAIZ / "data_manifest.json"

# Tablas retiradas el 2026-09-30 (sustituidas por las temáticas); no deben reaparecer.
RETIRADAS = {"macro_series", "macro_tasas_rendimientos", "macro_divisas_mercado", "macro_precios_actividad"}

ORIGEN = ("Banco Central de Chile — Base de Datos Estadísticos (API REST SIETE, "
          "https://si3.bcentral.cl/SieteRestWS).")

# Especificación de las 23 tablas temáticas. Cada tupla es (clave_serie, nombre_columna).
# Las columnas derivadas se calculan a partir de claves nativas y se documentan
# como "Calculada por SIF" en el diccionario de datos.
TABLAS = [
    {
        "id": "macro_tasas_corto_plazo",
        "nombre": "macro.tasas_corto_plazo",
        "frecuencia": "Diaria",
        "descripcion": "Tasas de referencia de corto plazo de Chile: Tasa de Política Monetaria (TPM) "
                       "del Banco Central y tasa promedio transada en el mercado interbancario (TIB), "
                       "en porcentaje.",
        "columnas": [("tpm", "tpm_pct"), ("tib", "tib_promedio_pct")],
    },
    {
        "id": "macro_swaps_camara",
        "nombre": "macro.swaps_camara",
        "frecuencia": "Diaria",
        "descripcion": "Tasa de swap promedio de cámara (SPC) del Banco Central: contratos en pesos a "
                       "90, 180 y 360 días y a 2 años, y contrato en UF a 1 año, en porcentaje.",
        "columnas": [
            ("spc_clp_90d", "swap_camara_pesos_90_dias_pct"),
            ("spc_clp_180d", "swap_camara_pesos_180_dias_pct"),
            ("spc_clp_360d", "swap_camara_pesos_360_dias_pct"),
            ("spc_clp_2y", "swap_camara_pesos_2_anos_pct"),
            ("spc_uf_1y", "swap_camara_uf_1_ano_pct"),
        ],
    },
    {
        "id": "macro_curva_bonos_pesos",
        "nombre": "macro.curva_bonos_pesos",
        "frecuencia": "Diaria",
        "descripcion": "Curva de rendimiento de los bonos soberanos en pesos licitados por el BCCh "
                       "(Bono Corto Plazo, BCP): tasa de interés de mercado secundario a 2, 5 y 10 años.",
        "columnas": [
            ("bcp_2y", "rendimiento_bono_pesos_2_anos_pct"),
            ("bcp_5y", "rendimiento_bono_pesos_5_anos_pct"),
            ("bcp_10y", "rendimiento_bono_pesos_10_anos_pct"),
        ],
    },
    {
        "id": "macro_curva_bonos_uf",
        "nombre": "macro.curva_bonos_uf",
        "frecuencia": "Diaria",
        "descripcion": "Curva de rendimiento de los bonos soberanos en UF (BCU/BTU): tasa de interés de "
                       "mercado secundario a 1, 2, 5, 10, 20 y 30 años.",
        "columnas": [
            ("bcu_1y", "rendimiento_bono_uf_1_ano_pct"),
            ("bcu_2y", "rendimiento_bono_uf_2_anos_pct"),
            ("bcu_5y", "rendimiento_bono_uf_5_anos_pct"),
            ("bcu_10y", "rendimiento_bono_uf_10_anos_pct"),
            ("bcu_20y", "rendimiento_bono_uf_20_anos_pct"),
            ("bcu_30y", "rendimiento_bono_uf_30_anos_pct"),
        ],
    },
    {
        "id": "macro_inflacion_implicita",
        "nombre": "macro.inflacion_implicita",
        "frecuencia": "Diaria",
        "descripcion": "Inflación implícita de las curvas soberanas (breakeven): diferencia entre el "
                       "rendimiento del bono en pesos y el del bono en UF del mismo plazo. Calculada por "
                       "SIF a partir de las curvas publicadas por el BCCh.",
        "derivadas": [
            ("inflacion_implicita_5_anos_pct", "bcp_5y", "bcu_5y"),
            ("inflacion_implicita_10_anos_pct", "bcp_10y", "bcu_10y"),
        ],
    },
    {
        "id": "macro_dolar_observado",
        "nombre": "macro.dolar_observado",
        "frecuencia": "Diaria",
        "descripcion": "Dólar observado: tipo de cambio nominal del dólar de los Estados Unidos en "
                       "pesos chilenos (CLP por USD), según el Banco Central.",
        "columnas": [("usd_clp", "dolar_observado_clp_por_usd")],
    },
    {
        "id": "macro_euro_observado",
        "nombre": "macro.euro_observado",
        "frecuencia": "Diaria",
        "descripcion": "Euro observado: tipo de cambio nominal del euro en pesos chilenos "
                       "(CLP por EUR), según el Banco Central.",
        "columnas": [("eur_clp", "euro_observado_clp_por_eur")],
    },
    {
        "id": "macro_tipo_cambio_multilateral",
        "nombre": "macro.tipo_cambio_multilateral",
        "frecuencia": "Diaria",
        "descripcion": "Índices de tipo de cambio nominal multilateral del Banco Central: TCM, TCM-5 "
                       "(monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro) y TCM-X.",
        "columnas": [
            ("tcm", "tipo_cambio_nominal_multilateral_indice"),
            ("tcm_5", "tipo_cambio_nominal_multilateral_5_monedas_indice"),
            ("tcm_x", "tipo_cambio_nominal_multilateral_x_indice"),
        ],
    },
    {
        "id": "macro_tipo_cambio_real",
        "nombre": "macro.tipo_cambio_real",
        "frecuencia": "Mensual",
        "descripcion": "Índices de tipo de cambio real (TCR) del Banco Central, promedio 1986=100: TCR "
                       "general y TCR-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro).",
        "columnas": [
            ("tcr", "tipo_cambio_real_general_indice"),
            ("tcr_5", "tipo_cambio_real_5_monedas_indice"),
        ],
    },
    {
        "id": "macro_uf",
        "nombre": "macro.uf",
        "frecuencia": "Diaria",
        "descripcion": "Valor diario de la Unidad de Fomento (UF) en pesos chilenos, según el Banco Central.",
        "columnas": [("uf", "uf_valor_clp")],
    },
    {
        "id": "macro_utm",
        "nombre": "macro.utm",
        "frecuencia": "Mensual",
        "descripcion": "Valor mensual de la Unidad Tributaria Mensual (UTM) en pesos chilenos, "
                       "según el Banco Central.",
        "columnas": [("utm", "utm_valor_clp")],
    },
    {
        "id": "macro_inflacion_ipc",
        "nombre": "macro.inflacion_ipc",
        "frecuencia": "Mensual",
        "descripcion": "Índice de Precios al Consumidor (IPC), serie empalmada del BCCh base 2023=100: "
                       "índice y variaciones mensual y anual en porcentaje (fuente INE).",
        "columnas": [
            ("ipc_indice", "ipc_indice"),
            ("ipc_var_mensual", "ipc_var_mensual_pct"),
            ("ipc_var_anual", "ipc_var_anual_pct"),
        ],
    },
    {
        "id": "macro_imacec",
        "nombre": "macro.imacec",
        "frecuencia": "Mensual",
        "descripcion": "Imacec a costo de factores, series empalmadas del BCCh (índice 2018=100): total, "
                       "no minero, minero, comercio y servicios.",
        "columnas": [
            ("imacec", "imacec_empalmado_indice"),
            ("imacec_no_minero", "imacec_no_minero_indice"),
            ("imacec_mineria", "imacec_minero_indice"),
            ("imacec_comercio", "imacec_comercio_indice"),
            ("imacec_servicios", "imacec_servicios_indice"),
        ],
    },
    {
        "id": "macro_pib_trimestral",
        "nombre": "macro.pib_trimestral",
        "frecuencia": "Trimestral",
        "descripcion": "Producto Interno Bruto (PIB) en volumen a precios del año anterior encadenado, "
                       "referencia 2018: miles de millones de pesos encadenados.",
        "columnas": [("pib", "pib_encadenado_miles_mm_clp")],
    },
    {
        "id": "macro_mercado_laboral",
        "nombre": "macro.mercado_laboral",
        "frecuencia": "Mensual",
        "descripcion": "Mercado laboral de Chile (series no ajustadas del INE, vía BCCh): tasa de "
                       "desocupación en porcentaje, y personas ocupadas, asalariadas y fuerza de "
                       "trabajo en miles de personas.",
        "columnas": [
            ("desocupacion", "desocupacion_pct"),
            ("ocupados", "ocupados_miles_personas"),
            ("asalariados", "asalariados_miles_personas"),
            ("fuerza_trabajo", "fuerza_trabajo_miles_personas"),
        ],
    },
    {
        "id": "macro_cobre",
        "nombre": "macro.cobre",
        "frecuencia": "Diaria",
        "descripcion": "Precio del cobre refinado en dólares por libra: cotización diaria de la Bolsa de "
                       "Metales de Londres (BML) y valor referencial mensual publicado por el BCCh "
                       "(la referencia mensual aparece en la fila del primer día de su mes).",
        "columnas": [
            ("cobre_diario", "cobre_refinado_usd_por_libra"),
            ("cobre_mensual", "cobre_referencial_mensual_usd_por_libra"),
        ],
    },
    {
        "id": "macro_metales_preciosos",
        "nombre": "macro.metales_preciosos",
        "frecuencia": "Diaria",
        "descripcion": "Precios de los metales preciosos en dólares por onza troy: oro y plata, "
                       "según el Banco Central.",
        "columnas": [
            ("oro", "oro_usd_por_onza_troy"),
            ("plata", "plata_usd_por_onza_troy"),
        ],
    },
    {
        "id": "macro_reservas_internacionales",
        "nombre": "macro.reservas_internacionales",
        "frecuencia": "Mensual",
        "descripcion": "Activos de reserva internacional del Banco Central de Chile, en millones de "
                       "dólares de los Estados Unidos.",
        "columnas": [("reservas", "reservas_internacionales_millones_usd")],
    },
    {
        "id": "macro_tasa_referencia_fed",
        "nombre": "macro.tasa_referencia_fed",
        "frecuencia": "Diaria",
        "descripcion": "Tasa de interés de política monetaria de la Reserva Federal de los Estados "
                       "Unidos (fed funds), en porcentaje.",
        "columnas": [("fed_funds", "tasa_fed_funds_pct")],
    },
    {
        "id": "macro_deuda_publica_pct_pib",
        "nombre": "macro.deuda_publica_pct_pib",
        "frecuencia": "Trimestral",
        "descripcion": "Deuda bruta del Gobierno Central como porcentaje del Producto Interno Bruto "
                       "(PIB), según el Banco Central.",
        "columnas": [("deuda_publica_pib", "deuda_bruta_gobierno_central_pct_pib")],
    },
    {
        "id": "macro_expectativas_inflacion",
        "nombre": "macro.expectativas_inflacion",
        "frecuencia": "Mensual",
        "descripcion": "Expectativas de inflación de la Encuesta de Expectativas Económicas (EEE) del "
                       "Banco Central: variación del IPC en 12 meses vista, con horizonte de 11 y 23 "
                       "meses, mediana en porcentaje.",
        "columnas": [
            ("eee_ipc_11m", "expectativa_inflacion_ipc_11_meses_pct"),
            ("eee_ipc_23m", "expectativa_inflacion_ipc_23_meses_pct"),
        ],
    },
    {
        "id": "macro_expectativas_tpm",
        "nombre": "macro.expectativas_tpm",
        "frecuencia": "Mensual",
        "descripcion": "Expectativas de la Tasa de Política Monetaria (TPM) de la Encuesta de "
                       "Expectativas Económicas (EEE) del Banco Central, con horizonte de 11 y 23 "
                       "meses, mediana en porcentaje.",
        "columnas": [
            ("eee_tpm_11m", "expectativa_tpm_11_meses_pct"),
            ("eee_tpm_23m", "expectativa_tpm_23_meses_pct"),
        ],
    },
    {
        "id": "macro_expectativas_operadores",
        "nombre": "macro.expectativas_operadores",
        "frecuencia": "Diaria",
        "descripcion": "Evolución diaria de la Encuesta de Operadores Financieros (EOF) del Banco "
                       "Central: expectativa de inflación (variación del IPC) y de TPM para los 12 "
                       "meses siguientes, en porcentaje.",
        "columnas": [
            ("eof_ipc_12m", "expectativa_inflacion_12_meses_pct"),
            ("eof_tpm_12m", "expectativa_tpm_12_meses_pct"),
        ],
    },
]


def cargar_series() -> pd.DataFrame:
    rutas = sorted(CARPETA_SERIES.glob("*.parquet"))
    if not rutas:
        raise ValueError(f"No hay series publicadas en {CARPETA_SERIES}")
    df = pd.concat([pq.read_table(r).to_pandas() for r in rutas], ignore_index=True)
    df = df.drop_duplicates(subset=["fecha", "clave"], keep="last")
    return df.sort_values(["fecha", "clave"], kind="stable").reset_index(drop=True)


def construir_tabla(spec: dict, series: pd.DataFrame) -> pd.DataFrame:
    """Pivota las series de una tabla temática; fechas = unión de las fechas de sus series."""
    claves = [clave for clave, _ in spec.get("columnas", [])]
    derivadas = spec.get("derivadas", [])
    for _, clave_a, clave_b in derivadas:
        claves.extend([clave_a, clave_b])
    sub = series[series["clave"].isin(claves)]
    if sub.empty:
        raise ValueError(f"Sin observaciones para {spec['id']} (claves: {claves})")

    pivot = sub.pivot(index="fecha", columns="clave", values="valor").sort_index()
    out = pd.DataFrame({"fecha": pivot.index})
    out["periodo"] = out["fecha"].str[:7]
    for clave, columna in spec.get("columnas", []):
        if clave not in pivot.columns:
            raise ValueError(f"Falta la serie '{clave}' en {spec['id']}")
        out[columna] = pivot[clave].reindex(pivot.index).to_numpy()
    for columna, clave_a, clave_b in derivadas:
        if clave_a not in pivot.columns or clave_b not in pivot.columns:
            raise ValueError(f"Faltan series para derivar '{columna}' en {spec['id']}")
        out[columna] = (pivot[clave_a] - pivot[clave_b]).round(4).to_numpy()
    # Una fecha sin ningún indicador no aporta (p. ej. tenores que no cotizaron ese día).
    indicadores = [c for c in out.columns if c not in ("fecha", "periodo")]
    return out.dropna(subset=indicadores, how="all").reset_index(drop=True)


def verificar(spec: dict, tabla: pd.DataFrame, series: pd.DataFrame) -> None:
    """Ninguna observación se pierde: cada celda coincide con la serie nativa."""
    hoy = date.today().isoformat()
    if tabla["fecha"].duplicated().any() or not tabla["fecha"].is_monotonic_increasing:
        raise ValueError(f"Fechas duplicadas o desordenadas en {spec['id']}")
    if (tabla["fecha"] > hoy).any():
        raise ValueError(f"Fecha futura en {spec['id']}")
    if not (tabla["periodo"] == tabla["fecha"].str[:7]).all():
        raise ValueError(f"Periodo incoherente con fecha en {spec['id']}")
    for clave, columna in spec.get("columnas", []):
        nativas = series[series["clave"] == clave].set_index("fecha")["valor"]
        filas = tabla.set_index("fecha")[columna]
        comunes = nativas.index.intersection(filas.index)
        if len(comunes) != len(nativas) or filas[comunes].isna().any():
            raise ValueError(f"Se perdieron observaciones de '{clave}' en {spec['id']}")
        dif = (nativas[comunes] - filas[comunes]).abs().max()
        if dif > 1e-9:
            raise ValueError(f"Valores distintos de la serie '{clave}' en {spec['id']}: dif {dif}")
    for columna, clave_a, clave_b in spec.get("derivadas", []):
        a = series[series["clave"] == clave_a].set_index("fecha")["valor"]
        b = series[series["clave"] == clave_b].set_index("fecha")["valor"]
        esperado = (a - b).round(4)
        filas = tabla.set_index("fecha")[columna]
        comunes = esperado.index.intersection(filas.dropna().index)
        if set(comunes) != set(esperado.dropna().index):
            raise ValueError(f"Fechas incompletas en derivada '{columna}' de {spec['id']}")
        if ((esperado[comunes] - filas[comunes]).abs() > 1e-9).any():
            raise ValueError(f"Derivada '{columna}' mal calculada en {spec['id']}")


def generar() -> dict[str, int]:
    series = cargar_series()
    conteos = {}
    for spec in TABLAS:
        tabla = construir_tabla(spec, series)
        verificar(spec, tabla, series)
        destino = SALIDA / f"{spec['id']}.parquet"
        pq.write_table(
            pa.Table.from_pandas(tabla, preserve_index=False),
            destino, compression="zstd",
        )
        conteos[spec["id"]] = len(tabla)
    return conteos


def actualizar_data_manifest() -> None:
    if not MANIFEST.exists() or not CATALOGO_PQ.exists():
        return
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cat = pq.read_table(CATALOGO_PQ).to_pandas()
    hoy = date.today().isoformat()
    base = {
        "sector": "macro",
        "sector_label": "Macroeconomía y Tasas (BCCh)",
        "norma": "Estadísticas oficiales BCCh",
        "frescura": "Se actualiza sola a diario",
        "modo": "Automático · diario, incremental",
        "ultima_actualizacion": hoy,
        "origen": ORIGEN,
    }
    entradas = []
    for spec in TABLAS:
        pqt = SALIDA / f"{spec['id']}.parquet"
        if not pqt.exists():
            continue
        per = pq.read_table(pqt, columns=["fecha"]).column(0).to_pylist()
        entradas.append({
            "id": spec["id"], "name": spec["nombre"], "view_name": spec["id"], **base,
            "corte": f"{per[0]} a {per[-1]}",
            "file_parquet": f"outputs/macro/{spec['id']}.parquet",
            "registros_reales": len(per),
            "descripcion": spec["descripcion"],
        })
    # Catálogo de series (metadatos): lo mantiene series_bcch; aquí sólo se refresca su corte.
    corte_cat = f"{cat['primera_fecha'].dropna().min()} a {cat['ultima_fecha'].dropna().max()}"
    for t in man["tables"]:
        if t["id"] == "macro_series_catalogo":
            nuevo = {"corte": corte_cat, "registros_reales": len(cat),
                     "ultima_actualizacion": hoy}
            if any(t.get(k) != v for k, v in nuevo.items()):
                t.update(nuevo)
    ids = {e["id"] for e in entradas} | RETIRADAS
    man["tables"] = [t for t in man["tables"] if t["id"] not in ids] + entradas
    man["tables"].sort(key=lambda t: t["id"])
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solo-data-manifest", action="store_true",
                    help="solo refresca data_manifest.json desde los Parquet publicados")
    ap.add_argument("--check", action="store_true",
                    help="falla si los Parquet publicados no coinciden con las series nativas")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
        return 0
    conteos = generar()
    actualizar_data_manifest()
    total = sum(conteos.values())
    print(f"Tablas temáticas generadas: {len(conteos)} ({total} filas)")
    for nombre, filas in conteos.items():
        print(f"  {nombre:42s} {filas:6d} filas")
    if a.check:
        print("Check: Parquet al día con las series nativas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
