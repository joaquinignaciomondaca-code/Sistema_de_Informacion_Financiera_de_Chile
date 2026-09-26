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
    s = s.strip("()-").replace(".", "").replace(",", ".")
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
    m = re.search(etiqueta + r"\s*</div>\s*</td>\s*<td[^>]*derecha[^>]*>\s*<div[^>]*>([^<]+)</div>", html, re.I)
    if not m: return None
    v = parse_num(m.group(1))
    return None if v is None else v / 1000.0  # CMF publica en pesos → miles


def parse_fecu_gestora(html):
    """Extrae totales de la FECU IFRS (HTML CMF). Devuelve dict o None si no es una FECU."""
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
            "ganancia_perdida_ejercicio_m_clp": _celda(html, r"Ganancia\s+\(p[eé]rdida\)(?:\s+del\s+ejercicio|\s+atribuible[^<]*)?")}


def _fetch_gestora(args):
    op, sec, y, m, tc = args
    base = sec["cmf_url"].replace("pestania=1", "pestania=3")
    for tipo in ("I", "C"):
        url = f"{base}&mm={m}&aa={y}&tipo={tipo}&tipo_norma=IFRS"
        try:
            html = http_get(op, url, timeout=20).decode("iso-8859-1", errors="ignore")
        except Exception:
            continue
        d = parse_fecu_gestora(html)
        if d:
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
def meta_desde_texto(texto_inicial, etiqueta_web, rut_body, nombre):
    """Identifica el PS. Devuelve None si no se logra un código de emisión confiable (no se inventa)."""
    t = texto_inicial + " " + etiqueta_web
    m = re.search(r"PATRIMONIO\s+SEPARADO\s+(?:N[°º\.\s]*|NUMERO\s*)(\d+)", t, re.I)
    if m:
        codigo = f"PS-{int(m.group(1))}"
    else:
        m = re.search(r"PATRIMONIO\s+SEPARADO\s+([A-Z]{2,}[A-Z0-9]*(?:-[A-Z0-9]+)?)", texto_inicial, re.I)
        if not m or m.group(1).upper() in ("N", "NO", "TODOS", "DE", "DEL"):
            return None
        codigo = m.group(1).upper()
    m_reg = re.search(r"(?:REGISTRO(?:\s+DE\s+VALORES)?|INSCRIPCI[OÓ]N)[^\n\d]{0,40}N[°º\.]?\s*(\d+)", texto_inicial, re.I)
    return {"id_patrimonio": f"{rut_body}_{codigo.lower().replace('-', '_')}", "rut_administradora": rut_completo(rut_body),
            "nombre_administradora": nombre, "codigo_emision": codigo, "denominacion_ps": f"PATRIMONIO SEPARADO {codigo.replace('PS-', 'N°')}",
            "nro_registro_cmf": m_reg.group(1) if m_reg else None}


def _numeros_siguientes(lineas, i, n=2, saltar_nota=True):
    out = []
    for k, l in enumerate(lineas[i + 1:i + 9]):
        if saltar_nota and k == 0 and re.fullmatch(r"\d{1,2}", l):
            continue  # nº de nota inmediatamente después de la glosa del balance
        if re.fullmatch(r"\(?-?[\d\.]+(,\d+)?\)?|[—–-]", l):
            out.append(parse_num(l))
            if len(out) == n: break
        elif any(c.isalpha() for c in l):
            break
    return out


CATALOGO_PATH = os.path.join(BASE_DIR, "securitizadoras", "data", "catalogo_fecu_ps.json")
with open(CATALOGO_PATH, encoding="utf-8") as _f:
    CATALOGO = json.load(_f)
_POR_CODIGO = {c: e for e in CATALOGO["cuentas"] for c in e["codigos"]}
_POR_REGEX = [(e["estado"], re.compile(e["regex"]), e) for e in CATALOGO["cuentas"]]
_RX_CODIGO = re.compile(r"^\d{2}\.\d{3}$")
_RX_NUM = re.compile(r"^\(?-?[\d\.]+(,\d+)?\)?$|^[—–-]$")


