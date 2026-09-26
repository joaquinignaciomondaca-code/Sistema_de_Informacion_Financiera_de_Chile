#!/usr/bin/env python3
"""
Pipeline v2 — Sociedades Securitizadoras y Patrimonios Separados (CMF, Título XVIII Ley 18.045).

Reemplaza a `stream_cmf_securitizadoras.py` y `03_extract_patrimonios_separados_series.py` (retirados).
Principios: nada inventado (si un dato no se extrae queda NULL y se registra en cobertura), columnas de
procedencia en todas las tablas, TLS verificado, sin rutas locales ni credenciales.

Pasos (`--step`):
  maestro   → securitizadoras_maestro, patrimonios_separados_maestro           (HTML CMF)
  gestoras  → securitizadoras_balance_resumen                                   (FECU IFRS HTML CMF)
  ps        → patrimonios_separados_eeff_lineas (balance + excedentes línea a línea, trimestral),
              patrimonios_separados_balance_resumen (pivot de las líneas), patrimonios_separados_notas_detalle
              (sólo PDFs de diciembre), patrimonios_separados_cobertura        (EEFF PDF, pestaña 18)
  reparar-legacy → repara in-place las tablas ya publicadas (RUT con DV, procedencia, ceros→NULL) sin red
  todo      → maestro + gestoras + ps

Salida: docs/outputs/securitizadoras/*.parquet + *.json. Requiere: pandas, pyarrow, beautifulsoup4, pymupdf (paso ps).
Variables de entorno opcionales: MFC_CMF_INSECURE_TLS=1 (sólo si la cadena TLS de CMF falla en tu red; queda
registrado en la columna `metodo`). Rango del paso ps: --desde 2010 --hasta <año actual> --trimestres 03,06,09,12.
Catálogo de cuentas: securitizadoras/data/catalogo_fecu_ps.json (versionado).
"""
import os, re, sys, json, ssl, socket, hashlib, argparse, urllib.request, urllib.parse, http.cookiejar
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

SCRIPT_VERSION = "securitizadoras_pipeline_v2.0.0"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "securitizadoras")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")
CMF = "https://www.cmfchile.cl"
HEADERS = {"User-Agent": "Mozilla/5.0 (monitor-financiero-chile; pipeline securitizadoras v2)"}
socket.setdefaulttimeout(30)

# Catálogo cerrado de tramos de mora (los textos de los PDF se normalizan a estas claves; lo no reconocido se descarta
# y se contabiliza en cobertura).
TRAMOS_MORA = {
    "AL_DIA": r"^AL\s+D[IÍ]A", "1_30": r"^1\s*[-–—A]\s*3[01]\b", "31_60": r"^31\s*[-–—A]\s*60\b", "61_90": r"^61\s*[-–—A]\s*90\b",
    "91_120": r"^91\s*[-–—A]\s*120\b", "121_180": r"^121\s*[-–—A]\s*1[58]0\b", "MAS_180": r"^(\+|M[AÁ]S\s+DE|SOBRE)\s*180\b",
    "COBRANZA_JUDICIAL": r"JUDICIAL", "1_6_CUOTAS": r"^1\s*A\s*6\b", "7_36_CUOTAS": r"^7\s*A\s*36\b", "37_MAS_CUOTAS": r"^37\s*Y\s*M[AÁ]S",
    "TOTAL": r"^TOTAL(ES)?\b",
}


# ----------------------------------------------------------------------------- utilidades
def dv_m11(body):
    s, m = 0, 2
    for c in reversed(str(body)):
        s += int(c) * m; m = m + 1 if m < 7 else 2
    return {11: "0", 10: "K"}.get(11 - s % 11, str(11 - s % 11))


def rut_completo(body):
    body = re.sub(r"\D", "", str(body))
    return f"{body}-{dv_m11(body)}" if body else None


def ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ssl_context():
    ctx = ssl.create_default_context()
    if os.environ.get("MFC_CMF_INSECURE_TLS") == "1":
        ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    return ctx


def metodo_tag(base):
    return base + ("|tls_no_verificado" if os.environ.get("MFC_CMF_INSECURE_TLS") == "1" else "")


def opener():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                                       urllib.request.HTTPSHandler(context=ssl_context()))


def http_get(op, url, data=None, referer=None, timeout=30):
    h = dict(HEADERS)
    if referer: h["Referer"] = referer
    req = urllib.request.Request(url, data=data, headers=h)
    return op.open(req, timeout=timeout).read()


def tc_map():
    """Tipo de cambio USD/CLP por periodo YYYY-MM desde el parquet macro. Sin fallback: si falta, m_usd = NULL."""
    if not os.path.exists(MACRO_PARQUET):
        return {}
    df = pd.read_parquet(MACRO_PARQUET)
    col = "usd_clp_cierre" if "usd_clp_cierre" in df.columns else "usd_clp_promedio"
    return {str(p): float(v) for p, v in zip(df["periodo"], df[col]) if pd.notna(v) and v > 0}


def parse_num(txt):
    """'1.234.567' → 1234567.0 ; '(12,5)' → -12.5 ; '-' → None ; texto → None."""
    if txt is None: return None
    s = str(txt).strip().replace("$", "").replace("M", "").replace(" ", "")
    if s in ("", "-", "—", "–"): return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = s.strip("()-")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):  # miles con separador '.' o ',' (OCR mezcla ambos)
        s = s.replace(".", "").replace(",", "")
    else:
        s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def con_procedencia(rows, fuente_url, metodo, extra=None):
    for r in rows:
        r["fuente_url"] = fuente_url; r["metodo"] = metodo; r["fecha_extraccion"] = ahora(); r["script_version"] = SCRIPT_VERSION
        if extra: r.update(extra)
    return rows


def guardar(nombre, rows_or_df, orden=None, json_max_filas=60000):
    """Parquet siempre; JSON sólo si la tabla es chica (el JSON de tablas largas superaría los límites de GitHub)."""
    df = rows_or_df if isinstance(rows_or_df, pd.DataFrame) else pd.DataFrame(rows_or_df)
    if orden and not df.empty:
        df = df.sort_values(orden).reset_index(drop=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_parquet(os.path.join(OUT_DIR, f"{nombre}.parquet"), index=False)
    pj = os.path.join(OUT_DIR, f"{nombre}.json")
    if len(df) <= json_max_filas:
        df.to_json(pj, orient="records", indent=2, force_ascii=False)
    elif os.path.exists(pj):
        os.remove(pj)
    print(f"  guardado {nombre}: {len(df)} filas")
    return df


# ----------------------------------------------------------------------------- paso maestro
def paso_maestro(op):
    from bs4 import BeautifulSoup
    print("[maestro] sociedades securitizadoras (RGSEC)")
    url = f"{CMF}/institucional/mercados/consulta_busqueda.php?valor=" + urllib.parse.quote("securitizadora")
    soup = BeautifulSoup(http_get(op, url).decode("iso-8859-1", errors="ignore"), "html.parser")
    secs = {}
    for a in soup.find_all("a", href=True):
        if "tipoentidad=RGSEC" not in a["href"]: continue
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(a["href"]).query)
        rut = qs.get("rut", [""])[0]
        if rut and rut not in secs:
            secs[rut] = {"rut": rut, "dv": dv_m11(rut), "rut_completo": rut_completo(rut), "razon_social": a.get_text(strip=True),
                         "estado_vigencia": "VIGENTE" if qs.get("vig", [""])[0] == "VI" else "NO VIGENTE / EN LIQUIDACION",
                         "tipo_entidad_cmf": "RGSEC", "lineas_deuda_registradas": 0,
                         "cmf_url": f"{CMF}/institucional/mercados/{a['href']}"}
    print(f"  {len(secs)} securitizadoras")

    print("[maestro] líneas de títulos de deuda securitizados")
    url_t = f"{CMF}/institucional/estadisticas/listado_titulos_deuda.php"
    soup_t = BeautifulSoup(http_get(op, url_t).decode("iso-8859-1", errors="ignore"), "html.parser")
    lineas = []
    nombres = {v["razon_social"].upper(): k for k, v in secs.items()}
    for tr in soup_t.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(tds) < 8: continue
        emisor = tds[2]; rut_raw = re.sub(r"[^\dK-]", "", tds[4].upper())
        body = rut_raw.split("-")[0] if "-" in rut_raw else rut_raw[:-1]
        if body not in secs:
            body = next((k for n, k in nombres.items() if n in emisor.upper() or emisor.upper() in n), None)
        if not body or "SECURITI" not in (emisor.upper() + secs[body]["razon_social"].upper()):
            continue
        secs[body]["lineas_deuda_registradas"] += 1

        def fecha(s):
            m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", s.strip())
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
        lineas.append({"numero_inscripcion": tds[0], "fecha_inscripcion": fecha(tds[1]), "rut_administradora": rut_completo(body),
                       "razon_social_administradora": secs[body]["razon_social"], "denominacion_emision": f"Línea N° {tds[0]} - {emisor}",
                       "tipo_emision": tds[3], "moneda": tds[6], "monto_inscrito": parse_num(tds[5]), "fecha_vencimiento": fecha(tds[7])})
    guardar("securitizadoras_maestro", con_procedencia(list(secs.values()), url, metodo_tag("html_cmf_busqueda")), ["estado_vigencia", "razon_social"])
    guardar("patrimonios_separados_maestro", con_procedencia(lineas, url_t, metodo_tag("html_cmf_listado_titulos_deuda")), ["fecha_inscripcion", "numero_inscripcion"])
    return secs


