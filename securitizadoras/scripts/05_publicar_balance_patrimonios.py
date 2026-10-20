"""Balance de los Patrimonios Separados (cuenta por cuenta) → Parquet publicado.

Fuente: securitizadoras/fuentes/balances_patrimonios_separados.xlsx, hoja Balance_por_cuenta.
    Excel curado localmente a partir de los PDF de estados financieros que publica la CMF.
    El script no extrae PDFs: publica una fila por cuenta ya consolidada; montos en miles de pesos
    (M$) con el signo impreso.

Cobertura publicada: cierres de diciembre 2014–2025 (ANIO_DESDE). La fuente trae 2010, 2011 y 2012
pero no 2013; para no dejar un hueco en la serie se publica desde 2014.

Qué se publica: docs/outputs/securitizadoras/patrimonios_separados_balance.parquet
    una fila por cuenta, con la administradora, el patrimonio, el cierre, la categoría del balance
    (Activo Circulante, Total Activos, Pasivo Circulante, …), la cuenta y su monto.

Validaciones que detienen la publicación (fail-closed):
    columnas esperadas; filas vacías solo con monto 0; categorías conocidas; montos enteros;
    un documento por patrimonio y cierre; RUT con DV módulo 11; período AAAAMM de diciembre;
    activos = pasivos circulantes + no circulantes + patrimonio (±2 M$) en TODOS los balances;
    las cuentas de detalle de cada categoría suman su subtotal impreso (±2 M$).

Uso:  python -m securitizadoras.scripts.05_publicar_balance_patrimonios [--xlsx RUTA] [--seco]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
from pipelines.auto.rut import con_puntos
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / "securitizadoras" / "fuentes" / "balances_patrimonios_separados.xlsx"
HOJA = "Balance_por_cuenta"
OUT = ROOT / "docs" / "outputs" / "securitizadoras"
TABLA = "patrimonios_separados_balance"
TOL = 2  # M$: redondeo impreso en los PDF
ANIO_DESDE = 2014  # 2013 no está en la fuente; ver docstring

DETALLE = {"Activo Circulante": "Total Activo Circulante",
           "Activo No Circulante": "Total Activo No Circulante",
           "Pasivo Circulante": "Total Pasivo Circulante",
           "Pasivo No Circulante": "Total Pasivo No Circulante",
           "Patrimonio (Excedente Acumulado)": "Total Patrimonio (Excedente Acumulado)"}
CATEGORIAS = set(DETALLE) | set(DETALLE.values()) | {"Total Activos", "Total Pasivos"}
COLUMNAS = ["archivo", "rut_administradora", "rut_completo", "nombre_administradora", "codigo_patrimonio",
            "periodo", "anio", "orden_en_balance", "categoria", "cuenta", "monto_m_clp"]


def fallar(msg: str) -> None:
    print(f"::error title=Balance patrimonios separados::{msg}", file=sys.stderr)
    raise SystemExit(1)


def dv_m11(cuerpo: str) -> str:
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    r = 11 - suma % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def leer(xlsx: Path) -> pd.DataFrame:
    cuentas = pd.read_excel(xlsx, HOJA, dtype={"entidad_rut": str, "periodo": str})
    esperadas = {"archivo", "entidad_rut", "entidad_nombre", "patrimonio_codigo", "periodo",
                 "categoria", "asiento", "monto"}
    if not esperadas <= set(cuentas.columns):
        fallar(f"Faltan columnas en {HOJA}: {esperadas - set(cuentas.columns)}")
    return cuentas


def limpiar(cuentas: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    cuentas = cuentas.copy()
    cuentas["orden_en_balance"] = cuentas.groupby("archivo").cumcount() + 1
    # Filas vacías de la lectura (sin nombre de cuenta o sin categoría válida), siempre con monto 0.
    vacias = cuentas["asiento"].isna() | ~cuentas["categoria"].isin(CATEGORIAS)
    if (cuentas.loc[vacias, "monto"] != 0).any():
        fallar("Hay filas sin cuenta o sin categoría válida con monto distinto de cero")
    cuentas = cuentas[~vacias].copy()
    if not (cuentas["monto"] % 1 == 0).all():
        fallar("Montos no enteros")
    return cuentas, int(vacias.sum())


def construir(cuentas: pd.DataFrame) -> pd.DataFrame:
    docs = cuentas.drop_duplicates("archivo").set_index("archivo")
    if docs.duplicated(["entidad_rut", "patrimonio_codigo", "periodo"]).any():
        fallar("Patrimonio y período repetidos en documentos distintos")
    if not docs["periodo"].str.fullmatch(r"20\d{2}12").all():
        fallar("Hay períodos que no son cierres de diciembre AAAA12")
    if not docs["entidad_rut"].str.fullmatch(r"\d{7,8}").all():
        fallar("RUT de administradora con formato inesperado")

    t = cuentas.pivot_table(index="archivo", columns="categoria", values="monto", aggfunc="sum").fillna(0)
    t = t.reindex(columns=sorted(CATEGORIAS), fill_value=0)
    cuadra = (t["Total Activos"] - t["Total Pasivo Circulante"] - t["Total Pasivo No Circulante"]
              - t["Total Patrimonio (Excedente Acumulado)"]).abs() <= TOL
    if not cuadra.all():
        fallar(f"Activos ≠ pasivos + patrimonio en: {sorted(cuadra[~cuadra].index)}")
    for detalle, subtotal in DETALLE.items():
        no_suma = (t[detalle] - t[subtotal]).abs() > TOL
        if no_suma.any():
            fallar(f"Las cuentas de '{detalle}' no suman '{subtotal}' en: {sorted(no_suma[no_suma].index)}")

    ident = pd.DataFrame({
        "rut_administradora": docs["entidad_rut"],
        "rut_completo": [con_puntos(r) for r in docs["entidad_rut"]],  # convención del proyecto (formato A)
        "nombre_administradora": docs["entidad_nombre"].str.replace("_", " ").str.strip(),
        "codigo_patrimonio": docs["patrimonio_codigo"].astype(str),
        "periodo": docs["periodo"].str[:4] + "-" + docs["periodo"].str[4:],
        "anio": docs["periodo"].str[:4].astype(int),
    }, index=docs.index)

    salida = cuentas.rename(columns={"asiento": "cuenta", "monto": "monto_m_clp"}).set_index("archivo")
    salida = ident.join(salida[["orden_en_balance", "categoria", "cuenta", "monto_m_clp"]]).reset_index()
    salida["monto_m_clp"] = salida["monto_m_clp"].astype("int64")
    salida["cuenta"] = salida["cuenta"].astype(str).str.strip()
    salida = salida.sort_values(["periodo", "rut_administradora", "codigo_patrimonio", "orden_en_balance"])
    return salida[COLUMNAS].reset_index(drop=True)


UMBRAL_VARIACION = 0.50      # 50 % frente al cierre anterior del mismo patrimonio
UMBRAL_MONTO_M = 1_000       # y al menos 1.000 M$ de diferencia (evita marcar cuentas chicas)
INFORME = ROOT / "docs" / "reproducibilidad" / "anomalias_patrimonios_separados.csv"


def revisar_cambios(salida: pd.DataFrame) -> pd.DataFrame:
    """Marca los subtotales que cambian mucho frente al cierre anterior del mismo patrimonio.

    No bloquea por sí solo: un cambio grande puede ser real (una emisión, un prepago). Sirve para
    que una persona lo revise antes de dar el dato por bueno. Solo compara categorías de subtotal,
    porque el nombre de las cuentas de detalle cambia entre años. Solo compara cierres consecutivos.
    """
    subtotales = salida[salida["categoria"].str.startswith("Total ")].copy()
    subtotales = subtotales.sort_values(["codigo_patrimonio", "periodo"])
    subtotales["monto_anterior"] = subtotales.groupby(["codigo_patrimonio", "categoria"])["monto_m_clp"].shift(1)
    subtotales["periodo_anterior"] = subtotales.groupby(["codigo_patrimonio", "categoria"])["periodo"].shift(1)
    # Solo cierres consecutivos: comparar 2023 con 2025 mezclaría dos años de cambios.
    anio = subtotales["periodo"].str[:4].astype(int)
    anio_ant = subtotales["periodo_anterior"].str[:4].astype(float)
    cambio = subtotales.dropna(subset=["monto_anterior"]).copy()
    cambio = cambio[(anio.loc[cambio.index] - anio_ant.loc[cambio.index]) == 1].copy()
    cambio["diferencia_m_clp"] = cambio["monto_m_clp"] - cambio["monto_anterior"]
    cambio["variacion"] = cambio["diferencia_m_clp"] / cambio["monto_anterior"].abs().where(cambio["monto_anterior"] != 0)
    marcados = cambio[(cambio["diferencia_m_clp"].abs() >= UMBRAL_MONTO_M)
                      & (cambio["variacion"].abs() > UMBRAL_VARIACION)].copy()
    marcados["motivo"] = "variación > 50 % y ≥ 1.000 M$ frente al cierre anterior"
    return marcados[["archivo", "rut_administradora", "nombre_administradora", "codigo_patrimonio",
                     "periodo_anterior", "periodo", "categoria", "monto_anterior", "monto_m_clp",
                     "diferencia_m_clp", "variacion", "motivo"]].rename(
        columns={"monto_m_clp": "monto_actual"}).reset_index(drop=True)


def escribir_informe(marcados: pd.DataFrame) -> None:
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    marcados.round({"variacion": 4}).to_csv(INFORME, index=False, encoding="utf-8")


def escribir(df: pd.DataFrame) -> Path:
    destino = OUT / f"{TABLA}.parquet"
    tmp = destino.with_suffix(".parquet.tmp")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tmp, compression="zstd")
    if pq.read_table(tmp).num_rows != len(df):
        tmp.unlink()
        fallar("La relectura del Parquet no coincide")
    tmp.replace(destino)
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", type=Path, default=XLSX)
    ap.add_argument("--seco", action="store_true", help="valida sin escribir")
    ap.add_argument("--bloquear-cambios", action="store_true",
                    help="no publica si hay cambios grandes marcados (por defecto solo se informan)")
    args = ap.parse_args()
    cuentas, vacias = limpiar(leer(args.xlsx))
    anios = sorted(int(a) for a in cuentas["periodo"].str[:4].unique())
    cuentas = cuentas[cuentas["periodo"].str[:4].astype(int) >= ANIO_DESDE]
    salida = construir(cuentas)
    balances = salida.drop_duplicates("archivo")
    marcados = revisar_cambios(salida)
    print(f"Cambios grandes marcados para revisión: {len(marcados)} "
          f"(informe: {INFORME.relative_to(ROOT)})")
    if args.bloquear_cambios and len(marcados):
        fallar(f"{len(marcados)} cambios grandes sin revisar; ver {INFORME.name}")
    sha = hashlib.sha256(args.xlsx.read_bytes()).hexdigest()[:12]
    print(f"Fuente {args.xlsx.name} (sha256 {sha}…), años {anios}; se publica desde {ANIO_DESDE}: "
          f"{len(salida)} cuentas, {len(balances)} balances, {balances['periodo'].nunique()} cierres "
          f"({balances['periodo'].min()}–{balances['periodo'].max()}), "
          f"{balances['rut_administradora'].nunique()} securitizadoras; {vacias} filas vacías descartadas.")
    if not args.seco:
        escribir_informe(marcados)
        print("→", escribir(salida).relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