def _norm(txt):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", t).strip()


def _mapear(estado, codigo, glosa):
    if codigo and codigo in _POR_CODIGO:
        return _POR_CODIGO[codigo]
    g = _norm(glosa)
    for est, rx, e in _POR_REGEX:
        if est == estado and rx.search(g):
            return e
    return None


def _estado_de_pagina(texto):
    cab = _norm(texto[:600])
    if any(k in cab for k in CATALOGO["estados"]["EXCEDENTES"]):
        return "EXCEDENTES"
    if "BALANCE" in cab or ("ACTIVOS" in cab and "PASIVOS" in cab) or re.search(r"\bACTIVOS\b|\bPASIVOS\b", cab):
        return "BALANCE"
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
        lineas = [l.strip() for l in t.split("\n") if l.strip()]
        if sum(1 for l in lineas if _RX_NUM.match(l) and any(ch.isdigit() for ch in l)) < 3 and not any(re.search(r"\d[\d\.]{3,}\s+\d", l) for l in lineas):
            continue
        codigo = None
        for i, l in enumerate(lineas):
            if _RX_CODIGO.match(l):
                codigo = l; continue
            # fila completa en una línea: "Disponible 5 119.969 15.615"  ó  "11.010 Disponible 119.969 15.615"
            m = re.match(r"^(\d{2}\.\d{3})?\s*([A-Za-zÁÉÍÓÚÑáéíóúñ](?:[^\d\(]|\([^)\d]*\))*?)\s+((?:\(?-?[\d\.]+(?:,\d+)?\)?|[—–-])(?:\s+(?:\(?-?[\d\.]+(?:,\d+)?\)?|[—–-]))*)\s*$", l)
            if m and len(m.group(2).strip()) > 3:
                cod = m.group(1) or codigo; glosa = m.group(2).strip(); toks = m.group(3).split()
                nota = None
                if len(toks) >= 2 and re.fullmatch(r"\d{1,2}", toks[0]):
                    nota, toks = toks[0], toks[1:]
                nums = [parse_num(x) for x in toks[:2]]
            elif any(ch.isalpha() for ch in l) and not _norm(l).startswith(("M$", "NOTA", "AL 31", "AL 30", "POR EL", "POR LOS", "EN MILES", "(EN MILES")):
                glosa = l; cod = codigo
                nums = _numeros_siguientes(lineas, i, 2, saltar_nota=True)
                nota = lineas[i + 1] if i + 1 < len(lineas) and re.fullmatch(r"\d{1,2}", lineas[i + 1]) and nums else None
                if not nums:
                    codigo = None; continue
            else:
                continue
            codigo = None
            if not nums or nums[0] is None and (len(nums) < 2 or nums[1] is None):
                continue
            e = _mapear(estado, cod, glosa)
            key = (estado, cod, _norm(glosa))
            if key in vistos:  # misma glosa repetida (p. ej. subtotal duplicado) → se conserva la primera
                continue
            vistos.add(key)
            lineas_out.append({"estado": estado, "pagina_pdf": pno + 1, "codigo_fecu": cod, "glosa": glosa, "nota": nota,
                               "monto_mclp": nums[0], "monto_anterior_mclp": nums[1] if len(nums) > 1 else None,
                               "cuenta_canonica": e["canonica"] if e else None, "seccion": e["seccion"] if e else None,
                               "es_total": bool(e and e.get("total"))})
    return lineas_out


def conciliar(lineas):
    """Aplica las conciliaciones del catálogo sobre monto_mclp. Devuelve dict nombre→bool|None (None si faltan cuentas)."""
    v = {l["cuenta_canonica"]: l["monto_mclp"] for l in lineas if l["cuenta_canonica"] and l["monto_mclp"] is not None}
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
    v = {l["cuenta_canonica"]: l["monto_mclp"] for l in lineas if l["cuenta_canonica"]}
    fila = {f"{k}_mclp": v.get(c) for k, c in _RESUMEN}
    conc = conciliar(lineas)
    fila["cuadre_contable_ok"] = bool(conc.get("activos_igual_pasivos"))
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
        if "patrimonios separados" not in tl or any(k in tl for k in ("analisis", "análisis", "declaraci", "responsabilidad")):
            continue
        a = tr.find("a", href=lambda h: h and "ver_sgd.php" in h and "bitacora" not in h)
        if a:
            out.append((txt, CMF + a["href"] if a["href"].startswith("/") else a["href"]))
    return url_ent, out


