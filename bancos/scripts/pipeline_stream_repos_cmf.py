"""
Extractor y normalizador incremental de saldos REPO (Contratos de Retrocompra)
de la banca comercial chilena vía API CMF Bancos (api.cmfchile.cl / api-sbifv3).

Cuentas contables CMF / Compendio de Normas Contables para Bancos:
- Activo (Pactos / Operaciones con pacto de retroventa / derechos):
    * 1160100 / 1160101 / 1160201 (Contratos de retrocompra y préstamos de valores - Activo)
- Pasivo (Pactos / Operaciones con pacto de retrocompra / obligaciones):
    * 2160100 / 2160101 / 2160201 (Contratos de retrocompra y préstamos de valores - Pasivo)

Diseñado para ejecutarse en GitHub Actions con consulta estrictamente
incremental (solo meses posteriores al último checkpoint o período publicado).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = ROOT / "docs" / "outputs" / "bancos"
PUBLISHED_PARQUET = PUBLISHED_DIR / "bancos_repos_saldos_series.parquet"
PUBLISHED_JSON = PUBLISHED_DIR / "bancos_repos_saldos_series.json"
MAESTRO_PARQUET = PUBLISHED_DIR / "bancos_maestro.parquet"
MACRO_FX = ROOT / "docs" / "outputs" / "macro" / "macro_divisas_mercado.parquet"

API_BASE_URL = "https://api.cmfchile.cl/api-sbifv3/recursos_api/balances"
# Códigos de cuentas contables de retrocompra / pactos según época CMF
CUENTAS_REPO_ACTIVO = ["1160100", "1160101", "1160201", "1160000", "1300000"]
CUENTAS_REPO_PASIVO = ["2160100", "2160101", "2160201", "2160000", "2200000"]

# Códigos de subtotales que no son bancos individuales
CODIGOS_AGREGADOS = {"900", "950", "960", "970", "980", "998", "999"}


def get_api_key() -> str:
    """Busca la API Key entre las variables disponibles en el entorno."""
    for var in ("CMF_API_KEY", "PASSWORD_CMF", "USER_CMF"):
        val = os.environ.get(var, "").strip()
        if val:
            return val
    return ""


def get_tc_map() -> dict[str, float]:
    """Carga mapa de tipos de cambio de cierre mensual desde el módulo macro."""
    if not MACRO_FX.exists():
        return {}
    try:
        df = pd.read_parquet(MACRO_FX)
        return dict(zip(df["periodo"].astype(str), df["usd_clp_cierre"].astype(float)))
    except Exception:
        return {}


def get_maestro_map() -> dict[str, dict[str, str]]:
    """Carga mapa de metadatos de bancos para normalizar nombres y RUT."""
    if not MAESTRO_PARQUET.exists():
        return {}
    try:
        df = pd.read_parquet(MAESTRO_PARQUET)
        res = {}
        for _, row in df.iterrows():
            code = str(row["codigo_institucion"]).strip().zfill(3)
            res[code] = {
                "rut": str(row.get("rut", "")),
                "razon_social": str(row.get("razon_social", "")),
                "nombre_fantasia": str(row.get("nombre_fantasia", "")),
            }
        return res
    except Exception:
        return {}


def fetch_cmf_json(url: str, max_retries: int = 3, timeout: int = 25) -> dict[str, Any] | None:
    """Descarga JSON desde la API CMF con reintentos y ocultamiento de claves."""
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "MonitorFinancieroChile/1.0 (+https://github.com/joaquinignaciomondaca-code)",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    raw = response.read().decode("utf-8", errors="replace")
                    return json.loads(raw)
        except Exception as e:
            if attempt == max_retries:
                # Sanitizar URL para nunca imprimir la api_key en logs
                parsed = urllib.parse.urlsplit(url)
                qs = urllib.parse.parse_qs(parsed.query)
                safe_qs = urllib.parse.urlencode({k: ("***" if "api" in k.lower() else v) for k, v in qs.items()})
                safe_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, safe_qs, ""))
                print(f"[AVISO] Error al consultar {safe_url}: {e}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)
    return None


def fetch_mes_cuenta(year: int, month: int, cuenta: str, api_key: str) -> list[dict[str, Any]]:
    """Consulta los saldos de una cuenta contable específica para todas las IFI del mes."""
    url = f"{API_BASE_URL}/{year:04d}/{month:02d}/cuentas/{cuenta}?apikey={api_key}&formato=json"
    data = fetch_cmf_json(url)
    if not data:
        return []
    items = data.get("CodigosBalances", {}).get("CodigoBalanceIFI", [])
    if isinstance(items, dict):
        items = [items]
    res = []
    for it in items:
        code = str(it.get("CodigoInstitucion") or it.get("códigoInstitucion") or "").strip().zfill(3)
        # La API entrega montos en miles de pesos chilenos
        monto_str = str(it.get("MonedaTotal") or "0").replace(".", "").replace(",", ".")
        try:
            monto_m_clp = float(monto_str) / 1000.0  # convertir miles a millones de CLP
        except ValueError:
            monto_m_clp = 0.0
        res.append({
            "codigo_institucion": code,
            "nombre_institucion": it.get("NombreInstitucion") or it.get("DescripcionInstitucion") or "",
            "cuenta": cuenta,
            "monto_mm_clp": monto_m_clp,
        })
    return res


def load_baseline() -> pd.DataFrame:
    """Carga el dataset publicado como base para preservar historia."""
    if PUBLISHED_PARQUET.exists():
        return pd.read_parquet(PUBLISHED_PARQUET)
    return pd.DataFrame()


def determine_target_periods(df_base: pd.DataFrame) -> list[str]:
    """
    Calcula los meses a consultar de forma estrictamente incremental:
    desde el último mes presente en el dataset hasta el mes actual.
    """
    now = datetime.now()
    mes_actual = f"{now.year:04d}-{now.month:02d}"
    if df_base.empty or "periodo" not in df_base.columns:
        p_prev = f"{now.year if now.month > 2 else now.year - 1:04d}-{(now.month - 2) if now.month > 2 else (now.month + 10):02d}"
        return pd.period_range(p_prev, mes_actual, freq="M").strftime("%Y-%m").tolist()

    ultimo_guardado = str(df_base["periodo"].max())
    rango = pd.period_range(ultimo_guardado, mes_actual, freq="M").strftime("%Y-%m").tolist()
    return rango


def process_period(
    periodo: str,
    api_key: str,
    tc_map: dict[str, float],
    maestro_map: dict[str, dict[str, str]],
) -> pd.DataFrame:
    """Consulta la API para un período específico y estructura los registros."""
    y_str, m_str = periodo.split("-")
    year, month = int(y_str), int(m_str)

    activos_por_banco: dict[str, float] = {}
    pasivos_por_banco: dict[str, float] = {}
    nombres_api: dict[str, str] = {}

    for c_act in CUENTAS_REPO_ACTIVO:
        filas = fetch_mes_cuenta(year, month, c_act, api_key)
        if filas:
            for f in filas:
                b = f["codigo_institucion"]
                if b not in CODIGOS_AGREGADOS:
                    activos_por_banco[b] = max(activos_por_banco.get(b, 0.0), f["monto_mm_clp"])
                    if f["nombre_institucion"]:
                        nombres_api[b] = f["nombre_institucion"]
            break

    for c_pas in CUENTAS_REPO_PASIVO:
        filas = fetch_mes_cuenta(year, month, c_pas, api_key)
        if filas:
            for f in filas:
                b = f["codigo_institucion"]
                if b not in CODIGOS_AGREGADOS:
                    pasivos_por_banco[b] = max(pasivos_por_banco.get(b, 0.0), f["monto_mm_clp"])
                    if f["nombre_institucion"]:
                        nombres_api[b] = f["nombre_institucion"]
            break

    todos_bancos = sorted(set(activos_por_banco.keys()) | set(pasivos_por_banco.keys()))
    if not todos_bancos:
        return pd.DataFrame()

    tc = tc_map.get(periodo, 900.0)
    fin_mes = (pd.to_datetime(f"{periodo}-01") + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")

    records = []
    for b in todos_bancos:
        act_clp = round(activos_por_banco.get(b, 0.0), 2)
        pas_clp = round(pasivos_por_banco.get(b, 0.0), 2)
        neto_clp = round(act_clp - pas_clp, 2)

        act_usd = round(act_clp / tc, 2) if tc > 0 else 0.0
        pas_usd = round(pas_clp / tc, 2) if tc > 0 else 0.0
        neto_usd = round(act_usd - pas_usd, 2)
        total_usd = round(act_usd + pas_usd, 2)

        pos = "Neutro"
        if neto_clp > 0:
            pos = "Prestamista Neto de Liquidez"
        elif neto_clp < 0:
            pos = "Tomador Neto de Fondeo"

        m_info = maestro_map.get(b, {})
        rut = m_info.get("rut", "")
        razon_social = m_info.get("razon_social") or nombres_api.get(b, f"Banco {b}")
        nombre_fantasia = m_info.get("nombre_fantasia") or nombres_api.get(b, f"BANCO {b}")

        records.append({
            "id_repo": f"{b}_{periodo}",
            "periodo": periodo,
            "fecha_corte": fin_mes,
            "codigo_institucion": b,
            "rut": rut,
            "razon_social": razon_social,
            "nombre_fantasia": nombre_fantasia,
            "repo_activo_mm_clp": act_clp,
            "repo_pasivo_mm_clp": pas_clp,
            "repo_neto_mm_clp": neto_clp,
            "tc_usd_cierre": tc,
            "repo_activo_mm_usd": act_usd,
            "repo_pasivo_mm_usd": pas_usd,
            "repo_neto_mm_usd": neto_usd,
            "total_transado_mm_usd": total_usd,
            "posicion_relativa": pos,
        })

    return pd.DataFrame(records)


def run_bancos_repo_pipeline(
    output_dir: Path | None = None,
    baseline_df: pd.DataFrame | None = None,
) -> tuple[bool, int]:
    """Ejecuta la actualización incremental contra la API CMF."""
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] Falta API Key de CMF (defina CMF_API_KEY o PASSWORD_CMF)", file=sys.stderr)
        return False, 0

    out = output_dir or PUBLISHED_DIR
    out.mkdir(parents=True, exist_ok=True)

    base = baseline_df if baseline_df is not None else load_baseline()
    tc_map = get_tc_map()
    maestro_map = get_maestro_map()
    target_periods = determine_target_periods(base)

    print(f"[CMF REPO] Períodos a evaluar de forma incremental: {target_periods}")
    nuevos_meses = []
    for p in target_periods:
        df_p = process_period(p, api_key, tc_map, maestro_map)
        if not df_p.empty:
            nuevos_meses.append(df_p)

    if not nuevos_meses:
        print("[CMF REPO] No se obtuvieron datos nuevos desde la API CMF.")
        return True, 0

    nuevos_df = pd.concat(nuevos_meses, ignore_index=True)

    # Fusionar con el histórico sin sobrescribir períodos que la API no entregó
    if not base.empty:
        # Reemplazar únicamente los períodos que efectivamente se descargaron con éxito
        periodos_descargados = set(nuevos_df["periodo"].unique())
        base_filtrada = base[~base["periodo"].isin(periodos_descargados)]
        consolidado = pd.concat([base_filtrada, nuevos_df], ignore_index=True)
    else:
        consolidado = nuevos_df

    consolidado = consolidado.sort_values(["periodo", "codigo_institucion"]).reset_index(drop=True)

    parquet_path = out / "bancos_repos_saldos_series.parquet"
    json_path = out / "bancos_repos_saldos_series.json"

    consolidado.to_parquet(parquet_path, index=False)
    consolidado.to_json(json_path, orient="records", date_format="iso", indent=2)

    print(f"[CMF REPO] Exportados {len(consolidado):,} registros ({len(nuevos_df)} del lote incremental).")
    return True, len(nuevos_df)


if __name__ == "__main__":
    ok, count = run_bancos_repo_pipeline()
    sys.exit(0 if ok else 1)