# ----------------------------------------------------------------------------- paso gestoras
def _celda(html, etiqueta):
    """Valor de la primera columna (período actual) de la fila cuya glosa coincide. Estructura conocida del balance
    primero; si no, genérico: glosa seguida sólo de etiquetas/espacios hasta el primer número (excluye '[sinopsis]')."""
    m = re.search(etiqueta + r"\s*</div>\s*</td>\s*<td[^>]*derecha[^>]*>\s*<div[^>]*>([^<]+)</div>", html, re.I) or \
        re.search(etiqueta + r"\s*(?:<[^>]*>|\s)+?(\(?-?\d[\d\.]*\)?|-)\s*<", html, re.I)
    if not m: return None
    v = parse_num(m.group(1))
    return None if v is None else v / 1000.0  # CMF publica en pesos → miles


def parse_fecu_gestora(html):
    """Extrae totales de la FECU IFRS (HTML CMF). Devuelve dict o None si no es una FECU."""
    import html as _html
    html = _html.unescape(html).replace("\xa0", " ")  # CMF escribe 'p&eacute;rdida'
    if "[210000]" not in html and "[220000]" not in html:
        return None
    act = _celda(html, r"Total\s+de\s+activos"); pas = _celda(html, r"Total\s+de\s+pasivos")
    pat = _celda(html, r"Patrimonio\s+total") or _celda(html, r"Total\s+patrimonio")
    if act is None or pas is None:
        return None
    return {"total_activos_m_clp": act, "total_pasivos_m_clp": pas,
            "patrimonio_neto_m_clp": pat if pat is not None else round(act - pas, 6),
            "patrimonio_neto_es_derivado": pat is None,
            "efectivo_y_equivalentes_m_clp": _celda(html, r"Efectivo\s+y\s+equivalentes\s+al\s+efectivo"),
            "ganancia_perdida_ejercicio_m_clp": _celda(html, r"Ganancia\s+\(p[eé]rdida\)(?!\s*[\[,]|\s+(?:antes|procedente|acumulada|por|atribuible|que|de\s+actividades|bruta))")}


_FECU_DEBUG = []


def _fetch_gestora(args):
    op, sec, y, m, tc = args
    base = sec["cmf_url"].replace("pestania=1", "pestania=3")
    for tipo in ("I", "C"):
        url = f"{base}&mm={m}&aa={y}&tipo={tipo}&tipo_norma=IFRS"
        html = None
        for intento in range(2):  # CMF tarda en períodos antiguos: 60 s y un reintento
            try:
                html = http_get(op, url, timeout=60).decode("iso-8859-1", errors="ignore"); break
            except Exception:
                continue
        if html is None:
            continue
        d = parse_fecu_gestora(html)
        if d:
            dbg = os.environ.get("MFC_PS_DEBUG_DIR")
            if dbg and d.get("ganancia_perdida_ejercicio_m_clp") is None and len(_FECU_DEBUG) < 3:
                _FECU_DEBUG.append(url); os.makedirs(dbg, exist_ok=True)
                with open(os.path.join(dbg, f"fecu_{sec['rut']}_{y}{m}.html"), "w", encoding="utf-8") as fh: fh.write(html)
            d.update({"periodo": f"{y}-{m}", "año": int(y), "trimestre": (int(m) - 1) // 3 + 1, "rut": sec["rut_completo"],
                      "razon_social": sec["razon_social"], "estado_vigencia": sec["estado_vigencia"], "tipo_estado": tipo,
                      "tipo_cambio_usd_clp": tc})
            for k in ("total_activos", "total_pasivos", "patrimonio_neto"):
                d[f"{k}_m_usd"] = round(d[f"{k}_m_clp"] / tc, 6) if tc else None
            return con_procedencia([d], url, metodo_tag("html_fecu_ifrs_cmf"))[0]
    return None


def paso_gestoras(op, secs, desde=2014):
    print("[gestoras] balances IFRS trimestrales")
    tc = tc_map(); hoy = datetime.now()
    tareas = [(op, s, str(y), m, tc.get(f"{y}-{m}")) for s in secs.values() for y in range(desde, hoy.year + 1)
              for m in ("03", "06", "09", "12") if datetime(y, int(m), 1) <= hoy]
    rows = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for f in as_completed([ex.submit(_fetch_gestora, t) for t in tareas]):
            if f.result(): rows.append(f.result())
    guardar("securitizadoras_balance_resumen", rows, ["periodo", "razon_social"])


# ----------------------------------------------------------------------------- paso ps (PDF)
_ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}


_ORDINALES = {"UNO": 1, "PRIMER": 1, "PRIMERO": 1, "1ER": 1, "1RO": 1, "DOS": 2, "SEGUNDO": 2, "2DO": 2, "TRES": 3, "TERCER": 3, "TERCERO": 3, "CUATRO": 4, "CUARTO": 4}
_NO_SERIE = {"EEFF", "FECU", "ANEXO", "PAT", "SEP", "TRANSA", "FINAL", "ESTADO", "INFORME", "INF", "FIRMAD", "FIRMADP", "SEPRAD", "SEPRADOS",
             "ENERO", "FEBRER", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPT", "OCTUBR", "NOVIEM", "DICIEM", "JUN", "DIC", "MAR",
             "CHILE", "BICE", "PRIMER", "DOS", "TRES", "UNO", "MAE", "BCI", "NRO", "NUM", "NAO", "VERSIO", "CARTA", "TOTAL", "ANEXOS", "PLAN"}
_PREFIJOS_PS = ("PS", "P", "N", "NA", "NAO", "NO", "NRO", "NUM", "NUMERO")


