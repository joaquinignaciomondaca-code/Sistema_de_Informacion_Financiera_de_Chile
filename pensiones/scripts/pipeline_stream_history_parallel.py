"""
Pipeline de Descarga y Normalización Paralela en Streaming de la Historia Completa (SPensiones).
Restricción estricta de espacio en disco:
  - Descarga el archivo ZIP del periodo mensual en un archivo temporal.
  - Envía la tarea a un pool de procesos paralelos (ProcessPoolExecutor) para parseo de alta velocidad.
  - El proceso de parseo extrae los datos directamente desde el flujo ZIP en memoria.
  - Guarda las particiones mensuales normalizadas en Parquet (bonos_{YYYYMM}, acciones_{YYYYMM}, derivados_{YYYYMM}).
  - ELIMINA INMEDIATAMENTE el archivo ZIP en cuanto termina el parseo (cero acumulación en disco).
  - Incluye reintento automático y recuperación de conexión de red para ejecución 100% desatendida.
  - Auto-consolida cada 12 periodos y al finalizar todo el pipeline.
"""

import os
import glob
import json
import time
import calendar
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
import pandas as pd
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

BASE_DIR = _ROOT
PARTITIONS_DIR = BASE_DIR / "pensiones" / "outputs" / "partitions"
OUTPUT_DIR = BASE_DIR / "pensiones" / "outputs"
DOCS_OUTPUT_DIR = BASE_DIR / "docs" / "outputs" / "pensiones"
RAW_TEMP_DIR = BASE_DIR / "pensiones" / "raw"

PARTITIONS_DIR.mkdir(parents=True, exist_ok=True)
RAW_TEMP_DIR.mkdir(parents=True, exist_ok=True)
DOCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AFP_MAP = {
    '98000000-1': ('98.000.000-1', 'AFP Capital S.A.'),
    '76240079-0': ('76.240.079-0', 'AFP Cuprum S.A.'),
    '98000100-8': ('98.000.100-8', 'AFP Habitat S.A.'),
    '76762250-3': ('76.762.250-3', 'AFP Modelo S.A.'),
    '98001200-K': ('98.001.200-K', 'AFP Planvital S.A.'),
    '76265736-8': ('76.265.736-8', 'AFP ProVida S.A.'),
    '76960424-3': ('76.960.424-3', 'AFP Uno S.A.'),
}

def clean_rut(num_str, dv_str):
    num = str(num_str).strip().replace('.', '')
    dv = str(dv_str).strip().upper()
    raw = f"{num}-{dv}"
    if raw in AFP_MAP:
        return AFP_MAP[raw]
    if len(num) == 8:
        formatted = f"{num[:2]}.{num[2:5]}.{num[5:]}-{dv}"
    elif len(num) == 7:
        formatted = f"{num[:1]}.{num[1:4]}.{num[4:]}-{dv}"
    else:
        formatted = raw
    return formatted, f"AFP {num}"

def get_end_of_month(periodo_iso: str) -> str:
    parts = periodo_iso.split('-')
    year, month = int(parts[0]), int(parts[1])
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-{last_day:02d}"

def is_period_processed(periodo: str) -> bool:
    b_part = PARTITIONS_DIR / f"bonos_{periodo}.parquet"
    a_part = PARTITIONS_DIR / f"acciones_{periodo}.parquet"
    return b_part.exists() and a_part.exists()

