"""Sonda temporal: registros públicos candidatos para las listas de entidades (se borra después)."""
import json, re, time, urllib.request
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).parent / "resultado"
OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)"}
C = "https://www.cmfchile.cl/institucional/mercados/"


def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except Exception as e:
            err = e
            time.sleep(4)
    return f"ERROR {err}".encode()


class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.rows, s.r, s.c, s.opts, s.links, s.o = [], None, None, [], [], None
    def handle_starttag(s, t, a):
        a = dict(a)
        if t == "tr": s.r = []
        elif t in ("td", "th") and s.r is not None: s.c = ""
        elif t == "option": s.o = [a.get("value"), ""]
        elif t == "a" and a.get("href"): s.links.append(a["href"])
    def handle_endtag(s, t):
        if t in ("td", "th") and s.c is not None and s.r is not None: s.r.append(" ".join(s.c.split())); s.c = None
        elif t == "tr" and s.r: s.rows.append(s.r); s.r = None
        elif t == "option" and s.o: s.opts.append(s.o); s.o = None
    def handle_data(s, d):
        if s.c is not None: s.c += d
        if s.o is not None: s.o[1] += d.strip()


res = {}
urls = {}
for pest in (18, 21, 22, 23, 24, 25, 33, 36):
    urls[f"ps_ef_p{pest}"] = C + f"entidad.php?mercado=V&rut=96971830&grupo=&tipoentidad=RGSEC&row=&vig=VI&control=svs&pestania={pest}"
urls["ps_volcom_p1"] = C + "entidad.php?mercado=V&rut=76965774&grupo=&tipoentidad=RGSEC&row=&vig=VI&control=svs&pestania=1"
res = {}
for k, u in urls.items():
    raw = get(u)
    txt = raw.decode("utf-8", errors="replace")
    p = P()
    try: p.feed(txt)
    except Exception: pass
    res[k] = {"url": u, "bytes": len(raw), "titulo": (re.search(r"<title>(.*?)</title>", txt, re.S | re.I) or [None, None])[1],
              "opciones": p.opts[:400], "filas": p.rows[:40], "texto": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", txt[txt.find("pestania=36"):]))[:3000], "n_filas": len(p.rows),
              "links": [l for l in p.links if any(x in l.lower() for x in ("pestania", "inscrip", "emision", "afp", "vcf", "entidad="))][:80],
              "inicio": txt[:300] if len(raw) < 2000 else ""}
(OUT / "sonda2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print({k: (v["bytes"], v["n_filas"], len(v["opciones"])) for k, v in res.items()})