def canonizar_codigo(txt):
    """Normaliza el nombre de un PS a un código estable. Busca primero un código de serie (`BSECS-9`, `BBICS-A`, `BTRA1-1`,
    `BVOLS 3`, `BSABN-ABH`, `VBOLS-A1`) y, si no hay, el primer número de 1-3 cifras (`PS12`, `Nº 8_0915`, `Patrimonio 5`,
    `201912 - Patrimonio Separado 5`, `PS 11 2`) o un ordinal/romano (`V`, `DOS`, `PRIMER`). Todo lo demás (razón social,
    meses, fechas pegadas, 'EEFF', 'FECU') se ignora porque nunca se consume. None si no queda nada identificable."""
    t = _norm(txt).replace("°", " ").replace("º", " ")
    t = re.sub(r"\bAL\s+\d{2}/\d{4}.*$", "", t); t = re.sub(r"\bDESCARGA\b.*$", "", t)
    t = re.sub(r"\s*-\s*", "-", t)  # 'BSECS -9', 'BTRA1- 1', 'BSABN - ABH'
    toks = [x.strip("-") for x in re.sub(r"[^A-Z0-9\-]+", " ", t).split() if x.strip("-")]
    # 1) código de serie: 3-6 letras + identificador pegado ('BTRA1-1', 'BVOLS3') o con guion ('BSECS-9', 'BBICS-A',
    #    'BSABN-ABH', 'VBOLS-A1'); también 'BSECS 9' / 'BVOLS 3' (sigla + número en el token siguiente)
    for k, tok in enumerate(toks):
        m = re.fullmatch(r"([A-Z]{3,6})(\d{1,3})(?:-([A-Z]?\d{1,3}|[A-Z]{1,4}))?", tok) or \
            re.fullmatch(r"([A-Z]{3,6})-([A-Z]?\d{1,3}|[A-Z]{1,4})(?:-(\d{1,3}))?", tok)
        if m and m.group(1) not in _NO_SERIE:
            return "-".join(g for g in m.groups() if g)
        if re.fullmatch(r"[A-Z]{4,6}", tok) and tok not in _NO_SERIE and re.search(r"[BCDFGHJKLMNPQRSTVWXZ]{2}", tok) \
                and k + 1 < len(toks) and re.fullmatch(r"\d{1,3}", toks[k + 1]):
            return f"{tok}-{int(toks[k + 1])}"
    # 2) número de PS: 'PS12', 'N12', 'P12' o el primer token de 1-3 dígitos (los de 4+ son fechas: 2011, 0915, 201912)
    for tok in toks:
        m = re.fullmatch(r"(?:%s)?-?(\d{1,3})" % "|".join(_PREFIJOS_PS), tok)
        if m:
            return f"PS-{int(m.group(1))}"
        if tok in _ORDINALES:
            return f"PS-{_ORDINALES[tok]}"
        if tok in _ROMANOS:
            return f"PS-{_ROMANOS[tok]}"
    # 3) serie sin identificador ('BVOLS' a secas, un solo PS): se acepta sólo si es una sigla de 4-6 letras que no es palabra común
    for tok in toks:
        if re.fullmatch(r"[A-Z]{4,6}", tok) and tok not in _NO_SERIE and re.search(r"[BCDFGHJKLMNPQRSTVWXZ]{2}", tok):
            return tok
    return None


def codigo_desde_etiqueta_web(etiqueta):
    """'Patrimonios Separados - BVOLS 3 al 12/2024' → 'BVOLS-3'. Quita el prefijo genérico de la fila web y canoniza."""
    t = _norm(etiqueta)
    t = re.sub(r"^.*?PATRIMONIOS\s+SEPARADOS\s*[-–:]?\s*", "", t, count=1)
    return canonizar_codigo(t)


_MESES = {"ENERO": "01", "FEBRERO": "02", "MARZO": "03", "ABRIL": "04", "MAYO": "05", "JUNIO": "06", "JULIO": "07", "AGOSTO": "08",
          "SEPTIEMBRE": "09", "OCTUBRE": "10", "NOVIEMBRE": "11", "DICIEMBRE": "12"}


def periodo_segun_pdf(paginas):
    """'YYYY-MM' más frecuente entre las fechas de cierre 'al 30 de junio de 2026' / '30.06.2026' / '30-06-2026' del inicio del PDF.
    Sirve para detectar PDFs mal archivados en la web CMF (p. ej. EEFF 2026 colgados en el período 06/2025)."""
    from collections import Counter
    c = Counter()
    for t in paginas[:8]:
        u = _norm(t)
        for d, m, a in re.findall(r"\bAL\s+(\d{1,2})\s+DE\s+([A-Z]+)\s+(?:DE\s+|DEL\s+)?(\d{4})", u):
            if m in _MESES and d in ("30", "31", "28", "29"):
                c[f"{a}-{_MESES[m]}"] += 1
        for d, m, a in re.findall(r"\b(3[01]|2[89])[\.\-/](0[369]|12)[\.\-/](20\d{2})\b", u):
            c[f"{a}-{m}"] += 1
    return c.most_common(1)[0][0] if c else None


def meta_desde_texto(texto_inicial, etiqueta_web, rut_body, nombre):
    """Identifica el PS: primero por la etiqueta oficial de la web CMF, luego por el texto del PDF. None si no hay código."""
    codigo = codigo_desde_etiqueta_web(etiqueta_web)
    if not codigo:
        m = re.search(r"PATRIMONIO\s+SEPARADO\s+((?:N[°º\*\?'’ro\.\s]*|NUMERO\s*)?\d+|[A-Z]{2,}[A-Z0-9]*(?:[\s-][A-Z0-9]+)?)", texto_inicial, re.I)
        codigo = canonizar_codigo(m.group(1)) if m else None
        if not codigo:
            return None
    m_reg = re.search(r"INSCRIPCI[OÓ]N\s+DE\s+LA\s+EMISI[OÓ]N\s+EN\s+EL\s+REGISTRO\s*:?\s*(\d+)", texto_inicial, re.I) or \
        re.search(r"(?:REGISTRO(?:\s+DE\s+VALORES)?|INSCRIPCI[OÓ]N)[^\n\d]{0,40}N[°º\.]?\s*(\d+)", texto_inicial, re.I)
    return {"id_patrimonio": f"{rut_body}_{codigo.lower().replace('-', '_')}", "rut_administradora": rut_completo(rut_body),
            "nombre_administradora": nombre, "codigo_emision": codigo, "denominacion_ps": f"PATRIMONIO SEPARADO {codigo.replace('PS-', 'N°')}",
            "nro_registro_cmf": m_reg.group(1) if m_reg else None}


def _numeros_siguientes(lineas, i, n=2, saltar_nota=True):
    out = []
    for k, l in enumerate(lineas[i + 1:i + 9]):
        if saltar_nota and k == 0 and re.fullmatch(r"\d{1,2}", l):
            continue  # nº de nota inmediatamente después de la glosa del balance
        toks = l.split()
        if any(re.fullmatch(r"\d{2}[\.\-/]\d{2}[\.\-/]\d{4}|\d{4}", x) for x in toks):
            break  # fila de fechas/años (encabezado de columnas), no montos
        if toks and all(re.fullmatch(r"\(?-?\d[\d\.,]*\)?|[—–-]", x) for x in toks):
            out.extend(parse_num(x) for x in toks)  # una celda por línea ó varias columnas en la misma línea ("5.762   5.750")
            if len(out) >= n: break
        elif any(c.isalpha() for c in l):
            break
    return out[:n]


CATALOGO_PATH = os.path.join(BASE_DIR, "securitizadoras", "data", "catalogo_fecu_ps.json")
with open(CATALOGO_PATH, encoding="utf-8") as _f:
    CATALOGO = json.load(_f)
_POR_CODIGO = {c: e for e in CATALOGO["cuentas"] for c in e["codigos"]}
_POR_REGEX = [(e["estado"], re.compile(e["regex"]), e) for e in CATALOGO["cuentas"]]
_RX_CODIGO = re.compile(r"^\d{2}\.\d{3}$")
_RX_IGNORAR = [re.compile(r) for r in CATALOGO.get("glosas_ignoradas", [])]
_RX_EXC = re.compile("|".join(re.escape(k) for k in CATALOGO["estados"]["EXCEDENTES"]) + r"|^INGRESOS(\s+OPERACIONALES)?$")
_RX_NUM = re.compile(r"^\(?-?\d[\d\.,]*\)?$|^[—–-]$")


def _norm(txt):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", t).strip()


_SECCIONES = [(k, re.compile(v)) for k, v in CATALOGO.get("secciones", {}).items()]
_POR_REGEX_SECCION = [(e["seccion"], re.compile(e["regex_seccion"]), e) for e in CATALOGO["cuentas"] if e.get("regex_seccion")]


def _sin_espacios(rx):
    """Versión del regex para glosas con letras espaciadas ('T OT A L A C T IVOS'): se quitan los espacios del patrón."""
    return re.compile(re.sub(r"\\s[+*]?|\\b| ", "", rx.pattern))


_POR_REGEX_SE = [(est, _sin_espacios(rx), e) for est, rx, e in _POR_REGEX]


def _espaciada(g):
    toks = g.split()
    return len(toks) >= 4 and sum(1 for t in toks if len(t) <= 2) >= len(toks) / 2