def parse_and_cleanup_worker(zip_path: str, periodo: str):
    """
    Función de trabajador paralelo: parsea el ZIP y lo ELIMINA inmediatamente al terminar.
    """
    periodo_iso = f"{periodo[:4]}-{periodo[4:]}"
    fecha_corte = get_end_of_month(periodo_iso)
    
    bonos_rows = []
    acciones_rows = []
    derivados_rows = []
    
    t0 = time.time()
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            namelist = z.namelist()
            xml_files = [n for n in namelist if n.endswith('.xml')]
            if xml_files:
                xml_name = xml_files[0]
                with z.open(xml_name) as f:
                    context = ET.iterparse(f, events=('start', 'end'))
                    _, root = next(context)
                    
                    current_listado = None
                    for event, elem in context:
                        tag = elem.tag.split('}')[-1]
                        if event == 'start' and tag == 'listado':
                            current_listado = elem.attrib.get('numero')
                        elif event == 'end':
                            if tag == 'fila':
                                # 1. ACCIONES CHILENAS (Listado 12)
                                if current_listado == '12':
                                    nemotecnico = (elem.findtext('{http://www.spensiones.cl/xml}glosa') or '').strip()
                                    emisor = (elem.findtext('{http://www.spensiones.cl/xml}emisor') or nemotecnico).strip()
                                    tipo_accion = (elem.findtext('{http://www.spensiones.cl/xml}tipo_accion') or 'N').strip()
                                    
                                    if not nemotecnico.upper().startswith('TOTAL') and not emisor.upper().startswith('TOTAL'):
                                        total_node = elem.find('.//{http://www.spensiones.cl/xml}total')
                                        pct_emisor_val = 0.0
                                        if total_node is not None:
                                            pe_txt = total_node.findtext('{http://www.spensiones.cl/xml}porcentaje_sobre_emisor')
                                            if pe_txt:
                                                try:
                                                    pct_emisor_val = float(pe_txt)
                                                except ValueError:
                                                    pct_emisor_val = 0.0
                                                    
                                        cols = elem.find('{http://www.spensiones.cl/xml}columnas')
                                        if cols is not None:
                                            for afp in cols.findall('{http://www.spensiones.cl/xml}afp'):
                                                num = afp.findtext('.//{http://www.spensiones.cl/xml}numero')
                                                dv = afp.findtext('.//{http://www.spensiones.cl/xml}dv')
                                                monto_txt = afp.findtext('{http://www.spensiones.cl/xml}monto_dolares')
                                                if num and dv and monto_txt:
                                                    try:
                                                        monto_usd = float(monto_txt)
                                                        if monto_usd > 0:
                                                            rut_afp, nom_afp = clean_rut(num, dv)
                                                            acciones_rows.append({
                                                                'periodo': periodo_iso,
                                                                'fecha_corte': fecha_corte,
                                                                'rut_administradora': rut_afp,
                                                                'nombre_administradora': nom_afp,
                                                                'nemotecnico': nemotecnico,
                                                                'emisor': emisor,
                                                                'tipo_accion': 'Nacional' if tipo_accion == 'N' else 'Extranjera',
                                                                'monto_usd_millones': round(monto_usd, 4),
                                                                'pct_emisor': round(pct_emisor_val, 2),
                                                                'fuente': 'Superintendencia de Pensiones'
                                                            })
                                                    except ValueError:
                                                        pass

                                # 2. BONOS CORPORATIVOS (Listado 15)
                                elif current_listado == '15':
                                    emisor = (elem.findtext('{http://www.spensiones.cl/xml}glosa') or '').strip()
                                    nemotecnico = (elem.findtext('{http://www.spensiones.cl/xml}nemotecnico') or '').strip()
                                    if not nemotecnico:
                                        nemotecnico = emisor[:25]
                                        
                                    if not emisor.upper().startswith('TOTAL') and not nemotecnico.upper().startswith('TOTAL'):
                                        cols = elem.find('{http://www.spensiones.cl/xml}columnas')
                                        if cols is not None:
                                            for afp in cols.findall('{http://www.spensiones.cl/xml}afp'):
                                                num = afp.findtext('.//{http://www.spensiones.cl/xml}numero')
                                                dv = afp.findtext('.//{http://www.spensiones.cl/xml}dv')
                                                monto_txt = afp.findtext('{http://www.spensiones.cl/xml}monto_dolares')
                                                if num and dv and monto_txt:
                                                    try:
                                                        monto_usd = float(monto_txt)
                                                        if monto_usd > 0:
                                                            rut_afp, nom_afp = clean_rut(num, dv)
                                                            bonos_rows.append({
                                                                'periodo': periodo_iso,
                                                                'fecha_corte': fecha_corte,
                                                                'rut_administradora': rut_afp,
                                                                'nombre_administradora': nom_afp,
                                                                'tipo_instrumento': 'Bono Corporativo',
                                                                'nemotecnico': nemotecnico,
                                                                'emisor': emisor,
                                                                'monto_usd_millones': round(monto_usd, 4),
                                                                'fuente': 'Superintendencia de Pensiones'
                                                            })
                                                    except ValueError:
                                                        pass

                                # 3. BONOS ESTATALES (Listado 1)
                                elif current_listado == '1':
                                    glosa = (elem.findtext('{http://www.spensiones.cl/xml}glosa') or '').strip()
                                    if glosa and not glosa.upper().startswith('TOTAL'):
                                        tipo_inst = 'Bono Banco Central' if any(k in glosa for k in ['BC', 'PD']) else 'Bono Tesorería'
                                        emisor = 'BANCO CENTRAL DE CHILE' if tipo_inst == 'Bono Banco Central' else 'TESORERIA GENERAL DE LA REPUBLICA'
                                        total_node = elem.find('.//{http://www.spensiones.cl/xml}total')
                                        total_usd = 0.0
                                        total_pct = 0.0
                                        if total_node is not None:
                                            try:
                                                total_usd = float(total_node.findtext('{http://www.spensiones.cl/xml}monto_dolares') or 0)
                                                total_pct = float(total_node.findtext('{http://www.spensiones.cl/xml}porcentaje') or 0)
                                            except ValueError:
                                                pass
                                        
                                        cols = elem.find('{http://www.spensiones.cl/xml}columnas')
                                        if cols is not None and total_usd > 0:
                                            for afp in cols.findall('{http://www.spensiones.cl/xml}afp'):
                                                num = afp.findtext('.//{http://www.spensiones.cl/xml}numero')
                                                dv = afp.findtext('.//{http://www.spensiones.cl/xml}dv')
                                                pct_txt = afp.findtext('{http://www.spensiones.cl/xml}porcentaje')
                                                if num and dv and pct_txt:
                                                    try:
                                                        pct_afp = float(pct_txt)
                                                        if pct_afp > 0:
                                                            rut_afp, nom_afp = clean_rut(num, dv)
                                                            factor = (pct_afp / total_pct) if total_pct > 0 else (1.0 / 7.0)
                                                            monto_usd = total_usd * factor
                                                            bonos_rows.append({
                                                                'periodo': periodo_iso,
                                                                'fecha_corte': fecha_corte,
                                                                'rut_administradora': rut_afp,
                                                                'nombre_administradora': nom_afp,
                                                                'tipo_instrumento': tipo_inst,
                                                                'nemotecnico': glosa,
                                                                'emisor': emisor,
                                                                'monto_usd_millones': round(monto_usd, 4),
                                                                'fuente': 'Superintendencia de Pensiones'
                                                            })
                                                    except ValueError:
                                                        pass

                                # 4. DERIVADOS / SWAPS (Listado 26 y 28)
                                elif current_listado in ('26', '28'):
                                    contraparte = (elem.findtext('{http://www.spensiones.cl/xml}glosa') or '').strip()
                                    if contraparte.startswith('SWAP '):
                                        contraparte = contraparte.split(':')[-1].strip()
                                    elif contraparte.upper().startswith('TOTAL'):
                                        contraparte = ''
                                        
                                    unidad = (elem.findtext('{http://www.spensiones.cl/xml}unidad_indexada') or 'US$').strip()
                                    tipo_der = 'Swap Nacional de Tasas' if current_listado == '26' else 'Swap Extranjero de Tasas'
                                    
                                    if contraparte and not contraparte.upper().startswith('TOTAL'):
                                        cols = elem.find('{http://www.spensiones.cl/xml}columnas')
                                        if cols is not None:
                                            for afp in cols.findall('{http://www.spensiones.cl/xml}afp'):
                                                num = afp.findtext('.//{http://www.spensiones.cl/xml}numero')
                                                dv = afp.findtext('.//{http://www.spensiones.cl/xml}dv')
                                                monto_txt = afp.findtext('{http://www.spensiones.cl/xml}monto_dolares')
                                                if num and dv and monto_txt:
                                                    try:
                                                        monto_usd = float(monto_txt)
                                                        if monto_usd > 0:
                                                            rut_afp, nom_afp = clean_rut(num, dv)
                                                            derivados_rows.append({
                                                                'periodo': periodo_iso,
                                                                'fecha_corte': fecha_corte,
                                                                'rut_administradora': rut_afp,
                                                                'nombre_administradora': nom_afp,
                                                                'tipo_derivado': tipo_der,
                                                                'contraparte': contraparte,
                                                                'unidad_indexada': unidad,
                                                                'nocional_usd_millones': round(monto_usd, 4),
                                                                'fuente': 'Superintendencia de Pensiones'
                                                            })
                                                    except ValueError:
                                                        pass

                            elif tag == 'listado':
                                elem.clear()
                                root.clear()
                                if current_listado == '28':
                                    break
                                current_listado = None
    except Exception as e:
        print(f"Error procesando {zip_path}: {e}", flush=True)
    finally:
        # ELIMINAR EL ARCHIVO ZIP INMEDIATAMENTE TRAS PROCESAR
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception as e:
                print(f"Error eliminando {zip_path}: {e}", flush=True)

    # Guardar particiones en Parquet
    df_b = pd.DataFrame(bonos_rows)
    df_a = pd.DataFrame(acciones_rows)
    df_d = pd.DataFrame(derivados_rows)
    
    df_b.to_parquet(PARTITIONS_DIR / f"bonos_{periodo}.parquet", index=False)
    df_a.to_parquet(PARTITIONS_DIR / f"acciones_{periodo}.parquet", index=False)
    df_d.to_parquet(PARTITIONS_DIR / f"derivados_{periodo}.parquet", index=False)
    
    dt = time.time() - t0
    return periodo, len(df_b), len(df_a), len(df_d), dt

