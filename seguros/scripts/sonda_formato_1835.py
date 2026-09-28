"""Guarda una muestra chica de líneas reales de la cartera de inversiones de seguros
(Circular 1835) para fijar y probar el formato de cada archivo. Uso: CSVID:202608 ..."""
import collections, io, os, sys, urllib.request, zipfile

BASE = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
OUT = "seguros/fuentes/muestras_1835"
os.makedirs(OUT, exist_ok=True)

def get(url, t=180):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=t) as r:
        return r.read()

for arg in sys.argv[1:]:
    ent, peri = arg.split(":")
    z = zipfile.ZipFile(io.BytesIO(get(f"{BASE}?tipoentidad={ent}&fnAjax=descarga&peri={peri}")))
    por_tipo = collections.defaultdict(list)
    for n in sorted(z.namelist()):
        L = z.open(n).read().decode("latin-1").splitlines()
        p = n.split("/")[-1][0].lower()
        if not L or p not in "afxibpc":
            continue
        vistos = collections.Counter(); sel = [L[0]]
        for l in L[1:]:
            if vistos[l[:1]] < 3:
                sel.append(l); vistos[l[:1]] += 1
        por_tipo[p].append((n, sel))
    for p, arch in por_tipo.items():
        cuenta = collections.Counter()
        with open(f"{OUT}/{ent}_{peri}_{p}.txt", "w", encoding="latin-1") as f:
            for n, sel in arch:
                for l in sel:
                    t = "H" if l is sel[0] else l[:1]
                    if cuenta[t] < 40:
                        f.write(f"{n}|{l}\n"); cuenta[t] += 1
    print(arg, {p: len(a) for p, a in por_tipo.items()})