_EJEMPLOS = [  # (glosa canónica de ejemplo, cuenta) para glosas truncadas por el margen ("AL ACTIVOS") o erratas de OCR ("PATRIMINIO")
    ("TOTAL ACTIVOS CIRCULANTES", "TOTAL_ACTIVOS_CIRCULANTES"), ("TOTAL ACTIVO CIRCULANTE", "TOTAL_ACTIVOS_CIRCULANTES"),
    ("TOTAL OTROS ACTIVOS", "TOTAL_OTROS_ACTIVOS"), ("TOTAL ACTIVOS", "TOTAL_ACTIVOS"),
    ("TOTAL PASIVOS CIRCULANTES", "TOTAL_PASIVOS_CIRCULANTES"), ("TOTAL PASIVO CIRCULANTE", "TOTAL_PASIVOS_CIRCULANTES"),
    ("TOTAL PASIVOS LARGO PLAZO", "TOTAL_PASIVOS_LARGO_PLAZO"), ("TOTAL PASIVOS A LARGO PLAZO", "TOTAL_PASIVOS_LARGO_PLAZO"),
    ("TOTAL EXCEDENTES ACUMULADOS", "TOTAL_EXCEDENTES_ACUMULADOS"), ("TOTAL EXCEDENTE ACUMULADO", "TOTAL_EXCEDENTES_ACUMULADOS"), ("TOTAL PATRIMONIO", "TOTAL_EXCEDENTES_ACUMULADOS"),
    ("TOTAL PASIVOS", "TOTAL_PASIVOS_Y_PATRIMONIO"), ("TOTAL PASIVOS Y PATRIMONIO", "TOTAL_PASIVOS_Y_PATRIMONIO"),
    ("TOTAL PATRIMONIO NETO Y PASIVOS", "TOTAL_PASIVOS_Y_PATRIMONIO"), ("TOTAL PATRIMONIO Y PASIVOS", "TOTAL_PASIVOS_Y_PATRIMONIO"), ("TOTAL PASIVOS Y EXCEDENTES", "TOTAL_PASIVOS_Y_PATRIMONIO"),
    ("TOTAL INGRESOS", "TOTAL_INGRESOS"), ("TOTAL GASTOS", "TOTAL_GASTOS"), ("TOTAL DE GASTOS", "TOTAL_GASTOS"),
    ("ACTIVO SECURITIZADO (LARGO PLAZO)", "ACTIVO_SECURITIZADO_LP"), ("ACTIVO SECURITIZADO (CORTO PLAZO)", "ACTIVO_SECURITIZADO_CP"),
    ("MENOR VALOR EN COLOCACION TITULOS DE DEUDA", "MENOR_VALOR_COLOCACION"),
    ("OBLIGACIONES POR TITULOS DE DEUDA DE SECURITIZACION (CORTO PLAZO)", "OBLIG_TITULOS_DEUDA_CP"),
    ("OBLIGACIONES POR TITULOS DE DEUDA DE SECURITIZACION (LARGO PLAZO)", "OBLIG_TITULOS_DEUDA_LP"),
]
_POR_CANONICA = {e["canonica"]: e for e in CATALOGO["cuentas"]}


def _mapear_difuso(estado, g):
    import difflib
    if len(g) < 8:
        return None
    mejor, ratio = None, 0.0
    for ej, can in _EJEMPLOS:
        e = _POR_CANONICA.get(can)
        if not e or e["estado"] != estado:
            continue
        if ej.endswith(g) and len(g) >= 8 and not ej[:-len(g)].endswith(" "):  # truncada a mitad de palabra: "AL OTROS ACTIVOS" (no "PASIVOS Y PATRIMONIO")
            r = 0.99
        elif e.get("total") and not re.search(r"\bTOTA?L?E?S?\b|^T\s*O\s*T", g):
            continue  # un total exige que la glosa traiga (aunque sea truncado) la palabra TOTAL; un encabezado nunca es un total
        else:
            r = difflib.SequenceMatcher(None, ej, g).ratio()
        if r > ratio:
            mejor, ratio = e, r
    return mejor if ratio >= 0.86 else None


def _mapear(estado, codigo, glosa, seccion=None):
    """Prioridad: glosa (regex curada) → glosa dentro de la sección → código FECU impreso (los PDFs traen códigos
    repetidos o equivocados, p. ej. '15.210' en todas las filas o '23.000' delante de TOTAL PASIVOS)."""
    g = _norm(glosa)
    for est, rx, e in _POR_REGEX:
        if est == estado and rx.search(g):
            return e
    if seccion:  # glosa sin plazo explícito: se resuelve por la sección del balance en que aparece
        for sec, rx, e in _POR_REGEX_SECCION:
            if sec == seccion and rx.search(g):
                return e
    if _espaciada(g):
        gs = g.replace(" ", "")
        for est, rx, e in _POR_REGEX_SE:
            if est == estado and rx.search(gs):
                return e
    if codigo and codigo in _POR_CODIGO:
        return _POR_CODIGO[codigo]
    return _mapear_difuso(estado, g)


def _estado_de_pagina(texto):
    cab = _norm(texto[:600])
    if any(k in cab for k in CATALOGO["estados"]["EXCEDENTES"]):
        return "EXCEDENTES"
    if "BALANCE" in cab or ("ACTIVOS" in cab and "PASIVOS" in cab) or re.search(r"\bACTIVOS\b|\bPASIVOS\b", cab):
        return "BALANCE"
    # encabezado ilegible (OCR) o muy largo: se decide por el contenido de la página
    cuerpo = _norm(texto)
    if re.search(r"TOTAL\s+(DE\s+)?(ACTIVOS?|PASIVOS?)\b|\b(ACTIVOS?|PASIVOS?)\s+CIRCULANTES?\b", cuerpo):
        return "BALANCE"
    if re.search(r"TOTAL\s+(DE\s+)?(INGRESOS|GASTOS)\b", cuerpo):
        return "EXCEDENTES"
    return None