def download_period_zip(page, periodo: str) -> str:
    url = f"https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo={periodo}&ext=.php"
    temp_zip = RAW_TEMP_DIR / f"temp_{periodo}_{int(time.time()*1000)}.zip"
    
    for attempt in range(1, 4):
        try:
            page.goto(url, wait_until='networkidle', timeout=25000)
            
            link = page.locator("a:has-text('Obtener Aquí')").first
            if link.count() == 0:
                link = page.locator("a[href$='.zip']").first
                
            if link.count() == 0:
                print(f"[{periodo}] Intento {attempt}: No hay enlace de descarga ZIP.", flush=True)
                time.sleep(2.0)
                continue
                
            with page.expect_download(timeout=25000) as download_info:
                link.click()
            download = download_info.value
            download.save_as(str(temp_zip))
            return str(temp_zip)
        except Exception as e:
            print(f"[{periodo}] Intento {attempt}/3 error: {e}", flush=True)
            if temp_zip.exists():
                temp_zip.unlink(missing_ok=True)
            time.sleep(3.0 * attempt)
            
    return ""

def consolidate_partitions():
    print("\n--- CONSOLIDANDO TODAS LAS PARTICIONES MENSUALES ---", flush=True)
    bono_files = sorted(glob.glob(str(PARTITIONS_DIR / "bonos_*.parquet")))
    accion_files = sorted(glob.glob(str(PARTITIONS_DIR / "acciones_*.parquet")))
    derivado_files = sorted(glob.glob(str(PARTITIONS_DIR / "derivados_*.parquet")))
    
    print(f"Particiones encontradas: {len(bono_files)} meses de bonos, {len(accion_files)} de acciones, {len(derivado_files)} de derivados", flush=True)
    
    # 1. Bonos
    if bono_files:
        df_bonos = pd.concat([pd.read_parquet(f) for f in bono_files], ignore_index=True)
        if not df_bonos.empty:
            df_bonos = df_bonos.groupby(
                ['periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_instrumento', 'nemotecnico', 'emisor', 'fuente'],
                as_index=False
            )['monto_usd_millones'].sum()
            df_bonos['monto_usd_millones'] = df_bonos['monto_usd_millones'].round(4)
            df_bonos['id_posicion'] = df_bonos['periodo'] + "_" + df_bonos['rut_administradora'] + "_" + df_bonos['nemotecnico']
            cols_bonos = ['id_posicion', 'periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_instrumento', 'nemotecnico', 'emisor', 'monto_usd_millones', 'fuente']
            df_bonos = df_bonos[cols_bonos]
            df_bonos.to_parquet(OUTPUT_DIR / "afp_cartera_bonos.parquet", index=False)
            df_bonos.to_parquet(DOCS_OUTPUT_DIR / "afp_cartera_bonos.parquet", index=False)
            print(f"Bonos consolidados: {len(df_bonos):,} registros en afp_cartera_bonos.parquet", flush=True)
            
    # 2. Acciones
    if accion_files:
        df_acciones = pd.concat([pd.read_parquet(f) for f in accion_files], ignore_index=True)
        if not df_acciones.empty:
            df_acciones = df_acciones.groupby(
                ['periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'nemotecnico', 'emisor', 'tipo_accion', 'fuente'],
                as_index=False
            ).agg({'monto_usd_millones': 'sum', 'pct_emisor': 'max'})
            df_acciones['monto_usd_millones'] = df_acciones['monto_usd_millones'].round(4)
            df_acciones['id_posicion'] = df_acciones['periodo'] + "_" + df_acciones['rut_administradora'] + "_" + df_acciones['nemotecnico']
            cols_acciones = ['id_posicion', 'periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'nemotecnico', 'emisor', 'tipo_accion', 'monto_usd_millones', 'pct_emisor', 'fuente']
            df_acciones = df_acciones[cols_acciones]
            df_acciones.to_parquet(OUTPUT_DIR / "afp_cartera_acciones.parquet", index=False)
            df_acciones.to_parquet(DOCS_OUTPUT_DIR / "afp_cartera_acciones.parquet", index=False)
            print(f"Acciones consolidadas: {len(df_acciones):,} registros en afp_cartera_acciones.parquet", flush=True)

    # 3. Derivados
    if derivado_files:
        df_derivados = pd.concat([pd.read_parquet(f) for f in derivado_files], ignore_index=True)
        if not df_derivados.empty:
            df_derivados = df_derivados.groupby(
                ['periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_derivado', 'contraparte', 'unidad_indexada', 'fuente'],
                as_index=False
            )['nocional_usd_millones'].sum()
            df_derivados['nocional_usd_millones'] = df_derivados['nocional_usd_millones'].round(4)
            df_derivados['id_posicion'] = (
                df_derivados['periodo'] + "_" + 
                df_derivados['rut_administradora'] + "_" + 
                df_derivados.groupby(['periodo', 'rut_administradora']).cumcount().astype(str)
            )
            cols_derivados = ['id_posicion', 'periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_derivado', 'contraparte', 'unidad_indexada', 'nocional_usd_millones', 'fuente']
            df_derivados = df_derivados[cols_derivados]
            df_derivados.to_parquet(OUTPUT_DIR / "afp_derivados.parquet", index=False)
            df_derivados.to_parquet(DOCS_OUTPUT_DIR / "afp_derivados.parquet", index=False)
            df_derivados.to_parquet(DOCS_OUTPUT_DIR / "afp_derivados_swaps.parquet", index=False)
            print(f"Derivados consolidados: {len(df_derivados):,} registros en afp_derivados.parquet", flush=True)

def run_parallel_pipeline(limit=None):
    with open(BASE_DIR / "pensiones" / "scripts" / "all_periods.json", "r") as f:
        all_periods = json.load(f)
        
    periods_to_run = all_periods[:limit] if limit else all_periods
    pending_periods = [p for p in periods_to_run if not is_period_processed(p)]
    already_done = len(periods_to_run) - len(pending_periods)
    print(f"Total periodos: {len(periods_to_run)} (Ya procesados: {already_done}, Pendientes: {len(pending_periods)})", flush=True)
    
    if not pending_periods:
        print("Todos los periodos ya están procesados en particiones. Consolidando...", flush=True)
        consolidate_partitions()
        return

    executor = ProcessPoolExecutor(max_workers=5)
    futures = []
    t_start = time.time()
    batch_counter = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        for idx, per in enumerate(pending_periods):
            print(f"[{idx+1}/{len(pending_periods)}] Descargando {per}...", flush=True)
            try:
                zip_path = download_period_zip(page, per)
            except Exception as e:
                print(f"[{per}] Error crítico de sesión: {e}. Reiniciando contexto...", flush=True)
                try:
                    page.close()
                    context.close()
                    context = browser.new_context(accept_downloads=True)
                    page = context.new_page()
                    zip_path = download_period_zip(page, per)
                except Exception:
                    zip_path = ""
                    
            if zip_path and os.path.exists(zip_path):
                fut = executor.submit(parse_and_cleanup_worker, zip_path, per)
                futures.append(fut)
            else:
                print(f"[{per}] No se pudo descargar.", flush=True)
                
            batch_counter += 1
            if batch_counter >= 12:
                print("\n[Auto-Checkpoint] Consolidando particiones acumuladas...", flush=True)
                for f in futures:
                    if not f.done():
                        try:
                            f.result(timeout=60)
                        except Exception:
                            pass
                consolidate_partitions()
                futures = []
                batch_counter = 0

            # Control de flujo para no superar 5 archivos concurrentes en disco
            while len([f for f in futures if not f.done()]) >= 5:
                time.sleep(1.0)
                
            time.sleep(0.4)
            
        browser.close()
        
    print("\nDescargas completadas. Esperando finalización de parseo de las tareas restantes...", flush=True)
    for fut in as_completed(futures):
        try:
            res_periodo, nb, na, nd, dt = fut.result()
            print(f"[{res_periodo}] Finalizado en {dt:.1f}s -> {nb} bonos, {na} acciones, {nd} derivados | ZIP ELIMINADO.", flush=True)
        except Exception as e:
            print(f"Error en worker: {e}", flush=True)
            
    executor.shutdown(wait=True)
    print(f"\nPipeline paralelo finalizado en {time.time()-t_start:.1f} s", flush=True)
    consolidate_partitions()

if __name__ == "__main__":
    import sys
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_parallel_pipeline(limit=limit_val)
