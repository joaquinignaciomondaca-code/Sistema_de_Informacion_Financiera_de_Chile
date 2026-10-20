#!/usr/bin/env python3
"""Auditoría de punta a punta de tres conjuntos publicados (punto 6 de la auditoría).

Conjuntos:
  1. ffmm/cartera_nacional      (automático, CMF)            — integridad, duplicados, cruce con ffmm/ffmm_balance
  2. securitizadoras/patrimonios_separados_balance (híbrido PDF → Excel curado → Parquet)
                                                              — reconciliación con el Excel, identidad contable, trazabilidad
  3. macro/macro_uf             (series, Banco Central)      — continuidad, duplicados, ciclo de reajuste día 10

Uso:  python scripts/auditar_fuente_a_fila.py   (desde la raíz del repo; requiere pyarrow, pandas, openpyxl)
Sale con código 1 si una comprobación de integridad falla. Las advertencias no detienen el script.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
errores: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("  OK    " if ok else "  FALLA ") + msg)
    if not ok:
        errores.append(msg)


def aviso(msg: str) -> None:
    print("  AVISO " + msg)


def seccion(titulo: str) -> None:
    print(f"\n== {titulo}")


# 0. Integridad de archivos frente al inventario de reproducibilidad
seccion("0. SHA-256 de los archivos frente a docs/reproducibilidad/inventario_fuentes.csv")
inv = list(csv.DictReader(open(DOCS / "reproducibilidad" / "inventario_fuentes.csv", encoding="utf-8")))
hash_ok = hash_mal = 0
for r in inv:
    if r["tabla"] not in {"cartera_nacional", "macro_uf", "patrimonios_separados_balance", "ffmm_balance"}:
        continue
    p = DOCS / r["archivo"]
    if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == r["sha256"]:
        hash_ok += 1
    else:
        hash_mal += 1
check(hash_mal == 0, f"hashes coinciden: {hash_ok}; distintos o ausentes: {hash_mal}")
ffmm_inv = [r for r in inv if r["tabla"] == "cartera_nacional" and r["sector"] == "ffmm"]
fi_inv = [r for r in inv if r["tabla"] == "cartera_nacional" and r["sector"] == "fi"]
aviso(f"'cartera_nacional' aparece en dos sectores del inventario: ffmm ({len(ffmm_inv)} entradas: Parquet y manifiesto) y fi ({len(fi_inv)}). "
      "El nombre de tabla no es único; la clave correcta es sector + tabla.")

# 1. Cartera nacional de fondos mutuos
seccion("1. ffmm/cartera_nacional (automático, CMF) — periodo 2025-12 para el cruce")
manifest = json.load(open(DOCS / "outputs/ffmm/cartera_nacional/manifest.json", encoding="utf-8"))
total = 0
for f in manifest["files"]:
    total += pd.read_parquet(DOCS / f, columns=["periodo"]).shape[0]
check(total == manifest["total_records"], f"filas Parquet {total:,} = manifiesto {manifest['total_records']:,}")
cart = pd.read_parquet(DOCS / "outputs/ffmm/cartera_nacional/2025-12.parquet")
bal = pd.read_parquet(DOCS / "outputs/ffmm/ffmm_balance/2025.parquet")
bal = bal[bal.periodo == "2025-12"]
dups_exactos = int(cart.duplicated().sum())
aviso(f"2025-12: {dups_exactos:,} filas exactamente duplicadas en {cart[cart.duplicated(keep=False)].run_fondo.nunique()} fondos; "
      "el Parquet no tiene identificador de línea de origen, así que no se puede decidir si son lotes distintos o repetición")
check(not (cart.valorizacion_miles_mf < 0).any() and cart.valorizacion_miles_mf.notna().all(),
      "valorización sin nulos ni negativos")
suma_pct = cart.groupby("run_fondo").pct_activo_fondo.sum()
suma_pct_sin = cart.drop_duplicates().groupby("run_fondo").pct_activo_fondo.sum()
aviso(f"suma de pct_activo_fondo por fondo, mediana: {suma_pct.median():.2f} % con duplicados; "
      f"{suma_pct_sin.median():.2f} % sin duplicados (los duplicados acercan los pesos a 100 %)")
tot_c = cart.groupby("run_fondo").valorizacion_miles_mf.sum()
tot_b = bal[bal.cuenta.str.lower().str.strip() == "total activo"].groupby("run_fondo").valor_miles_mf.sum()
j = pd.concat([tot_c.rename("cartera"), tot_b.rename("activo")], axis=1, join="inner")
r = j.cartera / j.activo
check(int((r > 1.01).sum()) == 0, f"cartera ≤ total activo en todos los fondos cruzados ({len(j)} de {len(tot_c)} fondos tienen balance)")
aviso(f"fondos con cartera < 50 % del activo: {int((r < 0.5).sum())} de {len(r)}; cobertura parcial a explicar en la metodología")
aviso("trazabilidad: cartera_nacional no guarda archivo de origen ni hash por fila; ffmm_balance sí (fuente_archivo, sha256_archivo)")

# 2. Patrimonios separados (híbrido)
seccion("2. securitizadoras/patrimonios_separados_balance (híbrido PDF → Excel curado)")
xl = pd.read_excel(ROOT / "securitizadoras/fuentes/balances_patrimonios_separados.xlsx", "Balance_por_cuenta",
                   dtype={"entidad_rut": str, "periodo": str})
pub = pd.read_parquet(DOCS / "outputs/securitizadoras/patrimonios_separados_balance.parquet")
anio = xl.periodo.str[:4].astype(int)
CATEGORIAS = {"Activo Circulante", "Activo No Circulante", "Pasivo Circulante", "Pasivo No Circulante",
              "Patrimonio (Excedente Acumulado)", "Total Activo Circulante", "Total Activo No Circulante",
              "Total Pasivo Circulante", "Total Pasivo No Circulante", "Total Patrimonio (Excedente Acumulado)",
              "Total Activos", "Total Pasivos"}  # mismas reglas que 05_publicar_balance_patrimonios.py
vacias = xl.asiento.isna() | ~xl.categoria.isin(CATEGORIAS)
aviso(f"{int(vacias.sum())} filas del Excel descartadas por cuenta o categoría inválida, todas con monto 0; "
      "tres tienen columnas desplazadas o abreviadas (curación manual)")
n_pre2014 = int(((anio < 2014) & ~vacias).sum())
check(len(xl) - int(vacias.sum()) - n_pre2014 == len(pub),
      f"conteo: Excel {len(xl):,} − vacías {int(vacias.sum())} − anteriores a 2014 {n_pre2014:,} = publicado {len(pub):,}")
piv = pub.pivot_table(index="archivo", columns="categoria", values="monto_m_clp", aggfunc="sum").fillna(0)
ident = (piv["Total Activos"] - piv["Total Pasivo Circulante"] - piv["Total Pasivo No Circulante"]
         - piv["Total Patrimonio (Excedente Acumulado)"]).abs()
check(int((ident > 2).sum()) == 0, f"activos = pasivos + patrimonio en {len(piv)} balances (máx. diferencia {int(ident.max())} M$)")
aviso(f"{int(pub.duplicated(['archivo', 'categoria', 'cuenta']).sum())} pares archivo+categoría+cuenta repetidos: "
      "una misma cuenta aparece en dos líneas; la clave única debe incluir orden_en_balance")
muestra = pub[pub.categoria == "Total Activos"].sample(1, random_state=7).iloc[0]
ref = xl[(xl.archivo == muestra.archivo) & (xl.categoria == "Total Activos")]
check(len(ref) == 1 and int(ref.monto.iloc[0]) == int(muestra.monto_m_clp),
      f"fila de muestra {muestra.nombre_administradora} {muestra.periodo}: Parquet {int(muestra.monto_m_clp):,} = Excel")
aviso(f"trazabilidad: el campo 'archivo' nombra el PDF de la CMF ({muestra.archivo}), pero el PDF y la página no están en el repositorio")

# 3. Serie UF (Banco Central)
seccion("3. macro/macro_uf (series, Banco Central)")
u = pd.read_parquet(DOCS / "outputs/macro/macro_uf.parquet")
u["fecha"] = pd.to_datetime(u["fecha"])
u = u.sort_values("fecha").reset_index(drop=True)
cal = pd.date_range(u.fecha.min(), u.fecha.max(), freq="D")
check(len(cal.difference(u.fecha)) == 0 and not u.fecha.duplicated().any(),
      f"calendario diario completo {u.fecha.min().date()} → {u.fecha.max().date()}, sin duplicados ({len(u):,} filas)")
u["d"] = u.uf_valor_clp.diff()
check(bool((u.d.dropna().abs() / u.uf_valor_clp.shift(1).dropna() <= 0.001).all()), "ningún salto diario mayor a 0,1 %")
ciclo = (u.fecha - pd.DateOffset(days=9)).dt.to_period("M")
signos = u.dropna(subset=["d"]).assign(ciclo=ciclo).groupby("ciclo").d.agg(lambda x: set((x > 0).astype(int) - (x < 0).astype(int)) - {0})
check(int((signos.map(len) > 1).sum()) == 0,
      f"signo constante dentro de cada ciclo de reajuste (día 10 → día 9): {len(signos)} ciclos")
ref_uf = {"2024-01-01": 36797.64, "2025-01-01": 38419.17, "2025-01-31": 38384.41,
          "2025-12-31": 39727.96, "2026-01-01": 39731.79, "2026-10-19": 41183.94}
malos = [f for f, v in ref_uf.items() if abs(float(u.loc[u.fecha == f, "uf_valor_clp"].iloc[0]) - v) >= 0.005]
check(not malos, f"6 fechas de referencia públicas coinciden con el Parquet (diferencias: {malos or 'ninguna'})")

print("\nResultado:", "sin fallas de integridad" if not errores else f"{len(errores)} falla(s)")
sys.exit(1 if errores else 0)