def parse_eeff_lineas(paginas, max_paginas=16):
    """Balance general y estado de excedentes línea a línea, tal como vienen en el PDF (texto pymupdf, una celda por
    línea o fila completa por línea). No inventa: glosas no reconocidas quedan con cuenta_canonica NULL.
    Devuelve lista de dicts: estado, codigo_fecu, glosa, nota, monto_mclp, monto_anterior_mclp, cuenta_canonica, seccion, es_total."""
    lineas_out, vistos = [], set()
    for pno, t in enumerate(paginas[:max_paginas]):
        cab = _norm(t[:400])
        if "INDICE" in cab or "CONTENIDO" in cab or "INFORME DEL AUDITOR" in cab or "NOTA N" in cab[:120]:
            continue
        estado = _estado_de_pagina(t)
        if not estado:
            continue
        if re.search(r"^[ \t]*NOTA[ \t]+\d+[ \t]*[-–\.:]", t, re.M | re.I) and not re.search(r"^[ \t]*(\d{2}\.\d{3}[ \t]+)?TOTAL[ \t]+(DE[ \t]+)?ACTIVOS[ \t]*$", t, re.M | re.I):
            continue  # página de notas (cuadros con 'Total de Activo', tramos de mora, etc.)
        lineas = [l.strip() for l in t.split("\n") if l.strip()]
        if sum(1 for l in lineas if _RX_NUM.match(l) and any(ch.isdigit() for ch in l)) < 3 and not any(re.search(r"\d[\d\.]{3,}\s+\d", l) for l in lineas) \
                and len(re.findall(r"\d{1,3}(?:\.\d{3})+", t)) < 3:
            continue
        codigo = None; pagina_out = []; seccion = None
        multicol = any(re.search(r"\$?\s*NO\s+REAJUSTABLES", _norm(l)) for l in lineas)
        limpias = []
        for l in lineas:
            l = re.sub(r"^[\|:;\.\-—–'\"´`»«_\s]+", "", l); l = re.sub(r"[\s;:,\|\]\}]+$", "", l)  # basura OCR en los bordes
            if not re.match(r"^\d{2}\.\d{3}\s", l):  # código FECU mal leído por OCR ("20. TOTAL PASIVOS", "13000 TOTAL…") → se descarta el código
                l = re.sub(r"^\d{1,2}[\.,]?\d{0,3}[\.,]?\s+(?=[A-Za-zÁÉÍÓÚÑáéíóúñ])", "", l)
            if not l:
                continue
            # dos estados lado a lado: "Disponible 318.363 17.408 Otros acreedores 411.563 429.899" → dos filas
            segs = re.findall(r"([A-Za-zÁÉÍÓÚÑáéíóúñ][^\d]*?)\s+((?:\(?-?[\d\.,]+\)?|[—–-])(?:\s+(?:\(?-?[\d\.,]+\)?|[—–-]))*)(?=\s+[A-Za-zÁÉÍÓÚÑáéíóúñ]|\s*$)", l)
            if len(segs) >= 2 and all(len(g.strip()) > 3 for g, _ in segs):
                limpias.extend(f"{g.strip()} {n}" for g, n in segs)
            else:
                limpias.append(l)
        lineas = limpias
        for i, l in enumerate(lineas):
            if _RX_CODIGO.match(l):
                codigo = l; continue
            ln = _norm(l)
            if _RX_EXC.search(ln) and not re.search(r"\d", ln):
                estado = "EXCEDENTES"  # el estado de excedentes puede venir en la misma página que el pasivo
            for sec, rx in _SECCIONES:
                if rx.fullmatch(ln):
                    seccion = sec
            if any(rx.fullmatch(ln) for rx in _RX_IGNORAR):
                codigo = None; continue
            # fila completa en una línea: "Disponible 5 119.969 15.615"  ó  "11.010 Disponible 119.969 15.615"
            m = re.match(r"^(\d{2}\.\d{3})?\s*([A-Za-zÁÉÍÓÚÑáéíóúñ](?:[^\d\(]|\([^)\d]*\))*?)\s+((?:\(?-?\d[\d\.,]*\)?|[—–-])(?:\s+(?:\(?-?\d[\d\.,]*\)?|[—–-]))*)\s*$", l)
            if m and len(m.group(2).strip()) > 3 and not re.search(r"\d{2}\.\d{2}\.\d{4}|\d{2}-\d{2}-\d{4}", m.group(3)):  # fechas ≠ montos
                cod = m.group(1) or codigo; glosa = m.group(2).strip(); toks = m.group(3).split()
                nota = None
                if re.fullmatch(r"\d{1,2}", toks[0]) and (len(toks) >= 2 or not _norm(glosa).startswith("TOTAL")):
                    nota, toks = toks[0], toks[1:]  # nº de nota (una cifra suelta de 1-2 dígitos sin monto = sólo la nota)
                nums = [parse_num(x) for x in toks[:4]]
            elif any(ch.isalpha() for ch in l) and not _norm(l).startswith(("M$", "NOTA", "AL 31", "AL 30", "POR EL", "POR LOS", "EN MILES", "(EN MILES")):
                glosa = l; cod = codigo
                mc = re.match(r"^(\d{2}\.\d{3})\s+(\S.*)$", l)  # '11.010 Disponible' (código y glosa en la misma línea)
                if mc:
                    cod, glosa = mc.group(1), mc.group(2).strip()
                nums = _numeros_siguientes(lineas, i, 4 if multicol else 2, saltar_nota=True)
                nota = lineas[i + 1] if i + 1 < len(lineas) and re.fullmatch(r"\d{1,2}", lineas[i + 1]) and nums else None
                if not nums:
                    codigo = None; continue
            else:
                continue
            codigo = None
            if not nums or nums[0] is None and (len(nums) < 2 or nums[1] is None):
                continue
            if any(rx.fullmatch(_norm(glosa)) for rx in _RX_IGNORAR):
                continue
            e = _mapear(estado, cod, glosa, seccion)
            key = (estado, seccion, cod, _norm(glosa))
            if key in vistos:  # misma glosa repetida (p. ej. subtotal duplicado) → se conserva la primera
                continue
            vistos.add(key)
            pagina_out.append({"estado": estado, "pagina_pdf": pno + 1, "codigo_fecu": cod, "glosa": glosa, "nota": nota,
                               "monto_mclp": nums[0], "monto_anterior_mclp": nums[1] if len(nums) > 1 else None,
                               "monto_col3": nums[2] if len(nums) > 2 else None, "monto_col4": nums[3] if len(nums) > 3 else None,
                               "layout_multicolumna": multicol, "seccion_balance": seccion,
                               "cuenta_canonica": e["canonica"] if e else None, "seccion": e["seccion"] if e else None,
                               "es_total": bool(e and e.get("total"))})
        # una página de estado financiero tiene al menos una línea de total reconocida; si no, es una nota u otra tabla
        if any(l["es_total"] for l in pagina_out):
            lineas_out.extend(pagina_out)
        else:
            for l in pagina_out: vistos.discard((l["estado"], l.get("seccion_balance"), l["codigo_fecu"], _norm(l["glosa"])))
    return lineas_out


def conciliar(lineas):
    """Aplica las conciliaciones del catálogo sobre monto_mclp. Devuelve dict nombre→bool|None (None si faltan cuentas)."""
    v = {}
    for l in lineas:
        if l["cuenta_canonica"] and l["monto_mclp"] is not None and l["cuenta_canonica"] not in v:
            v[l["cuenta_canonica"]] = l["monto_mclp"]
    out = {}
    for c in CATALOGO["conciliaciones"]:
        if not all(k in v for k in c["izq"] + c["der"]):
            out[c["nombre"]] = None; continue
        izq = sum(v[k] for k in c["izq"]); der = sum(v[k] for k in c["der"])
        out[c["nombre"]] = abs(izq - der) <= max(1.0, c["tolerancia_pct"] / 100 * abs(izq))
    return out


_RESUMEN = [("disponible", "DISPONIBLE"), ("valores_negociables", "VALORES_NEGOCIABLES"), ("activo_securitizado_corto_plazo", "ACTIVO_SECURITIZADO_CP"),
            ("provision_activo_securitizado", "PROVISION_ACTIVO_SECURITIZADO_CP"), ("otros_activos_circulantes", "OTROS_ACTIVOS_CIRCULANTES"),
            ("total_activo_circulante", "TOTAL_ACTIVOS_CIRCULANTES"), ("activo_securitizado_largo_plazo", "ACTIVO_SECURITIZADO_LP"),
            ("total_otros_activos", "TOTAL_OTROS_ACTIVOS"), ("total_activos", "TOTAL_ACTIVOS"), ("deuda_bonos_corto_plazo", "OBLIG_TITULOS_DEUDA_CP"),
            ("total_pasivo_circulante", "TOTAL_PASIVOS_CIRCULANTES"), ("deuda_bonos_largo_plazo", "OBLIG_TITULOS_DEUDA_LP"),
            ("total_pasivo_largo_plazo", "TOTAL_PASIVOS_LARGO_PLAZO"), ("excedentes_acumulados", "TOTAL_EXCEDENTES_ACUMULADOS"),
            ("total_pasivo_patrimonio", "TOTAL_PASIVOS_Y_PATRIMONIO"), ("excedente_neto_periodo", "EXCEDENTE_NETO_DEL_PERIODO")]


