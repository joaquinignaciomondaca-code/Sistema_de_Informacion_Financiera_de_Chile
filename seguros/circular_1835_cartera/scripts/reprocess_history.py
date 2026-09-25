"""
Reprocesamiento Histórico de Derivados B.7 - Circular 1835 CMF
============================================================
Descarga en streaming directo (in-memory) y recalibra todas las posiciones
con el nuevo parser dinámico inmune a desfases de longitud.
"""

import os
import sys
import io
import time
import threading
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Rutas del módulo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUTS_DIR = os.path.join(MODULE_DIR, "outputs")
CONTROL_FILE = os.path.join(MODULE_DIR, "control_descargas.csv")

sys.path.insert(0, SCRIPT_DIR)
from process_b7_derivatives import extract_contracts_from_zip, consolidate_contracts

BASE_URL = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
ENTITIES = {
    "generales": "CSGEN",
    "vida": "CSVID"
}

save_lock = threading.Lock()


def load_control():
    if os.path.exists(CONTROL_FILE):
        try:
            return pd.read_csv(CONTROL_FILE, dtype=str)
        except Exception:
            pass
    return pd.DataFrame(columns=["periodo", "sector", "estado", "forwards", "swaps", "repos", "opciones", "fecha_proceso"])


def record_status_threadsafe(periodo, sector, estado, counts):
    with save_lock:
        ctrl_df = load_control()
        ctrl_df = ctrl_df[~((ctrl_df["periodo"] == periodo) & (ctrl_df["sector"] == sector))]
        nueva_fila = {
            "periodo": periodo,
            "sector": sector,
            "estado": estado,
            "forwards": counts.get("forwards", 0),
            "swaps": counts.get("swaps", 0),
            "repos": counts.get("repos", 0),
            "opciones": counts.get("opciones", 0),
            "fecha_proceso": datetime.now().isoformat()
        }
        ctrl_df = pd.concat([ctrl_df, pd.DataFrame([nueva_fila])], ignore_index=True)
        ctrl_df.sort_values(by=["periodo", "sector"]).to_csv(CONTROL_FILE, index=False, encoding="utf-8")


def process_period_worker(sector, periodo):
    entity_code = ENTITIES[sector]
    yyyymm = periodo.replace("-", "")
    download_url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=descarga&peri={yyyymm}"
    filename_hint = f"{yyyymm}_{sector}.zip"

    req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                if not data.startswith(b"PK"):
                    return {"status": "NO_ZIP", "periodo": periodo, "sector": sector, "counts": {}}

                buffer = io.BytesIO(data)
                contracts = extract_contracts_from_zip(buffer, filename_hint=filename_hint)

                # Consolidación thread-safe
                with save_lock:
                    counts = consolidate_contracts(contracts)

                record_status_threadsafe(periodo, sector, "COMPLETO", counts)
                return {"status": "OK", "periodo": periodo, "sector": sector, "counts": counts}
        except Exception as e:
            if attempt == 2:
                return {"status": "ERROR", "periodo": periodo, "sector": sector, "error": str(e), "counts": {}}
            time.sleep(2)


def run_reprocessing(max_workers=3):
    print("=" * 80)
    print("REPROCESAMIENTO HISTÓRICO TOTAL - DERIVADOS B.7 (CMF SEGUROS)")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hilos concurrentes: {max_workers}")
    print("=" * 80)

    ctrl_df = load_control()
    if ctrl_df.empty:
        print("[ERROR] No se encontró historial en control_descargas.csv")
        return

    # Limpiar o reiniciar los outputs para que no queden datos antiguos desalineados
    print("\nReiniciando datasets de salida en outputs/...")
    for name in ["forwards", "swaps", "repos", "opciones"]:
        p_path = os.path.join(OUTPUTS_DIR, f"b7_{name}.parquet")
        c_path = os.path.join(OUTPUTS_DIR, f"b7_{name}.csv")
        if os.path.exists(p_path):
            os.remove(p_path)
        if os.path.exists(c_path):
            os.remove(c_path)

    # Identificar todas las tareas que estaban completas
    tasks = []
    for _, row in ctrl_df.iterrows():
        if row.get("estado") == "COMPLETO":
            tasks.append((row["sector"].lower(), row["periodo"]))

    total_tasks = len(tasks)
    print(f"Total períodos a recalibrar y procesar: {total_tasks}")

    completed = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_period_worker, s, p): (s, p) for s, p in tasks}

        for f in as_completed(futures):
            res = f.result()
            completed += 1
            elapsed = time.time() - t0
            avg_time = elapsed / completed
            eta_mins = (total_tasks - completed) * avg_time / 60.0

            if res["status"] == "OK":
                c = res["counts"]
                print(f"[{completed}/{total_tasks}] (ETA {eta_mins:.1f}m) OK {res['sector'].upper():<9} {res['periodo']} -> "
                      f"Fwd:{c.get('forwards',0)} Swp:{c.get('swaps',0)} Rep:{c.get('repos',0)} Opc:{c.get('opciones',0)}")
            else:
                print(f"[{completed}/{total_tasks}] (ETA {eta_mins:.1f}m) {res['status']} {res['sector'].upper()} {res['periodo']}")

    print("\n" + "=" * 80)
    print(f"REPROCESAMIENTO COMPLETADO en {(time.time()-t0)/60:.1f} minutos.")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=3, help="Número de hilos concurrentes")
    args = parser.parse_args()
    run_reprocessing(max_workers=args.workers)
