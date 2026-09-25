import urllib.request
import json
from bs4 import BeautifulSoup

def test():
    url = "https://www.cmfchile.cl/institucional/estadisticas/seg_rgpsf_ajax.php?f=servFiltrosPLSQL&tipo=T&estado=TODO"
    data = b"tip_busqueda=T&rut_ENT=&nombre_ENT=&servicio_ENT="
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    })
    with urllib.request.urlopen(req) as resp:
        entities = json.loads(resp.read().decode("utf-8"))

    print(f"Total entidades descargadas del RPSF: {len(entities)}")
    
    # Probar 3 entidades para ver pestaña 1 y pestaña 111
    sample_ruts = [entities[0]["per_rut"], entities[1]["per_rut"], entities[2]["per_rut"]]
    for rut in sample_ruts:
        ent_url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=O&rut={rut}&tipoentidad=RGPSF&vig=VI&control=svs&pestania=1"
        req_ent = urllib.request.Request(ent_url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req_ent, timeout=10) as r:
                html = r.read().decode("iso-8859-1", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                data_dict = {}
                for tr in soup.find_all("tr"):
                    tds = [td.get_text().strip() for td in tr.find_all(["th", "td"])]
                    if len(tds) == 2:
                        data_dict[tds[0]] = tds[1]
                print(f"RUT {rut}: {data_dict.get('Raz\xf3n Social', '')} | Inscripcion: {data_dict.get('N\xfamerodeInscripci\xf3n', data_dict.get('N\xfamero de Inscripci\xf3n', ''))} | Fecha: {data_dict.get('Fecha de Inscripci\xf3n', '')}")
        except Exception as e:
            print(f"Error {rut}: {e}")

if __name__ == "__main__":
    test()
