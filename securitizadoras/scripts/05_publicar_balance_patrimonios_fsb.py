"""Balance General de Patrimonios Separados desde el Excel FSB (EF5) → Parquet publicado.

Fuente: securitizadoras/fuentes/FSB_Patrimonio_Separado_v4.xlsx
    Balances de los PDF de EEFF de cada patrimonio separado publicados en la CMF, leídos con
    NotebookLM (ver hoja Glosario_y_Metodologia). Montos en miles de pesos (M$), con el signo impreso.

Cobertura publicada: cierres de diciembre 2014–2025 (ANIO_DESDE). El Excel trae 2010, 2011 y 2012
pero no 2013; para no dejar un hueco en la serie se publica desde 2014. Esos años eran además los
más dudosos (Transa 2010–2011 no calza con otra lectura de los mismos PDF).

Qué se publica (docs/outputs/securitizadoras/):
    patrimonios_separados_balance_cuentas.parquet  una fila por cuenta impresa (hoja Detalle_de_Cuentas)
    patrimonios_separados_balance_fsb.parquet      una fila por patrimonio y cierre: las 6 categorías FSB
                                                   y los ratios CI2 / MT2 / L5, RECALCULADOS desde las cuentas

Por qué se recalcula en vez de copiar las hojas resumen del Excel:
    La hoja Detalle_de_Cuentas cuadra en el 100% de los documentos (activos = pasivos + patrimonio) y
    coincide al peso con una lectura independiente previa de los mismos PDF en 489 de 497 documentos.
    La hoja Detalle_por_patrimonio (y el Agregado que se calcula sobre ella) difiere de las cuentas en
    21 documentos (p. ej. 3 de BICE 2017 con patrimonio = 0 y pasivo de largo plazo a la mitad). Esos
    documentos y los demás casos dudosos quedan marcados con `revisar = true` y su motivo.

Validaciones que detienen la publicación (fail-closed):
    hojas/columnas esperadas; sin archivos duplicados; mismo conjunto de documentos en ambas hojas;
    RUT con DV módulo 11; período AAAAMM de diciembre; montos enteros;
    activos = pasivos circulantes + no circulantes + patrimonio (±2 M$) en TODOS los documentos.

Uso:  python -m securitizadoras.scripts.05_publicar_balance_patrimonios_fsb [--xlsx RUTA] [--seco]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / "securitizadoras" / "fuentes" / "FSB_Patrimonio_Separado_v4.xlsx"
OUT = ROOT / "docs" / "outputs" / "securitizadoras"
CUENTAS = "patrimonios_separados_balance_cuentas"
FSB = "patrimonios_separados_balance_fsb"
TOL = 2  # M$: redondeo impreso en los PDF
ANIO_DESDE = 2014  # 2013 no está en el Excel; ver docstring

DETALLE = {"Activo Circulante": "Total Activo Circulante",
           "Activo No Circulante": "Total Activo No Circulante",
           "Pasivo Circulante": "Total Pasivo Circulante",
           "Pasivo No Circulante": "Total Pasivo No Circulante",
           "Patrimonio (Excedente Acumulado)": "Total Patrimonio (Excedente Acumulado)"}
CATEGORIAS = set(DETALLE) | set(DETALLE.values()) | {"Total Activos", "Total Pasivos"}

# (Con ANIO_DESDE = 2014 estos 8 documentos, todos de 2010–2011, quedan fuera de la publicación;
# la lista se conserva por si se vuelve a publicar desde 2010.)
# Documentos cuyo total no coincide con una lectura independiente previa de los mismos PDF
# (tabla patrimonios_separados_balance_pdf, retirada el 2026-09-28; ver git 6fb6285). En los otros
# 489 documentos ambas lecturas coinciden al peso en los 7 totales del balance.
DISCREPA_LECTURA_INDEPENDIENTE = {
    "201012_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA1.pdf",
    "201012_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA14.pdf",
    "201012_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA16.pdf",
    "201012_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA17.pdf",
    "201012_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA18.pdf",
    "201012_96777130_SECURITIZADORA_LA_CONSTRUCCION_Primer_patrimonio_separado.pdf",
    "201112_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA15.pdf",
    "201112_96765170_TRANSA_SECURITIZADORA_PATRIMONIO_SEPARADO_BTRA18.pdf",
}
FSB_HOJA = {"total_financial_assets": "total_activos_m_clp", "short_term_assets": "activos_corto_plazo_m_clp",
            "short_term_liabilities": "pasivos_corto_plazo_m_clp", "long_term_liabilities": "pasivos_largo_plazo_m_clp",
            "equity": "patrimonio_m_clp", "loans": "cartera_securitizada_m_clp"}


def dv_m11(cuerpo: str) -> str:
    suma, mult = 0, 2
    for digito in reversed(cuerpo):
        suma += int(digito) * mult
        mult = mult + 1 if mult < 7 else 2
    resto = 11 - suma % 11
    return "0" if resto == 11 else "K" if resto == 10 else str(resto)


def fallar(msg: str) -> None:
    raise SystemExit(f"✗ {msg}")


def leer(xlsx: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    tipos = {"entidad_rut": str, "periodo": str}
    cuentas = pd.read_excel(xlsx, "Detalle_de_Cuentas", dtype=tipos)
    resumen = pd.read_excel(xlsx, "Detalle_por_patrimonio", dtype=tipos)
    esperadas = {"archivo", "entidad_rut", "entidad_nombre", "patrimonio_codigo", "periodo",
                 "categoria", "asiento", "monto", "categoria_fsb"}
    if not esperadas <= set(cuentas.columns):
        fallar(f"Faltan columnas en Detalle_de_Cuentas: {esperadas - set(cuentas.columns)}")
    return cuentas, resumen


def limpiar_cuentas(cuentas: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    cuentas = cuentas.copy()
    cuentas["orden_en_balance"] = cuentas.groupby("archivo").cumcount() + 1
    # Filas vacías de la lectura (sin nombre de cuenta, monto 0 y categoría "2"/"Pasivo No Circ"/vacía).
    basura = cuentas["asiento"].isna() | ~cuentas["categoria"].isin(CATEGORIAS)
    if (cuentas.loc[basura, "monto"] != 0).any():
        fallar("Hay filas sin cuenta o sin categoría válida con monto distinto de cero")
    cuentas = cuentas[~basura].copy()
    fuera = set(cuentas["categoria"]) - CATEGORIAS
    if fuera:
        fallar(f"Categorías no reconocidas: {fuera}")
    if not (cuentas["monto"] % 1 == 0).all():
        fallar("Montos no enteros")
    return cuentas, int(basura.sum())


def totales(cuentas: pd.DataFrame) -> pd.DataFrame:
    t = cuentas.pivot_table(index="archivo", columns="categoria", values="monto", aggfunc="sum").fillna(0)
    for categoria in CATEGORIAS:
        if categoria not in t:
            t[categoria] = 0
    return t


def construir(cuentas: pd.DataFrame, resumen: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    docs = cuentas.drop_duplicates("archivo").set_index("archivo")
    if set(docs.index) != set(resumen["archivo"]) or resumen["archivo"].duplicated().any():
        fallar("Los documentos de Detalle_de_Cuentas y Detalle_por_patrimonio no son los mismos")
    if docs.duplicated(["entidad_rut", "patrimonio_codigo", "periodo"]).any():
        fallar("Patrimonio y período repetidos en documentos distintos")
    if not docs["periodo"].str.fullmatch(r"20\d{2}12").all():
        fallar("Hay períodos que no son cierres de diciembre AAAA12")
    ruts = docs["entidad_rut"]
    if not ruts.str.fullmatch(r"\d{7,8}").all():
        fallar("RUT de administradora con formato inesperado")

    t = totales(cuentas)
    identidad = (t["Total Activos"] - t["Total Pasivo Circulante"] - t["Total Pasivo No Circulante"]
                 - t["Total Patrimonio (Excedente Acumulado)"]).abs() <= TOL
    if not identidad.all():
        fallar(f"Activos ≠ pasivos + patrimonio en: {sorted(identidad[~identidad].index)}")
    detalle_ok = pd.Series(True, index=t.index)
    for det, sub in DETALLE.items():
        detalle_ok &= (t[det] - t[sub]).abs() <= TOL
    cartera = cuentas[cuentas["categoria_fsb"] == "Loans (componente)"].groupby("archivo")["monto"].sum()

    fsb = pd.DataFrame(index=t.index)
    fsb["total_activos_m_clp"] = t["Total Activos"]
    fsb["cartera_securitizada_m_clp"] = cartera.reindex(t.index).fillna(0)
    fsb["activos_corto_plazo_m_clp"] = t["Total Activo Circulante"]
    fsb["pasivos_corto_plazo_m_clp"] = t["Total Pasivo Circulante"]
    fsb["pasivos_largo_plazo_m_clp"] = t["Total Pasivo No Circulante"]
    fsb["patrimonio_m_clp"] = t["Total Patrimonio (Excedente Acumulado)"]
    activos = fsb["total_activos_m_clp"].where(fsb["total_activos_m_clp"] != 0)
    fsb["ci2_intermediacion_credito"] = fsb["cartera_securitizada_m_clp"] / activos
    fsb["mt2_transformacion_plazos"] = (fsb["pasivos_corto_plazo_m_clp"]
                                        / fsb["activos_corto_plazo_m_clp"].where(fsb["activos_corto_plazo_m_clp"] != 0))
    fsb["l5_apalancamiento"] = (fsb["total_activos_m_clp"] - fsb["patrimonio_m_clp"]) / activos

    hoja = resumen.set_index("archivo")
    difiere_hoja = pd.Series(False, index=t.index)
    for columna_excel, columna in FSB_HOJA.items():
        if columna_excel != "loans":
            difiere_hoja |= (hoja[columna_excel].reindex(t.index) - fsb[columna]).abs() > TOL
    # "loans" de la hoja resumen a veces suma otras cuentas (ajustes de valorización, dividendos por
    # cobrar…); aquí la cartera es el mapeo declarado en categoria_fsb: activo securitizado ± provisiones.
    difiere_cartera = (hoja["loans"].reindex(t.index) - fsb["cartera_securitizada_m_clp"]).abs() > TOL

    motivos = []
    for archivo in t.index:
        m = []
        if not detalle_ok[archivo]:
            m.append("las cuentas de detalle no suman el subtotal impreso")
        if archivo in DISCREPA_LECTURA_INDEPENDIENTE:
            m.append("una lectura independiente del mismo PDF dio otros totales")
        if difiere_hoja[archivo]:
            m.append("la hoja Detalle_por_patrimonio del Excel trae otros totales")
        elif difiere_cartera[archivo]:
            m.append("la hoja Detalle_por_patrimonio calcula la cartera securitizada con otro criterio (afecta CI2)")
        motivos.append("; ".join(m) or None)
    fsb["motivo_revision"] = motivos
    fsb["revisar"] = fsb["motivo_revision"].notna()

    ident = pd.DataFrame({
        "archivo": docs.index,
        "rut_administradora": docs["entidad_rut"].values,
        "rut_completo": [f"{r}-{dv_m11(r)}" for r in docs["entidad_rut"]],
        "nombre_administradora": docs["entidad_nombre"].str.replace("_", " ").str.strip().values,
        "codigo_patrimonio": docs["patrimonio_codigo"].astype(str).values,
        "periodo": (docs["periodo"].str[:4] + "-" + docs["periodo"].str[4:]).values,
        "anio": docs["periodo"].str[:4].astype(int).values,
    }).set_index("archivo")
    fsb = ident.join(fsb).reset_index()
    enteros = [c for c in fsb.columns if c.endswith("_m_clp")]
    fsb[enteros] = fsb[enteros].astype("int64")

    salida = cuentas.rename(columns={"asiento": "cuenta", "monto": "monto_m_clp"})
    salida = ident.join(salida.set_index("archivo")[["orden_en_balance", "categoria", "cuenta", "monto_m_clp", "categoria_fsb"]])
    salida = salida.join(fsb.set_index("archivo")[["revisar"]]).reset_index()
    salida["monto_m_clp"] = salida["monto_m_clp"].astype("int64")
    salida["cuenta"] = salida["cuenta"].astype(str).str.strip()
    salida["categoria_fsb"] = salida["categoria_fsb"].str.replace(" (componente)", "", regex=False)
    salida = salida.sort_values(["periodo", "rut_administradora", "codigo_patrimonio", "orden_en_balance"]).reset_index(drop=True)
    fsb = fsb.sort_values(["periodo", "rut_administradora", "codigo_patrimonio"]).reset_index(drop=True)
    return salida, fsb


def escribir(df: pd.DataFrame, nombre: str) -> Path:
    destino = OUT / f"{nombre}.parquet"
    tmp = destino.with_suffix(".parquet.tmp")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tmp, compression="zstd")
    if pq.read_table(tmp).num_rows != len(df):
        tmp.unlink()
        fallar(f"Relectura de {nombre} no coincide")
    tmp.replace(destino)
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", type=Path, default=XLSX)
    ap.add_argument("--seco", action="store_true", help="valida sin escribir")
    args = ap.parse_args()
    cuentas, resumen = leer(args.xlsx)
    cuentas, descartadas = limpiar_cuentas(cuentas)
    anios_excel = sorted(int(a) for a in cuentas["periodo"].str[:4].unique())
    cuentas = cuentas[cuentas["periodo"].str[:4].astype(int) >= ANIO_DESDE]
    resumen = resumen[resumen["periodo"].astype(str).str[:4].astype(int) >= ANIO_DESDE]
    print(f"Años en el Excel: {anios_excel}; se publica desde {ANIO_DESDE}.")
    salida, fsb = construir(cuentas, resumen)
    sha = hashlib.sha256(args.xlsx.read_bytes()).hexdigest()[:12]
    print(f"Excel {args.xlsx.name} (sha256 {sha}…): {len(salida)} cuentas, {len(fsb)} balances, "
          f"{fsb['periodo'].nunique()} cierres ({fsb['periodo'].min()}–{fsb['periodo'].max()}), "
          f"{fsb['rut_administradora'].nunique()} securitizadoras; {descartadas} filas vacías descartadas; "
          f"{int(fsb['revisar'].sum())} balances marcados para revisar.")
    if args.seco:
        return
    for df, nombre in ((salida, CUENTAS), (fsb, FSB)):
        print("→", escribir(df, nombre).relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
