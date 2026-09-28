import zipfile
import xml.etree.ElementTree as ET
import os
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

zip_path = str(_ROOT.joinpath('pensiones', 'raw', 'cartera_desagregada202603.zip'))
extract_dir = str(_ROOT.joinpath('pensiones', 'raw', 'extracted'))
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as z:
    xml_filename = z.namelist()[0]
    print(f"Extrayendo {xml_filename}...")
    z.extract(xml_filename, extract_dir)
    extracted_file = os.path.join(extract_dir, xml_filename)
    print(f"Archivo XML extraido: {extracted_file}, tamano: {os.path.getsize(extracted_file):,} bytes")

# Leer primeras 100 líneas del XML
with open(extracted_file, 'r', encoding='latin-1', errors='replace') as f:
    print("\n--- PRIMERAS 60 LINEAS DEL XML ---")
    for i in range(60):
        line = f.readline()
        if not line:
            break
        print(line.rstrip())
