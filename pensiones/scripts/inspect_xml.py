import zipfile
import xml.etree.ElementTree as ET
import os

zip_path = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\cartera_desagregada202603.zip"
extract_dir = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted"
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
