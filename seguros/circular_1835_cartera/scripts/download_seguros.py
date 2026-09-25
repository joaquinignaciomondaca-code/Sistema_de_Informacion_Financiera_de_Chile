# -*- coding: utf-8 -*-
"""
descargar_carteras.py — Descarga mensual de carteras B.7 (seguros generales y vida).

=== QUE HACE ===
Descarga los ZIPs mensuales de carteras de inversión (Circular B.7) desde el
portal de la CMF usando Playwright + resolución de CAPTCHA. Gestiona un registro
de control CSV (meses_descargados.csv) para saber qué meses están completos o
parciales. El *último* mes detectado siempre se re-descarga (las aseguradoras
pueden reportar de a poco).

=== COMO CORRER ===
    cd /d D:/Compañias_de_seguro
    python -m scripts.ingestion.descargar_carteras

=== OUTPUT EXACTO ===
  Carpeta: 01_cartera_B7/raw/carteras/generales/
           01_cartera_B7/raw/carteras/vida/
  Archivos: cartera_generales_AAAA_MM.zip
            cartera_vida_AAAA_MM.zip
  Control:  01_cartera_B7/raw/carteras/meses_descargados.csv
            columnas: periodo, sector, estado, n_archivos_zip, fecha_proceso
            estado ∈ {completo, parcial}  (parcial = último mes, se re-descarga)

=== CONFIG ===
  FECHA_INICIO        : primer mes a descargar (AAAA-MM)
  FECHA_FIN           : "auto" = mes actual; o "AAAA-MM" fijo
  REPROCESAR_PARCIALES: True  = re-descarga meses marcados "parcial"
"""

# =============================================================================
# CONFIG (editar aqui antes de correr)
# =============================================================================
FECHA_INICIO         = "2020-01"   # primer mes a descargar (AAAA-MM)
FECHA_FIN            = "auto"      # "auto" = mes actual del sistema; o "AAAA-MM"
REPROCESAR_PARCIALES = True        # True = re-descarga meses "parcial"
MAX_WORKERS          = 2           # hilos paralelos de Playwright
# =============================================================================