def paso_ps(op, secs, desde, hasta, trimestres):
    import fitz  # pymupdf
    print(f"[ps] EEFF PDF de patrimonios separados {desde}-{hasta}, trimestres {trimestres}")
    tc = tc_map(); lineas_all, balances, notas, cobertura = [], [], [], []
    hoy = datetime.now()
    for sec in secs.values():
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
                        paginas = [doc[i].get_text() for i in range(len(doc))]; doc.close()
                    except Exception as e:
                        cobertura.append({**cob, "estado": f"error_pdf:{e}"}); continue
                    if len(paginas) <= 1 or "Archivo No Disponible" in paginas[0]:
                        cobertura.append({**cob, "estado": "pdf_no_disponible"}); continue
                    if sum(len(pg) for pg in paginas[:4]) < 200:
                        cobertura.append({**cob, "estado": "pdf_sin_texto_(escaneado)"}); continue
                    meta = meta_desde_texto("\n".join(paginas[:5]), txt, sec["rut"], sec["razon_social"])
                    if not meta:
                        cobertura.append({**cob, "estado": "sin_codigo_emision"}); continue
                    prov = {"fuente_url": pdf_url, "metodo": metodo_tag("pdf_texto_pymupdf|catalogo_" + CATALOGO["version"]), "fecha_extraccion": ahora(),
                            "script_version": SCRIPT_VERSION, "pdf_sha256": hashlib.sha256(pdf).hexdigest()}
                    lin = parse_eeff_lineas(paginas)
                    for l in lin:
                        lineas_all.append({**meta, "periodo": periodo, **l, **prov})
                    if lin:
                        r = tc.get(periodo); fila = derivar_resumen(lin)
                        fila.update(meta); fila.update(prov); fila["periodo"] = periodo; fila["tipo_cambio_usd_clp"] = r
                        fila["total_activos_musd"] = round(fila["total_activos_mclp"] / r, 2) if r and fila["total_activos_mclp"] is not None else None
                        balances.append(fila)
                    efe, mor, desc = [], [], 0
                    if mm == "12":
                        efe = parse_nota_efectivo_ps(paginas); mor, desc = parse_nota_morosidad_ps(paginas)
                        for n in efe + mor:
                            notas.append({**meta, "periodo": periodo, **n, **prov})
                    cobertura.append({**cob, **{k: meta[k] for k in ("id_patrimonio", "codigo_emision")}, "estado": "ok" if lin else "sin_lineas_eeff",
                                      "lineas_eeff": len(lin), "cuentas_reconocidas": sum(1 for l in lin if l["cuenta_canonica"]),
                                      "partidas_efectivo": len(efe), "tramos_mora": len(mor), "tramos_mora_descartados": desc, **prov})
                    print(f"  {sec['razon_social'][:26]:26} {meta['codigo_emision']:10} {periodo}: lineas={len(lin)}")
    df_l = pd.DataFrame(lineas_all)
    guardar("patrimonios_separados_eeff_lineas", df_l, ["id_patrimonio", "periodo", "estado", "pagina_pdf"])
    df_b = pd.DataFrame(balances)
    if not df_b.empty:
        df_b = df_b.sort_values("cuentas_reconocidas", ascending=False).drop_duplicates(["id_patrimonio", "periodo"])
    guardar("patrimonios_separados_balance_resumen", df_b, ["id_patrimonio", "periodo"])
    guardar("patrimonios_separados_notas_detalle", notas, ["id_patrimonio", "periodo", "nota"])
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
