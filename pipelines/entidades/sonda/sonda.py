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


import urllib.parse
def forms(txt):
    out=[]
    for m in re.finditer(r"<form\b(.*?)>(.*?)</form>", txt, re.S|re.I):
        attrs, body = m.group(1), m.group(2)
        if "<select" not in body.lower(): continue
        campos=[]
        for t in re.finditer(r"<(input|select)\b([^>]*)>", body, re.I):
            a=dict(re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', t.group(2)))
            campos.append([t.group(1).lower(), a.get("name"), a.get("value"), a.get("type")])
        out.append({"attrs": attrs.strip(), "campos": campos, "html": body[:3000]})
    return out
def titulo_tab(txt):
    t=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",txt))
    j=t.find("Raz&oacute;n Social:"); j = j if j>0 else t.find("Razón Social")
    return t[max(0,j-80):j+40]
base = C + "entidad.php?mercado=V&rut=96971830&grupo=&tipoentidad=RGSEC&row=&vig=VI&control=svs&pestania="
res = {}
raw = get(base+"18").decode("utf-8", errors="replace")
fs = forms(raw); res["p18_forms"] = fs
for f in fs:
    datos = {}
    for tipo, n, v, ty in f["campos"]:
        if not n: continue
        if tipo == "select":
            datos[n] = None
        elif (ty or "").lower() not in ("button","submit","reset") or v:
            datos[n] = v or ""
    sels = [n for tipo, n, v, ty in f["campos"] if tipo == "select" and n]
    for mes, ano in (("12","2025"), ("06","2025")):
        d = dict(datos)
        for n in sels:
            d[n] = mes if ("mm" in n.lower() or "mes" in n.lower()) else ano
        if len(sels)==2 and all(d[n]==d[sels[0]] for n in sels):
            d[sels[0]], d[sels[1]] = mes, ano
        am = re.search(r'action\s*=\s*["\']([^"\']*)', f["attrs"], re.I)
        act = urllib.parse.urljoin(base+"18", am.group(1).replace("&amp;","&")) if am and am.group(1) else base+"18"
        meth = (re.search(r'method\s*=\s*["\'](\w+)', f["attrs"], re.I) or [None,"get"])[1].lower()
        body = urllib.parse.urlencode({k:v for k,v in d.items() if v is not None})
        try:
            if meth=="post":
                req = urllib.request.Request(act, data=body.encode(), headers={**UA, "Content-Type":"application/x-www-form-urlencoded"})
            else:
                req = urllib.request.Request(act + ("&" if "?" in act else "?") + body, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r: t2 = r.read().decode("utf-8","replace")
        except Exception as e:
            t2 = f"ERROR {e}"
        p = P()
        try: p.feed(t2)
        except Exception: pass
        res[f"p18_{ano}{mes}"] = {"metodo": meth, "action": act, "body": body, "n_filas": len(p.rows), "filas": p.rows[:80],
                                 "links": [l for l in p.links if "pdf" in l.lower() or "inscrip" in l.lower() or "patrim" in l.lower()][:40]}
for pest in (37, 38, 43, 46, 47, 48, 49, 50, 100, 115):
    t = get(base+str(pest)).decode("utf-8", errors="replace")
    p = P()
    try: p.feed(t)
    except Exception: pass
    res[f"tab{pest}"] = {"titulo": titulo_tab(t), "n_filas": len(p.rows), "filas": p.rows[:25], "forms": [f["campos"] for f in forms(t)]}
(OUT / "sonda3.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print({k: v.get("n_filas") if isinstance(v, dict) else len(v) for k, v in res.items()})