import io
import sys
import subprocess
import threading
import time
import json
from datetime import datetime, date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def _ensure(pkg: str, import_name: str = None):
    """Importa un paquete; si falla, lo instala con pip y reintenta."""
    name = import_name or pkg
    try:
        __import__(name)
    except ImportError:
        print(f"[setup] Instalando {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        __import__(name)


_ensure("playwright", "playwright.sync_api")
_ensure("playwright-stealth", "playwright_stealth")
_ensure("tqdm")
_ensure("pandas")

import pandas as pd
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import Stealth
    _HAS_STEALTH = True
except ImportError:
    _HAS_STEALTH = False

# Rutas portables desde la raiz del proyecto
_HERE = Path(__file__).resolve()
PROJECT_ROOT = _HERE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config.paths import CARTERAS_DIR, COOKIES_FILE, SECRETS_DIR, ensure_project_dirs

# ----- Constantes de descarga -----
BASE_URL_TEMPLATE = (
    "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/"
    "cartera_inversiones/dcisgv/descarga_cartera_inv.php?tipoentidad={}"
)
ENTITY_TYPES = {
    "CSVID": "vida",
    "CSGEN": "generales",
}

# Control CSV  (por-sector, para poder re-descargar independientemente)
CTRL_CSV = CARTERAS_DIR / "meses_descargados.csv"
_CTRL_COLS = ["periodo", "sector", "estado", "n_archivos_zip", "fecha_proceso"]

_DB_LOCK = threading.Lock()


# ===========================================================================
# CONTROL CSV
# ===========================================================================

def _leer_control() -> pd.DataFrame:
    if CTRL_CSV.exists():
        return pd.read_csv(CTRL_CSV, dtype=str)
    return pd.DataFrame(columns=_CTRL_COLS)


def _guardar_control(df: pd.DataFrame):
    df = df.sort_values(["periodo", "sector"]).reset_index(drop=True)
    df.to_csv(CTRL_CSV, index=False, encoding="utf-8")


def _estado(ctrl: pd.DataFrame, periodo: str, sector: str) -> str | None:
    row = ctrl[(ctrl["periodo"] == periodo) & (ctrl["sector"] == sector)]
    if row.empty:
        return None
    return row.iloc[0]["estado"]


def _registrar(ctrl: pd.DataFrame, periodo: str, sector: str,
               estado: str, n_zip: int) -> pd.DataFrame:
    fila = {
        "periodo":        periodo,
        "sector":         sector,
        "estado":         estado,
        "n_archivos_zip": str(n_zip),
        "fecha_proceso":  datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    mask = (ctrl["periodo"] == periodo) & (ctrl["sector"] == sector)
    ctrl = ctrl[~mask].copy()
    ctrl = pd.concat([ctrl, pd.DataFrame([fila])], ignore_index=True)
    return ctrl


# ===========================================================================
# HELPERS DE RANGO
# ===========================================================================

def _periodos_rango(ini: str, fin: str) -> list[str]:
    y0, m0 = int(ini[:4]), int(ini[5:7])
    y1, m1 = int(fin[:4]), int(fin[5:7])
    out = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _fecha_fin_efectiva() -> str:
    if FECHA_FIN == "auto":
        hoy = date.today()
        return f"{hoy.year}-{hoy.month:02d}"
    return FECHA_FIN


# ===========================================================================
# DESCARGA (un mes, un sector)
# ===========================================================================

def _load_cookies(context):
    if COOKIES_FILE.exists():
        try:
            with io.open(str(COOKIES_FILE), encoding="utf-8") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
        except Exception as e:
            print(f"[warn] No se cargaron cookies: {e}")


def _descargar_mes(entity_code: str, sector: str, year: int, month: int,
                   forzar: bool = False) -> bool:
    """
    Intenta descargar el ZIP de (sector, year, month).
    Devuelve True si tuvo éxito.
    """
    filename = f"cartera_{sector}_{year}_{month:02d}.zip"
    save_path = CARTERAS_DIR / sector / filename

    if save_path.exists() and not forzar:
        return True  # ya descargado

    save_path.parent.mkdir(parents=True, exist_ok=True)
    target_url = BASE_URL_TEMPLATE.format(entity_code)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )
        _load_cookies(context)
        page = context.new_page()
        if _HAS_STEALTH:
            Stealth().apply_stealth_sync(page)
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            page.goto(target_url, timeout=120_000, wait_until="networkidle")
            success = False
            retries = 5
            last_captcha = None

            while retries > 0 and not success:
                try:
                    page.select_option("#s_agno", str(year))
                    page.select_option("#s_mes", f"{month:02d}")
                    time.sleep(2)

                    captcha_el = page.wait_for_selector('img[src*="captcha.php"]')
                    broken = page.evaluate(
                        "(img) => !img.complete || img.naturalWidth === 0",
                        captcha_el,
                    )
                    if broken:
                        page.reload()
                        retries -= 1
                        continue

                    if retries < 5:
                        captcha_el.click()
                        time.sleep(3)
                        captcha_el = page.wait_for_selector('img[src*="captcha.php"]')

                    # Resuelve CAPTCHA (importa al vuelo para no fallar si no existe)
                    try:
                        from scripts.ingestion.captcha_solver import solve_captcha
                        from scripts.config.paths import STAGING_DIR
                        captcha_dir = STAGING_DIR / "captchas"
                        captcha_dir.mkdir(parents=True, exist_ok=True)
                        cap_path = captcha_dir / f"cap_{sector}_{year}_{month}_{int(time.time())}.png"
                        captcha_el.screenshot(path=str(cap_path))
                        captcha_text = solve_captcha(str(cap_path))
                    except Exception as e:
                        print(f"[warn] CAPTCHA solver error: {e}")
                        retries -= 1
                        continue

                    if (not captcha_text or len(captcha_text) != 6
                            or captcha_text == last_captcha):
                        retries -= 1
                        continue
                    last_captcha = captcha_text
                    page.fill("#fcaptcha", captcha_text)

                    with page.expect_download(timeout=120_000) as dl_info:
                        page.click("#b_descargar")
                    dl_info.value.save_as(str(save_path))
                    print(f"[OK] {filename}")
                    success = True

                except Exception as e:
                    print(f"[RETRY] {sector} {year}-{month:02d}: {e}")
                    try:
                        if "captcha.php" not in page.content():
                            print(f"[warn] posible bloqueo WAF, esperando 10 s...")
                            time.sleep(10)
                        page.reload(timeout=60_000)
                    except Exception:
                        pass
                    retries -= 1

            return success

        except Exception as e:
            print(f"[FATAL] {sector} {year}-{month:02d}: {e}")
            return False
        finally:
            try:
                browser.close()
            except Exception:
                pass


# ===========================================================================
# PIPELINE PRINCIPAL
# ===========================================================================

def main():
    ensure_project_dirs()
    fin_str = _fecha_fin_efectiva()
    periodos = _periodos_rango(FECHA_INICIO, fin_str)
    ultimo   = periodos[-1]

    print("=" * 65)
    print("descargar_carteras.py — Carteras B.7 seguros (resiliente)")
    print(f"  FECHA_INICIO         = {FECHA_INICIO}")
    print(f"  FECHA_FIN            = {FECHA_FIN}  -> {fin_str}")
    print(f"  REPROCESAR_PARCIALES = {REPROCESAR_PARCIALES}")
    print(f"  Ultimo periodo       = {ultimo}  (siempre se re-descarga)")
    print(f"  Periodos en rango    = {len(periodos)}")
    print("=" * 65)

    ctrl = _leer_control()

    for periodo in periodos:
        year  = int(periodo[:4])
        month = int(periodo[5:7])
        es_ultimo = (periodo == ultimo)

        for entity_code, sector in ENTITY_TYPES.items():
            estado_actual = _estado(ctrl, periodo, sector)

            # Decidir si procesar
            if estado_actual == "completo" and not es_ultimo:
                print(f"[skip] {periodo} {sector} (completo)")
                continue
            if estado_actual == "parcial" and not REPROCESAR_PARCIALES and not es_ultimo:
                print(f"[skip] {periodo} {sector} (parcial, REPROCESAR_PARCIALES=False)")
                continue

            forzar = es_ultimo or (estado_actual == "parcial")
            print(f"[desc] {periodo} {sector}  forzar={forzar}")

            ok = _descargar_mes(entity_code, sector, year, month, forzar=forzar)

            if ok:
                # Contar archivos en el ZIP para valor_clave
                zip_path = CARTERAS_DIR / sector / f"cartera_{sector}_{year}_{month:02d}.zip"
                try:
                    import zipfile
                    with zipfile.ZipFile(zip_path) as zf:
                        n_zip = len(zf.namelist())
                except Exception:
                    n_zip = 0

                nuevo_estado = "parcial" if es_ultimo else "completo"
                ctrl = _registrar(ctrl, periodo, sector, nuevo_estado, n_zip)
                _guardar_control(ctrl)
            else:
                print(f"[FALLO] {periodo} {sector}")

    print("\n[LISTO] Descarga finalizada.")
    print(f"Control: {CTRL_CSV}")


if __name__ == "__main__":
    main()