def derivar_resumen(lineas):
    v = {}
    for l in lineas:  # primera ocurrencia (orden del PDF): el balance va antes que cualquier cuadro de notas
        if l["cuenta_canonica"] and l["cuenta_canonica"] not in v:
            v[l["cuenta_canonica"]] = l["monto_mclp"]
    fila = {f"{k}_mclp": v.get(c) for k, c in _RESUMEN}
    conc = conciliar(lineas)
    fila["cuadre_contable_ok"] = bool(conc.get("activos_igual_pasivos"))
    fila["signo_total_pasivos_invertido"] = False
    fila["total_activos_impreso_mclp"] = v.get("TOTAL_ACTIVOS"); fila["total_pasivo_patrimonio_impreso_mclp"] = v.get("TOTAL_PASIVOS_Y_PATRIMONIO")
    fila["total_corregido_por_componentes"] = None
    A, Pt = v.get("TOTAL_ACTIVOS"), v.get("TOTAL_PASIVOS_Y_PATRIMONIO")
    if not fila["cuadre_contable_ok"] and A is not None and Pt is not None and abs(A + Pt) <= max(1.0, 0.001 * abs(A)) and conc.get("pasivos_igual_componentes"):
        fila["cuadre_contable_ok"] = True; fila["signo_total_pasivos_invertido"] = True  # el PDF imprime el total entre paréntesis
    if not fila["cuadre_contable_ok"]:
        # el total impreso falta o está mal leído/impreso, pero los subtotales de un lado igualan al total del otro lado:
        # se usa la suma de componentes (queda el impreso en *_impreso_mclp y el flag indica qué lado se corrigió)
        def _suma(ks):
            return sum(v[k] for k in ks) if all(k in v and v[k] is not None for k in ks) else None
        sA = _suma(["TOTAL_ACTIVOS_CIRCULANTES", "TOTAL_OTROS_ACTIVOS"])
        sP = _suma(["TOTAL_PASIVOS_CIRCULANTES", "TOTAL_PASIVOS_LARGO_PLAZO", "TOTAL_EXCEDENTES_ACUMULADOS"])
        def _eq(x, y): return x is not None and y is not None and abs(x - y) <= max(1.0, 0.001 * abs(y))
        if Pt is not None and sA is not None and _eq(sA, Pt) and not _eq(A, Pt):
            fila["total_activos_mclp"] = sA; fila["total_corregido_por_componentes"] = "activos"; fila["cuadre_contable_ok"] = True; A = sA
        elif A is not None and sP is not None and _eq(sP, A) and not _eq(Pt, A):
            fila["total_pasivo_patrimonio_mclp"] = sP; fila["total_corregido_por_componentes"] = "pasivo_patrimonio"; fila["cuadre_contable_ok"] = True; Pt = sP
        elif A is None and Pt is None and sA is not None and sP is not None and _eq(sA, sP):
            fila["total_activos_mclp"] = sA; fila["total_pasivo_patrimonio_mclp"] = sP; fila["total_corregido_por_componentes"] = "ambos"; fila["cuadre_contable_ok"] = True; A, Pt = sA, sP
    fila["conciliacion_componentes_ok"] = (conc.get("activos_igual_componentes") is not False) and (conc.get("pasivos_igual_componentes") is not False)
    fila["cuentas_reconocidas"] = sum(1 for l in lineas if l["cuenta_canonica"])
    fila["cuentas_no_reconocidas"] = sum(1 for l in lineas if not l["cuenta_canonica"])
    return fila


def parse_nota_efectivo_ps(paginas):
    rows, seen = [], set()
    for t in paginas[3:20]:
        up = t.upper()
        if not ("DISPONIBLE" in up or "EFECTIVO Y EQUIVALENTES" in up or "VALORES NEGOCIABLES" in up):
            continue
        m = re.search(r"NOTA\s*(\d+)[\.\s\-]+(DISPONIBLE|VALORES NEGOCIABLES|EFECTIVO Y EQUIVALENTES)", up)
        if not m:  # sin número de nota no publicamos la partida (no se inventa "Nota Disponible")
            continue
        nota = f"Nota {m.group(1)} - {m.group(2).title()}"
        lineas = [l.strip() for l in t.split("\n") if l.strip()]
        for i, l in enumerate(lineas):
            lu = l.upper()
            if any(k in lu for k in ("POR PAGAR", "PASIVO", "ACREEDOR", "HONORARIO", "RETENCI", "DEUDA", "NOTA", "BALANCE")):
                continue
            if not re.search(r"\b(BANCO|FONDOS?\s+MUTUOS?|DEP[OÓ]SITOS?\s+A\s+PLAZO|CAJA)\b", lu):
                continue
            nums = _numeros_siguientes(lineas, i, 1, saltar_nota=False)
            if not nums or nums[0] is None or nums[0] <= 0:
                continue
            key = (nota, l)
            if key in seen: continue
            seen.add(key)
            rows.append({"nota": nota, "concepto": re.sub(r"[\(\*].*?[\)\*]", "", l).strip(),
                         "tipo": "VALORES_NEGOCIABLES" if "VALORES" in nota.upper() else "DISPONIBLE", "monto_mclp": nums[0]})
    return rows


def parse_nota_morosidad_ps(paginas):
    rows, seen, descartados = [], set(), 0
    for t in paginas[3:22]:
        up = t.upper()
        if not ("EN MORA" in up or "TRAMOS DE MOROSIDAD" in up or "PROVISION DEL ACTIVO SECURITIZADO" in up or "PROVISIÓN DEL ACTIVO SECURITIZADO" in up):
            continue
        lineas = [l.strip() for l in t.split("\n") if l.strip()]
        for i, l in enumerate(lineas):
            lu = l.upper()
            tramo = next((k for k, rx in TRAMOS_MORA.items() if re.search(rx, lu)), None)
            if not tramo or "NOTA" in lu:
                continue
            nums = [n for n in _numeros_siguientes(lineas, i, 3, saltar_nota=False) if n is not None]
            if len(nums) < 2:
                continue
            deud = int(nums[0]) if len(nums) == 3 and nums[0] < 1_000_000 and float(nums[0]).is_integer() else None
            monto = nums[1] if deud is not None else nums[0]
            prov = nums[2] if deud is not None else nums[1]
            if monto is None or monto <= 0 or prov is None or abs(prov) > abs(monto):  # provisión > cartera = mala lectura
                descartados += 1; continue
            if tramo in seen: continue
            seen.add(tramo)
            rows.append({"nota": "Morosidad y provisiones", "tramo_mora": tramo, "numero_deudores": deud, "monto_mclp": monto,
                         "provision_mclp": abs(prov), "porcentaje_provision_pct": round(abs(prov) / monto * 100, 2)})
    return rows, descartados


def _listar_pdfs_ps(op, sec, anio, mm):
    """Devuelve [(etiqueta, url_pdf)] de la pestaña 18 para un período. Incluye no vigentes (vig=NV)."""
    from bs4 import BeautifulSoup
    vig = "VI" if sec["estado_vigencia"] == "VIGENTE" else "NV"
    url_ent = f"{CMF}/institucional/mercados/entidad.php?mercado=V&rut={sec['rut']}&tipoentidad=RGSEC&vig={vig}&control=svs&pestania=18"
    html = http_get(op, url_ent, data=urllib.parse.urlencode({"mm": mm, "aa": str(anio)}).encode()).decode("latin1", errors="ignore")
    out = []
    for tr in BeautifulSoup(html, "html.parser").find_all("tr"):
        txt = tr.get_text(" ", strip=True); tl = txt.lower()
        if "patrimonios separados" not in tl or any(k in tl for k in ("analisis", "análisis", "razonado", "declaraci", "responsabilidad", "auditor", "hechos relevantes", "carta", "anexo")):  # 'INFORME PATRIMONIO SEPARADO Nº1' (Santander 2010-11) sí es el EEFF
            continue
        a = tr.find("a", href=lambda h: h and "ver_sgd.php" in h and "bitacora" not in h)
        if a:
            out.append((txt, CMF + a["href"] if a["href"].startswith("/") else a["href"]))
    return url_ent, out


def _tesseract_disponible():
    import shutil
    return shutil.which("tesseract") is not None


