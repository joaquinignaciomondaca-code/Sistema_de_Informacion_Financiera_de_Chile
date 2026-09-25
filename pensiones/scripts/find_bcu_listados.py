import zipfile
import xml.etree.ElementTree as ET

zip_path = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\cartera_desagregada202603.zip"

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open(z.namelist()[0]) as f:
        context = ET.iterparse(f, events=('start', 'end'))
        _, root = next(context)
        
        current_listado = None
        bcu_occurrences = []
        for event, elem in context:
            tag = elem.tag.split('}')[-1]
            if event == 'start' and tag == 'listado':
                current_listado = elem.attrib.get('numero')
            elif event == 'end':
                if tag == 'fila':
                    glosa = elem.find('{http://www.spensiones.cl/xml}glosa')
                    if glosa is not None and glosa.text == 'BCU':
                        cols = elem.find('{http://www.spensiones.cl/xml}columnas')
                        col_tags = [c.tag.split('}')[-1] for c in cols] if cols is not None else []
                        sub_tags = []
                        if cols is not None and len(cols) > 0:
                            sub_tags = [sc.tag.split('}')[-1] for sc in cols[0]]
                        bcu_occurrences.append((current_listado, col_tags[:3], sub_tags))
                elif tag == 'listado':
                    elem.clear()
                    root.clear()

print("Ocurrencias de BCU por Listado:")
for o in bcu_occurrences:
    print(f"Listado {o[0]}: columnas={o[1]}, subelementos primer hijo={o[2]}")
