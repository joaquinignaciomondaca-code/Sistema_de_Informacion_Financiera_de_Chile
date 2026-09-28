import zipfile
import xml.etree.ElementTree as ET
import time
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

zip_path = str(_ROOT.joinpath('pensiones', 'raw', 'cartera_desagregada202603.zip'))

t0 = time.time()
print(f"Abriendo {zip_path} directamente desde ZIP...")

records_acciones = 0
records_bonos = 0
records_swaps = 0

with zipfile.ZipFile(zip_path, 'r') as z:
    xml_name = z.namelist()[0]
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
                    if current_listado == '12': # Acciones
                        records_acciones += 1
                    elif current_listado in ('1', '15'): # Bonos
                        records_bonos += 1
                    elif current_listado in ('26', '28'): # Swaps
                        records_swaps += 1
                elif tag == 'listado':
                    elem.clear()
                    root.clear()
                    current_listado = None

dt = time.time() - t0
print(f"Completado en {dt:.2f} s")
print(f"Filas de Acciones (Listado 12): {records_acciones}")
print(f"Filas de Bonos (Listados 1, 15): {records_bonos}")
print(f"Filas de Swaps (Listados 26, 28): {records_swaps}")
