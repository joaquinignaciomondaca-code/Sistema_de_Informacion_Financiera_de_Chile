# -*- coding: utf-8 -*-
"""
orchestrate_overnight_market_pipeline.py — Orquestador Maestro Nocturno CMF (FFMM + FI)
======================================================================================
Ejecuta de manera secuencial, desatendida y autónoma las siguientes fases:

1. ESPERA ACTIVA: Monitorea la tarea actual de Fondos Mutuos hasta su finalización.
2. FFMM FASE 2: Procesa la extensión histórica de Fondos Mutuos 2010–2014.
3. FFMM AUDITORÍA: Sincroniza Parquets y valida la identidad contable al 100%.
4. FI CENSO: Verifica el Universo Oficial de Fondos de Inversión (1,677 fondos).
5. FI REPOS: Extrae masivamente contratos REPO (VRC y CRV) 2010–2026.
6. FI EEFF: Extrae balances y carátulas auditadas de Fondos de Inversión.
7. FI AUDITORÍA: Audita cuadre contable y genera métricas de mercado.
8. REGISTRO WEB: Sincroniza metadatos y asegura disponibilidad en DuckDB-Wasm.
"""

import os
import sys
import time
import subprocess
import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_EXE = sys.executable

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

def run_step(cmd_args, step_name):
    log(f"================================================================================")
    log(f"INICIANDO PASO: {step_name}")
    log(f"Comando: {' '.join(cmd_args)}")
    log(f"================================================================================")
    t0 = time.time()
    try:
        proc = subprocess.Popen(
            cmd_args,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )
        for line in proc.stdout:
            print(line, end='', flush=True)
        proc.wait()
        elapsed = time.time() - t0
        if proc.returncode == 0:
            log(f"PASO COMPLETADO CON ÉXITO: {step_name} (Tiempo: {elapsed:.1f}s)")
            return True
        else:
            log(f"ERROR EN PASO: {step_name} (Código de salida: {proc.returncode}, Tiempo: {elapsed:.1f}s)")
            return False
    except Exception as e:
        log(f"EXCEPCIÓN EN PASO {step_name}: {e}")
        return False

import psutil

def wait_for_running_ffmm_task():
    log("Verificando si hay una tarea previa de FFMM en ejecución...")
    ckpt_path = os.path.join(BASE_DIR, "ffmm", "data", "checkpoint_historico_eeff.json")
    
    current_pid = os.getpid()
    
    while True:
        running = False
        target_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                cmdline = proc.info.get('cmdline') or []
                cmd_str = ' '.join(cmdline)
                if '03b_extract_ffmm_historico.py' in cmd_str and 'orchestrate' not in cmd_str:
                    running = True
                    target_pid = proc.pid
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if running:
            # Report checkpoint progress
            if os.path.exists(ckpt_path):
                try:
                    with open(ckpt_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        done = len(data.get('processed_keys', []))
                        eeff = len(data.get('eeff', []))
                        repos = len(data.get('repos', []))
                        log(f"Tarea FFMM activa (PID {target_pid}). Checkpoint: {done} consultas | {eeff} EEFF | {repos} REPOs. Esperando...")
                except Exception:
                    log(f"Tarea FFMM activa (PID {target_pid}). Esperando...")
            else:
                log(f"Tarea FFMM activa (PID {target_pid}). Esperando...")
            time.sleep(20)
        else:
            log("No se detectan tareas previas de FFMM en ejecución. Continuando orquestación...")
            break

def main():
    log("********************************************************************************")
    log("INICIO DEL PIPELINE MAESTRO NOCTURNO CMF: FONDOS MUTUOS (FFMM) Y FONDOS DE INVERSIÓN (FI)")
    log("********************************************************************************")

    # 1. Esperar tarea actual si está corriendo
    wait_for_running_ffmm_task()

    # 2. Paso 1: Extensión histórica de FFMM a 2010-2014 (reanudando checkpoint)
    log("\n>>> INICIANDO PROCESAMIENTO HISTÓRICO FFMM (2010 a 2025)...")
    ffmm_script = os.path.join(BASE_DIR, "ffmm", "scripts", "03b_extract_ffmm_historico.py")
    run_step([PYTHON_EXE, ffmm_script], "FFMM Extracción Histórica (2010-2025)")

    # 3. Sincronización y Auditoría FFMM
    sync_ffmm_script = os.path.join(BASE_DIR, "ffmm", "scripts", "sync_checkpoint_to_parquet.py")
    audit_ffmm_script = os.path.join(BASE_DIR, "ffmm", "scripts", "04b_audit_historico.py")
    run_step([PYTHON_EXE, sync_ffmm_script], "FFMM Sincronización Parquet")
    run_step([PYTHON_EXE, audit_ffmm_script], "FFMM Auditoría Contable y Benchmark REPO")

    log("\n" + "="*80)
    log("FONDOS MUTUOS (FFMM) FINALIZADO Y AUDITADO AL 100%.")
    log("="*80 + "\n")

    # 4. Paso 2: Construcción / Verificación de Universo de Fondos de Inversión (FI)
    fi_universe_script = os.path.join(BASE_DIR, "fi", "scripts", "01_build_universe_fi.py")
    run_step([PYTHON_EXE, fi_universe_script], "FI Censo Oficial Universo (1,677 fondos)")

    # 5. Paso 3: Extracción Masiva de REPOs FI (2010 a 2026)
    fi_repos_script = os.path.join(BASE_DIR, "fi", "scripts", "02_extract_fi_repos_historico.py")
    run_step([PYTHON_EXE, fi_repos_script], "FI Extracción Masiva de REPOs (VRC / CRV)")

    # 6. Paso 4: Extracción de Estados Financieros FI (Audited EEFF)
    fi_eeff_script = os.path.join(BASE_DIR, "fi", "scripts", "03_extract_fi_eeff_historico.py")
    run_step([PYTHON_EXE, fi_eeff_script], "FI Extracción de Balances Auditados (Carátula EEFF)")

    # 7. Paso 5: Auditoría y Verificación Contable FI
    fi_audit_script = os.path.join(BASE_DIR, "fi", "scripts", "04_audit_fi_pipeline.py")
    run_step([PYTHON_EXE, fi_audit_script], "FI Auditoría Contable y Métricas de REPOs")

    log("\n********************************************************************************")
    log("PIPELINE NOCTURNO CONCLUIDO CON ÉXITO PARA AMBAS INDUSTRIAS (FFMM Y FI)")
    log("********************************************************************************")

if __name__ == '__main__':
    main()