def ocr_paginas_imagen(doc, paginas, max_paginas=16, dpi=300):
    """Páginas cuyo balance viene como imagen (texto < 300 caracteres pero con imágenes): se reemplaza su texto por el
    OCR de Tesseract (idioma spa, psm 6 = bloque uniforme). Devuelve (paginas, indices_ocr). Sin tesseract → sin cambios."""
    import subprocess, tempfile
    def _ilegible(t):  # fuente sin mapa Unicode: pymupdf devuelve caracteres de control
        return len(t) > 50 and sum(1 for ch in t if ord(ch) < 32 and ch not in "\n\t\r") > 0.2 * len(t)

    def _sin_cifras(t):  # página "sólo encabezado": casi sin cifras con separador de miles y poco texto
        return (len(re.findall(r"\d{1,3}(?:\.\d{3})+", t)) < 3 and len(t.strip()) < 1200) or _ilegible(t)
    def _tiene_grafico(pg):  # imagen incrustada o tabla dibujada con vectores (muchos trazos)
        try:
            return bool(pg.get_images()) or len(pg.get_drawings()) > 20
        except Exception:
            return bool(pg.get_images())
    idx = [i for i in range(min(len(paginas), max_paginas)) if _sin_cifras(paginas[i]) and _tiene_grafico(doc[i])]
    if not idx or not _tesseract_disponible():
        return paginas, []
    out = list(paginas); hechos = []
    try:
        import fitz
    except ImportError:
        fitz = None

    def _sin_lineas_tabla(png):  # borra los bordes de celdas (líneas largas) que tesseract confunde con dígitos: 'l', '|', '1'
        try:
            import cv2, numpy as np
        except ImportError:
            return False
        im = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
        if im is None:
            return False
        bw = cv2.adaptiveThreshold(~im, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
        h, w = bw.shape
        horiz = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(20, w // 40), 1)))
        vert = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, h // 40))))
        lineas = cv2.dilate(cv2.bitwise_or(horiz, vert), cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        limpio = cv2.bitwise_or(im, lineas)  # las líneas pasan a blanco
        cv2.imwrite(png, limpio)
        return True

    def _ocr(page, rot, psm="6", dpi_=None, binarizar=False, quitar_lineas=False):
        d = dpi_ or dpi
        mat = fitz.Matrix(d / 72, d / 72).prerotate(rot) if fitz is not None and hasattr(fitz, "Matrix") else None
        pix = page.get_pixmap(matrix=mat) if mat is not None else page.get_pixmap(dpi=d)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
            pix.save(fh.name); png = fh.name
        if binarizar:  # escaneos grises con bordes de tabla: escala de grises + umbral (Otsu) mejora mucho las cifras
            try:
                from PIL import Image
                im = Image.open(png).convert("L"); h = im.histogram(); tot = sum(h)
                # umbral de Otsu
                sumB = wB = 0; sum1 = sum(i * h[i] for i in range(256)); mejor, thr = 0.0, 128
                for t in range(256):
                    wB += h[t]
                    if wB == 0: continue
                    wF = tot - wB
                    if wF == 0: break
                    sumB += t * h[t]; mB = sumB / wB; mF = (sum1 - sumB) / wF; var = wB * wF * (mB - mF) ** 2
                    if var > mejor: mejor, thr = var, t
                im.point(lambda v, thr=thr: 255 if v > thr else 0).save(png)
            except Exception:
                pass
        if quitar_lineas:
            _sin_lineas_tabla(png)
        cmd = ["tesseract", png, "stdout", "-l", "spa", "--psm", psm, "-c", "preserve_interword_spaces=1"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        os.unlink(png)
        return r.stdout if r.returncode == 0 else ""

    _CLAVES = re.compile(r"\b(TOTAL|ACTIVOS?|PASIVOS?|CIRCULANTES?|PLAZO|OBLIGACIONES|EXCEDENTES?|PATRIMONIO|SEPARADO|SECURITIZAD[OA]S?|REMUNERACION(ES)?|"
                         r"PROVISION(ES)?|DISPONIBLE|DEUDA|TITULOS|INGRESOS|GASTOS|VALORES|NOTAS?|ESTADOS?|FINANCIEROS?|MILES|PESOS|POR|PAGAR|DEL|LOS|LAS|CON|PARA)\b")

    def _calidad(t):  # cifras con separador de miles + palabras castellanas reales (una página al revés da 'SOAISVd TVLOL', que no cuenta)
        return len(re.findall(r"\d{1,3}(?:[\.,]\d{3})+", t)) * 3 + len(_CLAVES.findall(_norm(t))) * 2

    for i in idx:
        try:
            txt = _ocr(doc[i], 0); mejor_rot = 0
            if _calidad(txt) < 40:  # página escaneada girada (apaisada o boca abajo): probar las otras orientaciones
                for rot in (90, 180, 270):
                    alt = _ocr(doc[i], rot)
                    if _calidad(alt) > _calidad(txt):
                        txt, mejor_rot = alt, rot
            def _filas(t):  # filas 'glosa + monto' (lo que el parser necesita): 'TOTAL ACTIVOS CIRCULANTES 707.967 1.004.403'
                return len(re.findall(r"^[^\n]*[A-Za-zÁÉÍÓÚÑáéíóúñ]{4,}[^\n]*?\s\(?-?\d{1,3}(?:[\.,]\d{3})+\)?(?:\s+\(?-?\d{1,3}(?:[\.,]\d{3})+\)?)?\s*$", t, re.M))
            # escaneos con celdas bordeadas: tesseract confunde los bordes con dígitos ('TOTAL ACTIVOS 2 or | too 03'); se prueba
            # siempre la variante sin líneas de tabla (400 dpi) y gana la lectura con más filas glosa+monto (empate: calidad)
            for psm, ql in (("6", True), ("4", True)):
                alt = _ocr(doc[i], mejor_rot, psm, 400, False, ql)
                if (_filas(alt), _calidad(alt)) > (_filas(txt), _calidad(txt)):
                    txt = alt
            if txt.strip():
                out[i] = ("" if _ilegible(paginas[i]) else paginas[i]) + "\n" + txt; hechos.append(i + 1)
        except Exception as e:  # OCR fallido en una página: se deja el texto original
            print(f"    ocr página {i + 1}: {e}")
    return out, hechos


def paso_ps(op, secs, desde, hasta, trimestres):
    import fitz  # pymupdf
    print(f"[ps] EEFF PDF de patrimonios separados {desde}-{hasta}, trimestres {trimestres}")
    tc = tc_map(); lineas_all, balances, notas, cobertura = [], [], [], []
    hoy = datetime.now()
    solo_ruts = {r.strip() for r in os.environ.get("MFC_PS_RUTS", "").split(",") if r.strip()}  # diagnóstico: sólo estas administradoras (cuerpo del RUT)
    debug_dir = os.environ.get("MFC_PS_DEBUG_DIR")  # diagnóstico: texto de las páginas de los PDFs que no cuadran
    if debug_dir: os.makedirs(debug_dir, exist_ok=True)
    for sec in secs.values():
        if solo_ruts and str(sec["rut"]) not in solo_ruts:
            continue
        for anio in range(desde, hasta + 1):
            for mm in trimestres:
                if datetime(anio, int(mm), 1) > hoy:
                    continue
                periodo = f"{anio}-{mm}"
                try:
                    url_ent, pdfs = _listar_pdfs_ps(op, sec, anio, mm)
                except Exception as e:
                    cobertura.append({"rut_administradora": sec["rut_completo"], "periodo": periodo, "estado": f"error_entidad:{e}"}); continue
                for txt, pdf_url in pdfs:
                    cob = {"rut_administradora": sec["rut_completo"], "nombre_administradora": sec["razon_social"], "periodo": periodo,
                           "etiqueta_web": txt[:120], "fuente_url": pdf_url}
                    try:
                        pdf = http_get(op, pdf_url, referer=url_ent, timeout=90)
                        doc = fitz.open(stream=pdf, filetype="pdf")
                        paginas = [doc[i].get_text() for i in range(len(doc))]
                        paginas, pags_ocr = ocr_paginas_imagen(doc, paginas); doc.close()
                    except Exception as e:
                        cobertura.append({**cob, "estado": f"error_pdf:{e}"}); continue
                    cob["paginas_ocr"] = ",".join(map(str, pags_ocr)) if pags_ocr else None
                    cob["periodo_segun_pdf"] = periodo_segun_pdf(paginas)
                    cob["periodo_inconsistente"] = bool(cob["periodo_segun_pdf"] and cob["periodo_segun_pdf"] != periodo)
                    if len(paginas) <= 1 or "Archivo No Disponible" in paginas[0]:
                        cobertura.append({**cob, "estado": "pdf_no_disponible"}); continue
                    if sum(len(pg) for pg in paginas[:4]) < 200:
                        cobertura.append({**cob, "estado": "pdf_sin_texto_(escaneado)"}); continue
                    meta = meta_desde_texto("\n".join(paginas[:5]), txt, sec["rut"], sec["razon_social"])
                    if not meta:
                        cobertura.append({**cob, "estado": "sin_codigo_emision"}); continue
                    prov = {"fuente_url": pdf_url, "metodo": metodo_tag(("pdf_texto_pymupdf+ocr_tesseract" if pags_ocr else "pdf_texto_pymupdf") + "|catalogo_" + CATALOGO["version"]), "fecha_extraccion": ahora(),
                            "script_version": SCRIPT_VERSION, "pdf_sha256": hashlib.sha256(pdf).hexdigest()}
                    lin = parse_eeff_lineas(paginas)
                    for l in lin:
                        lineas_all.append({**meta, "periodo": periodo, **l, **prov})
                    if lin:
                        r = tc.get(periodo); fila = derivar_resumen(lin)
                        fila.update(meta); fila.update(prov); fila["periodo"] = periodo; fila["tipo_cambio_usd_clp"] = r
                        fila["periodo_segun_pdf"] = cob["periodo_segun_pdf"]; fila["periodo_inconsistente"] = cob["periodo_inconsistente"]
                        fila["total_activos_musd"] = round(fila["total_activos_mclp"] / r, 2) if r and fila["total_activos_mclp"] is not None else None
                        balances.append(fila)
                    if debug_dir and (not lin or not fila.get("cuadre_contable_ok")):
                        with open(os.path.join(debug_dir, f"{meta['id_patrimonio']}_{periodo}.txt"), "w", encoding="utf-8") as fh:
                            fh.write(f"# {txt} | {pdf_url}\n")
                            for i, pg in enumerate(paginas[:16]):
                                fh.write(f"\n===== PAGINA {i + 1} =====\n{pg}")
                        if pags_ocr:  # imagen (100 dpi) de las páginas OCR para revisar a ojo cómo se ve el escaneo
                            try:
                                d2 = fitz.open(stream=pdf, filetype="pdf")
                                for i in pags_ocr[:3]:
                                    d2[i - 1].get_pixmap(dpi=100).save(os.path.join(debug_dir, f"{meta['id_patrimonio']}_{periodo}_p{i}.png"))
                                d2.close()
                            except Exception as e:
                                print(f"    debug png: {e}")
                    efe, mor, desc = [], [], 0
                    if mm == "12":
                        efe = parse_nota_efectivo_ps(paginas); mor, desc = parse_nota_morosidad_ps(paginas)
                        for n in efe + mor:
                            notas.append({**meta, "periodo": periodo, **n, **prov})
                    cobertura.append({**cob, **{k: meta[k] for k in ("id_patrimonio", "codigo_emision")}, "estado": "ok" if lin else ("documento_no_eeff" if re.search(r"ANALISIS\s+RAZONADO|INFORME\s+DE\s+(CARTERA|GESTION)|SUSTITUCION\s+DE\s+ACTIVOS", _norm(" ".join(paginas[:3]))) else "sin_lineas_eeff"),
                                      "lineas_eeff": len(lin), "cuentas_reconocidas": sum(1 for l in lin if l["cuenta_canonica"]),
                                      "partidas_efectivo": len(efe), "tramos_mora": len(mor), "tramos_mora_descartados": desc, **prov})
                    print(f"  {sec['razon_social'][:26]:26} {meta['codigo_emision']:10} {periodo}: lineas={len(lin)}")
    df_l = pd.DataFrame(lineas_all); df_b = pd.DataFrame(balances); df_n = pd.DataFrame(notas)
    if not df_b.empty:
        # el mismo PS+período puede venir en dos PDF (p. ej. 'BTRA1-1 INFORMACION FINANCIERA' y 'PATRIMONIO SEPARADO BTRA1-1'):
        # se conserva UN solo documento (el que cuadra y con más cuentas reconocidas) y sus líneas/notas, no una mezcla
        df_b = df_b.sort_values(["cuadre_contable_ok", "cuentas_reconocidas"], ascending=False).drop_duplicates(["id_patrimonio", "periodo"])
        ganadores = set(zip(df_b["id_patrimonio"], df_b["periodo"], df_b["fuente_url"]))
        for d in (df_l, df_n):
            if not d.empty:
                d.drop(d.index[[k not in ganadores for k in zip(d["id_patrimonio"], d["periodo"], d["fuente_url"])]], inplace=True)
    guardar("patrimonios_separados_eeff_lineas", df_l, ["id_patrimonio", "periodo", "estado", "pagina_pdf"])
    guardar("patrimonios_separados_balance_resumen", df_b, ["id_patrimonio", "periodo"])
    guardar("patrimonios_separados_notas_detalle", df_n, ["id_patrimonio", "periodo", "nota"])
    guardar("patrimonios_separados_cobertura", cobertura, ["rut_administradora", "periodo"])


# ----------------------------------------------------------------------------- reparar legacy (sin red)
def paso_reparar_legacy():
    """Repara determinísticamente las tablas v1 ya publicadas; se marca metodo='legacy_v1_*' hasta que se corra `todo`."""
    def leer(n):
        p = os.path.join(OUT_DIR, f"{n}.parquet")
        return pd.read_parquet(p) if os.path.exists(p) else None

    def marcar(df, metodo, url):
        if "metodo" in df.columns and df["metodo"].astype(str).str.startswith(SCRIPT_VERSION[:20]).all():
            return df
        for c, v in (("fuente_url", url), ("metodo", metodo), ("fecha_extraccion", ahora()), ("script_version", SCRIPT_VERSION + "|reparar-legacy")):
            if c not in df.columns: df[c] = v
        return df

    df = leer("securitizadoras_maestro")
    if df is not None:
        df["rut_completo"] = df["rut"].map(rut_completo); df["dv"] = df["rut"].map(dv_m11)
        guardar("securitizadoras_maestro", marcar(df, "legacy_v1_html_cmf_busqueda", f"{CMF}/institucional/mercados/consulta_busqueda.php?valor=securitizadora"))
    df = leer("securitizadoras_balance_resumen")
    if df is not None:
        df["rut"] = df["rut"].map(rut_completo)
        if "patrimonio_neto_es_derivado" not in df.columns: df["patrimonio_neto_es_derivado"] = True  # v1 lo calculaba A-P
        df.loc[df["ganancia_perdida_ejercicio_m_clp"] == 0, "ganancia_perdida_ejercicio_m_clp"] = None  # v1 no la capturaba
        guardar("securitizadoras_balance_resumen", marcar(df, "legacy_v1_html_fecu_ifrs_cmf", f"{CMF}/institucional/mercados/entidad.php?pestania=3"))
    df = leer("patrimonios_separados_maestro")
    if df is not None:
        df["rut_administradora"] = df["rut_administradora"].map(rut_completo)
        df = df.drop(columns=[c for c in ("clase_colateral_subyacente",) if c in df.columns])  # heurística por nombre, no dato CMF
        guardar("patrimonios_separados_maestro", marcar(df, "legacy_v1_html_cmf_listado_titulos_deuda", f"{CMF}/institucional/estadisticas/listado_titulos_deuda.php"))
    df = leer("patrimonios_separados_balance_resumen")
    if df is not None:
        df["rut_administradora"] = df["id_patrimonio"].str.split("_").str[0].map(rut_completo)
        # v1 igualaba activos a pasivos cuando faltaba uno, así que su flag no prueba nada. Se recalcula con
        # componentes: activos ≈ pasivo circulante + pasivo largo plazo + excedentes acumulados (±1 %).
        comp = df["total_pasivo_circulante_mclp"].fillna(0) + df["total_pasivo_largo_plazo_mclp"].fillna(0) + df["excedentes_acumulados_mclp"].fillna(0)
        df["cuadre_contable_ok"] = (comp != 0) & ((df["total_activos_mclp"] - comp).abs() <= 0.01 * df["total_activos_mclp"].abs())
        for c in ("disponible_musd", "total_activos_musd", "deuda_bonos_total_musd"):
            if c in df.columns: df[c] = None  # v1 usaba tipos de cambio hardcodeados
        guardar("patrimonios_separados_balance_resumen", marcar(df, "legacy_v1_pdf_pymupdf_con_defaults", f"{CMF}/institucional/mercados/entidad.php?pestania=18"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", choices=["maestro", "gestoras", "ps", "reparar-legacy", "todo"], default="todo")
    ap.add_argument("--desde", type=int, default=2010, help="primer año del paso ps (CMF publica desde 2000)")
    ap.add_argument("--hasta", type=int, default=datetime.now().year)
    ap.add_argument("--trimestres", default="03,06,09,12", help="meses de cierre a descargar, p. ej. 12 para sólo anuales")
    a = ap.parse_args()
    if a.step == "reparar-legacy":
        paso_reparar_legacy(); return
    op = opener()
    secs = paso_maestro(op)
    if a.step in ("gestoras", "todo"):
        paso_gestoras(op, secs)
    if a.step in ("ps", "todo"):
        paso_ps(op, secs, a.desde, a.hasta, [m.strip().zfill(2) for m in a.trimestres.split(",")])
    print("Listo. Ejecuta ahora: python securitizadoras/scripts/audit_patrimonios_separados_v2.py")


if __name__ == "__main__":
    main()
