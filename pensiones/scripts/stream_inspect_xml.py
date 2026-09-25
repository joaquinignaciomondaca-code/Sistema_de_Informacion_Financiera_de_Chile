import xml.etree.ElementTree as ET

xml_file = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted\cartera_desagregada202603.xml"

# Usar iterparse para procesar de manera eficiente sin cargar los 277MB en RAM de golpe
import io
import sys

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

print("Analizando estructura XML con iterparse...")

tag_counts = {}
sample_records = {}

# Namespaces en el XML
# xmlns="http://www.spensiones.cl/xml"
context = ET.iterparse(xml_file, events=('start', 'end'))
_, root = next(context) # get root

depth = 0
current_path = []

for event, elem in context:
    # strip namespace
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    
    if event == 'start':
        current_path.append(tag)
        path_str = "/".join(current_path)
        tag_counts[path_str] = tag_counts.get(path_str, 0) + 1
        
        # Guardar sample si es un nodo de datos
        if len(current_path) >= 4 and path_str not in sample_records:
            sample_records[path_str] = {
                'attrib': elem.attrib,
                'text': (elem.text or '').strip()[:80]
            }
    elif event == 'end':
        current_path.pop()
        # Liberar memoria de los nodos hijos
        if len(current_path) <= 2:
            elem.clear()
            root.clear()
            
    # Limitar para no tardar minutos si hay millones de nodos
    if sum(tag_counts.values()) > 500000:
        print("Llegamos a 500,000 tags inspeccionados. Deteniendo muestreo.")
        break

print("\n--- ESTRUCTURA DE PATHS Y CONTEOS (TOP 40) ---")
for p, c in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:40]:
    sample = sample_records.get(p, '')
    print(f"{c:7d} | {p} | sample: {sample}")
