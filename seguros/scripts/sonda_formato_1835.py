"""Sonda temporal: muestra el formato (largo de línea y tipo de registro) de cada archivo
de la cartera de inversiones de seguros (Circular 1835) para algunos meses."""
import collections, io, sys, urllib.request, zipfile

BASE = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
UA = {"User-Agent": "Mozilla/5.0"}

def get(url, t=180):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t) as r:
        return r.read()

for arg in sys.argv[1:]:
    ent, peri = arg.split(":")
    disp = get(f"{BASE}?tipoentidad={ent}&fnAjax=archi&peri={peri}", 30).decode("latin-1").strip()
    print(f"\n===== {ent} {peri}: archi={disp!r}")
    if disp != "1":
        continue
    data = get(f"{BASE}?tipoentidad={ent}&fnAjax=descarga&peri={peri}")
    print(f"bytes={len(data)} zip={data[:2] == b'PK'}")
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    print("archivos:", len(names), names[:2])
    cnt = collections.defaultdict(collections.Counter)
    ej = {}
    for n in names:
        L = z.open(n).read().decode("latin-1").splitlines()
        p = n.split("/")[-1][0].lower()
        if L:
            cnt[p][("H", len(L[0]))] += 1
        for l in L[1:]:
            cnt[p][(l[:1], len(l))] += 1
            if l[:1] == "2" and p in "ib" and (p, len(l)) not in ej:
                ej[(p, len(l))] = (n, L[0], l)
    for p, c in sorted(cnt.items()):
        print(p, c.most_common(6))
    for (p, ln), (n, h, l) in ej.items():
        if ln not in (930, 477):
            print(f"--- ejemplo {p} largo {ln} ({n})\n2: {l.rstrip()!r}")
