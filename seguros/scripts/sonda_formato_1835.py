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
        cuerpo = [l for l in L[1:] if l[:1] != "3"]
        # por compañía: encabezado, hasta 4 líneas de cada tipo de registro y el total
        vistos = collections.Counter(); sel = [L[0]]
        for l in cuerpo:
            if vistos[l[:1]] < 4:
                sel.append(l); vistos[l[:1]] += 1
        sel += [l for l in L[1:] if l[:1] == "3"][:1]
        por_tipo[p].append((n, sel))
    for p, arch in por_tipo.items():
        with open(f"{OUT}/{ent}_{peri}_{p}.txt", "w", encoding="latin-1") as f:
            for n, sel in arch[:12]:
                for l in sel:
                    f.write(f"{n}|{l}\n")
    print(arg, {p: len(a) for p, a in por_tipo.items()})
