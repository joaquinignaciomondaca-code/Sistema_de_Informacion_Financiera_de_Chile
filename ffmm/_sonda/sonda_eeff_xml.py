#!/usr/bin/env python3
"""SONDA TEMPORAL de investigación (se elimina de la rama al terminar; nunca va a main).

Pregunta: ¿se pueden obtener balance y estado de resultados de los fondos mutuos desde el XML IFRS
(«FMEF», Circular 1997) que la CMF publica en la ficha de cada fondo? La sonda NO publica nada: mide, desde
el runner de Actions (el sandbox de desarrollo no llega a cmfchile.cl), con una muestra fija:

  * ¿la ficha y el XML se descargan con un GET plano (sin sesión ni token)?
  * ¿cuántas fichas traen XML, cuántas dicen «No existe información»?
  * ¿el XML se lee (codificación, estructura)? ¿qué códigos de cuenta trae y cuáles no están en el modelo?
  * ¿cuadra: activos = pasivos + activo neto, y las sumas de las partes con sus totales del estado de resultados?
  * ¿coincide el ejercicio anterior de un archivo con el ejercicio actual del archivo del año previo?
  * tiempos, tamaños, moneda funcional, generador del XML.

Resultado: anotaciones `::notice` (JSON compacto) + out/resultados.json. Siempre termina con código 0.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BASE = "https://www.cmfchile.cl/institucional"
FICHA = (BASE + "/mercados/entidad.php?mercado=V&rut={run}&grupo=&tipoentidad=RGFMU&row=&vig=VI"
         "&control=svs&pestania=3&mm=12&aa={aa}&tipo_norma=IFRS")
XML = (BASE + "/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo={arch}&&rut={run}&&periodo={per}"
       "&&path=/web/ifrs_xml/fmifr/xml/&&desc_archivo=Estados_financieros_")
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)"}
TOL = 2  # miles: redondeo de cada cuenta al informarla

ESF_ACTIVOS = ["EfectivoYEfectivoEquivalente", "ActivosFinancierosAValorRazonableConEfectoEnResultados",
               "ActivosFinancierosAValorRazonableConEfectoEnResultadosEntregadosEnGarantia",
               "ActivosFinancierosACostoAmortizado", "CuentasPorCobrarAIntermediarios", "OtrasCuentasPorCobrar",
               "OtrosActivos"]
ESF_PASIVOS = ["PasivosFinancierosAValorRazonableConEfectoEnResultados", "CuentasPorAPagarIntermediarios",
               "RescatesPorPagar", "RemuneracionesSociedadAdministradora", "OtrosDocumentosYCuentasPorPagar",
               "OtrosPasivos"]
ESF_TOTALES = ["TotalActivo", "TotalPasivo", "ActivoNetoAtribuibleALosParticipes"]
ERI_INGRESOS = ["InteresesYReajustes", "IngresosPorDividendos",
                "DiferenciasDeCambioNetasSobreActivosFinancierosACostoAmortizado",
                "DiferenciasDeCambioNetasSobreEfectivoYEfectivoEquivalente",
                "CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados",
                "ResultadoEnVentaDeInstrumentosFinancieros", "OtrosEri"]          # el modelo de 2011 decía «Otros»
ERI_GASTOS = ["ComisionDeAdministracion", "HonorariosPorCustodiaYAdministracion", "CostosDeTransaccion",
              "OtrosGastosDeOperacion"]
ERI_TOTALES = ["TotalIngresosPerdidasNetosDeLaOperacion", "TotalGastosDeOperacion",
               "UtilidadPerdidaDeLaOperacionAntesDeImpuesto", "ImpuestosALasGananciasPorInversionesEnElExterior",
               "UtilidadPerdidaDeLaOperacionDespuesDeImpuesto", "DistribucionDeBeneficios",
               "AumentoDisminucionDeActivoNetoAtribuibleAParticipesOriginadasPorActividadesDeLaOperacionAntesDeDistribucionDeBeneficios",
               "AumentoDisminucionDeActivoNetoAtribuibleAParticipesOriginadasPorActividadesDeLaOperacionDespuesDeDistribucionDeBeneficios"]
ANTES = ERI_TOTALES[6]
DESPUES = ERI_TOTALES[7]
CONOCIDOS = set(ESF_ACTIVOS + ESF_PASIVOS + ESF_TOTALES + ERI_INGRESOS + ERI_GASTOS + ERI_TOTALES + ["Otros"])
CONTROLES = {("8011", 2025): {"TotalActivo": 192872200, "TotalPasivo": 26925,
                              "ActivoNetoAtribuibleALosParticipes": 192845275,
                              "UtilidadPerdidaDeLaOperacionAntesDeImpuesto": 8689720},
             ("8001", 2012): {"TotalActivo": 5582795, "TotalPasivo": 73499,
                              "ActivoNetoAtribuibleALosParticipes": 5509296,
                              "UtilidadPerdidaDeLaOperacionAntesDeImpuesto": 2487}}


def get(url: str, intentos: int = 3) -> tuple[bytes | None, float, str]:
    """GET plano. Devuelve (cuerpo|None, segundos, estado). Reintenta solo errores transitorios."""
    t0, estado = time.time(), "?"
    time.sleep(0.1)  # cortesía con la CMF: 4 hilos × 10 peticiones/s como máximo
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read(), time.time() - t0, f"http{r.status}"
        except urllib.error.HTTPError as e:
            estado = f"http{e.code}"
            if e.code < 500 and e.code != 429:
                break
        except Exception as e:  # noqa: BLE001 - la sonda debe sobrevivir a todo
            estado = f"{type(e).__name__}"
        time.sleep(2 * (i + 1))
    return None, time.time() - t0, estado


def leer_xml(raw: bytes) -> tuple[ET.Element | None, str]:
    try:
        return ET.fromstring(raw), "ok"
    except (ET.ParseError, LookupError, ValueError) as e:  # LookupError: encoding="iso-8011-K" (RUN pegado)
        err = f"{type(e).__name__}:{e}"
    try:  # declaración inválida: se descarta y el cuerpo se relee como latin-1
        txt = re.sub(rb"^\s*<\?xml[^>]*\?>", b"", raw).decode("latin-1")
        return ET.fromstring(txt), "ok_sin_declaracion (" + err[:70] + ")"
    except Exception as e:  # noqa: BLE001
        return None, f"{err[:80]} | reintento: {type(e).__name__}:{str(e)[:60]}"


def num(txt: str | None):
    s = (txt or "").strip()
    try:
        return int(s)
    except ValueError:
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None


def extraer(raiz: ET.Element) -> dict:
    d = {"cuentas": defaultdict(dict), "series": set(), "no_numericos": 0, "no_enteros": 0, "codigos": Counter()}
    ident, per = raiz.find("Identificacion"), raiz.find("DatosPeriodo")
    g = lambda nodo, tag: (nodo.findtext(tag) or "").strip() if nodo is not None else ""  # noqa: E731
    d["moneda"] = g(per, "MonedaPresentacionEstadosFinancieros")
    d["mes"], d["anio"] = (per.findtext("PeriodoPresentacionEstadosFinancieros/Mes") or "").strip() if per is not None else "", \
        (per.findtext("PeriodoPresentacionEstadosFinancieros/Anio") or "").strip() if per is not None else ""
    d["flags"] = "".join(g(per, t) or "?" for t in ("EstadoSituacionFinanciera", "EstadoResultadosIntegrales",
                                                      "EstadoCambiosActivoNetoAtribuibleParticipes",
                                                      "EstadoFlujoEfectivoMetodoDirecto",
                                                      "EstadoFlujoEfectivoMetodoIndirecto"))
    d["ultima_nota"] = g(per, "NumUltimaNotaInformada")
    d["run_xml"] = g(ident, "RUTFondoInforma") + "-" + g(ident, "DVFondoInforma")
    for c in raiz.findall("Cuenta"):
        cod, ctx, serie = c.get("CodigoCuenta", ""), c.get("Context", ""), c.get("Serie")
        v = num(c.text)
        d["codigos"][cod] += 1
        if v is None:
            d["no_numericos"] += 1
            continue
        if isinstance(v, float) and v != int(v):
            d["no_enteros"] += 1
        if serie:
            d["series"].add(serie)
        else:
            d["cuentas"][ctx][cod] = v
    return d


def chequeos(cuentas: dict) -> dict:
    """Devuelve {nombre: (ok, delta)} para un contexto; omite lo que no se puede evaluar."""
    s = lambda lst: sum(cuentas.get(k, 0) for k in lst)  # noqa: E731
    out, c = {}, cuentas
    if "TotalActivo" in c:
        out["esf_suma_activos"] = (abs(s(ESF_ACTIVOS) - c["TotalActivo"]) <= TOL, s(ESF_ACTIVOS) - c["TotalActivo"])
    if "TotalPasivo" in c:
        out["esf_suma_pasivos"] = (abs(s(ESF_PASIVOS) - c["TotalPasivo"]) <= TOL, s(ESF_PASIVOS) - c["TotalPasivo"])
    if all(k in c for k in ESF_TOTALES):
        dlt = c["TotalActivo"] - c["TotalPasivo"] - c["ActivoNetoAtribuibleALosParticipes"]
        out["esf_activo=pasivo+neto"] = (abs(dlt) <= TOL, dlt)
    if "TotalIngresosPerdidasNetosDeLaOperacion" in c:
        dlt = s(ERI_INGRESOS) - c["TotalIngresosPerdidasNetosDeLaOperacion"]
        out["eri_suma_ingresos"] = (abs(dlt) <= TOL, dlt)
    if "TotalGastosDeOperacion" in c:
        dlt = s(ERI_GASTOS) - c["TotalGastosDeOperacion"]
        out["eri_suma_gastos"] = (abs(dlt) <= TOL, dlt)
    if all(k in c for k in ERI_TOTALES[:3]):
        dlt = c[ERI_TOTALES[0]] + c[ERI_TOTALES[1]] - c[ERI_TOTALES[2]]
        out["eri_ingresos+gastos=utilidad"] = (abs(dlt) <= TOL, dlt)
    if all(k in c for k in (ERI_TOTALES[2], ERI_TOTALES[3], ERI_TOTALES[4])):
        dlt = c[ERI_TOTALES[2]] + c[ERI_TOTALES[3]] - c[ERI_TOTALES[4]]
        out["eri_utilidad+impuesto=despues"] = (abs(dlt) <= TOL, dlt)
    if ERI_TOTALES[4] in c and ANTES in c:
        dlt = c[ERI_TOTALES[4]] - c[ANTES]
        out["eri_utilidad=aumento_antes"] = (abs(dlt) <= TOL, dlt)
    if all(k in c for k in (ANTES, "DistribucionDeBeneficios", DESPUES)):
        dlt = c[ANTES] + c["DistribucionDeBeneficios"] - c[DESPUES]
        out["eri_aumento+distrib=despues"] = (abs(dlt) <= TOL, dlt)
    return out


def procesar(item: dict) -> dict:
    run, aa = item["run"], item["anio"]
    r = {"run": run, "anio": aa, "grupo": item["grupo"]}
    cuerpo, seg, est = get(FICHA.format(run=run, aa=aa))
    r["t_ficha"], r["est_ficha"] = round(seg, 2), est
    if cuerpo is None:
        r["clase"] = "ficha_error"
        return r
    html = cuerpo.decode("latin-1", errors="replace")
    if "No existe información de la entidad" in html:
        r["clase"] = "sin_informacion"
        return r
    m = re.search(r"ifrs_xml_verarchivo\.php\?archivo=(FMEF[A-Za-z0-9_\-]+\.xml)", html)
    r["pdf_notas"] = bool(re.search(r"archivo=FMNO\d+", html))
    r["pdf_dictamen"] = bool(re.search(r"archivo=FMDA\d+", html))
    r["pdf_declaracion"] = bool(re.search(r"archivo=FMDR\d+", html))
    if not m:
        r["clase"] = "ficha_sin_enlace_xml"
        r["muestra_html"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[-240:]
        return r
    arch = m.group(1)
    r["archivo"] = arch
    mt = re.search(r"_(\d{8})_(\d{6})_", arch)
    r["subido"] = f"{mt.group(1)} {mt.group(2)}" if mt else ""
    raw, seg, est = get(XML.format(arch=arch, run=run, per=f"{aa}12"))
    r["t_xml"], r["est_xml"] = round(seg, 2), est
    if raw is None:
        r["clase"] = "xml_error_descarga"
        return r
    r["bytes"] = len(raw)
    gen = re.search(rb"Generado por ([^<>\-]{2,60}?)\s*(?:-|<)", raw[:600])
    r["generador"] = gen.group(1).decode("latin-1").strip() if gen else "(sin comentario)"
    r["decl"] = (re.match(rb"\s*<\?xml[^>]*encoding=[\"']([^\"']+)", raw) or [None, b"?"])[1].decode("ascii", "replace") \
        if re.match(rb"\s*<\?xml", raw) else "(sin declaración)"
    raiz, est_parse = leer_xml(raw)
    r["parse"] = est_parse
    if raiz is None:
        r["clase"] = "xml_ilegible"
        r["muestra_xml"] = raw[:160].decode("latin-1", "replace")
        return r
    d = extraer(raiz)
    r.update(moneda=d["moneda"], flags=d["flags"], ultima_nota=d["ultima_nota"], n_series=len(d["series"]),
             mes=d["mes"], anio_xml=d["anio"], no_numericos=d["no_numericos"], no_enteros=d["no_enteros"],
             n_cuentas=sum(d["codigos"].values()), codigos=dict(d["codigos"]),
             run_en_xml=d["run_xml"])
    r["clase"] = "xml_ok"
    r["actual"] = d["cuentas"].get("PeriodoActual", {})
    r["anterior"] = d["cuentas"].get("PeriodoAnterior", {})
    r["chk_actual"] = {k: [bool(ok), dl] for k, (ok, dl) in chequeos(r["actual"]).items()}
    r["chk_anterior"] = {k: [bool(ok), dl] for k, (ok, dl) in chequeos(r["anterior"]).items()}
    esperado = CONTROLES.get((run, aa))
    if esperado:
        r["control_html"] = {k: [r["actual"].get(k), v, r["actual"].get(k) == v] for k, v in esperado.items()}
    return r


def seguro(item: dict) -> dict:
    try:
        return procesar(item)
    except Exception as e:  # noqa: BLE001
        return {"run": item["run"], "anio": item["anio"], "grupo": item["grupo"], "clase": "error_inesperado",
                "t_ficha": 0, "est_ficha": "?", "error": repr(e)[:200]}


def pct(a, b):
    return f"{a}/{b}" + (f" ({100 * a / b:.1f}%)" if b else "")


def resumir(filas: list[dict]) -> dict:
    R = {"fichas": len(filas), "por_clase": dict(Counter(f["clase"] for f in filas))}
    R["estado_http_ficha"] = dict(Counter(f["est_ficha"] for f in filas))
    R["estado_http_xml"] = dict(Counter(f.get("est_xml") for f in filas if "est_xml" in f))
    por_anio = defaultdict(Counter)
    for f in filas:
        por_anio[f["anio"]][f["clase"]] += 1
    R["clase_por_anio"] = {a: dict(c) for a, c in sorted(por_anio.items())}
    ok = [f for f in filas if f["clase"] == "xml_ok"]
    tf = [f["t_ficha"] for f in filas]
    tx = [f["t_xml"] for f in filas if "t_xml" in f]
    pq = lambda xs, q: round(sorted(xs)[min(len(xs) - 1, int(q * len(xs)))], 2) if xs else None  # noqa: E731
    R["tiempos_s"] = {"ficha_p50": pq(tf, .5), "ficha_p95": pq(tf, .95), "xml_p50": pq(tx, .5), "xml_p95": pq(tx, .95)}
    bs = [f["bytes"] for f in filas if "bytes" in f]
    if bs:
        R["bytes_xml"] = {"min": min(bs), "p50": int(statistics.median(bs)), "max": max(bs), "suma": sum(bs)}
    R["enlaces_pdf"] = {k: sum(1 for f in filas if f.get(k)) for k in ("pdf_notas", "pdf_dictamen", "pdf_declaracion")}
    R["generadores"] = dict(Counter(f.get("generador") for f in ok).most_common(8))
    R["declaracion_xml"] = dict(Counter(f.get("decl") for f in filas if "decl" in f))
    R["declaraciones_anomalas"] = [[f["run"], f["anio"], f["decl"]] for f in filas
                                   if "decl" in f and f["decl"].lower() not in ("iso-8859-1", "utf-8")][:15]
    R["errores_inesperados"] = [[f["run"], f["anio"], f.get("error")] for f in filas if f["clase"] == "error_inesperado"][:6]
    R["parse"] = dict(Counter(f.get("parse", "")[:40] for f in filas if "parse" in f))
    R["moneda"] = dict(Counter(f["moneda"] for f in ok))
    R["flags_ESF_ERI_ECAN_EFEdir_EFEind"] = dict(Counter(f["flags"] for f in ok).most_common(6))
    R["mes_distinto_de_12"] = sum(1 for f in ok if f["mes"] != "12")
    R["anio_xml_distinto_del_pedido"] = [(f["run"], f["anio"], f["anio_xml"]) for f in ok if str(f["anio"]) != f["anio_xml"]][:10]
    R["run_xml_distinto"] = [(f["run"], f["run_en_xml"]) for f in ok if f["run_en_xml"].split("-")[0] != f["run"]][:10]
    R["series_por_fondo"] = {"min": min((f["n_series"] for f in ok), default=0),
                             "p50": int(statistics.median([f["n_series"] for f in ok])) if ok else 0,
                             "max": max((f["n_series"] for f in ok), default=0)}
    R["valores_no_numericos"] = sum(f["no_numericos"] for f in ok)
    R["valores_no_enteros"] = sum(f["no_enteros"] for f in ok)
    cod = Counter()
    for f in ok:
        for k, n in f["codigos"].items():
            cod[k] += 1
    R["codigos_en_n_archivos"] = {k: n for k, n in sorted(cod.items()) if k in CONOCIDOS}
    R["codigos_fuera_del_modelo_esf_eri"] = {k: n for k, n in sorted(cod.items())
                                              if k not in CONOCIDOS and "PorSerie" not in k}
    faltan = Counter()
    for f in ok:
        for k in ESF_ACTIVOS + ESF_PASIVOS + ESF_TOTALES + ERI_INGRESOS + ERI_GASTOS + ERI_TOTALES:
            if k not in f["actual"]:
                faltan[k] += 1
    R["cuentas_esf_eri_ausentes_en_actual"] = dict(faltan.most_common(12))
    R["otros_eri_variante"] = {"Otros": sum(1 for f in ok if "Otros" in f["actual"]),
                               "OtrosEri": sum(1 for f in ok if "OtrosEri" in f["actual"])}
    for ctx in ("chk_actual", "chk_anterior"):
        agg, malos = defaultdict(lambda: [0, 0]), []
        for f in ok:
            for k, (b, dl) in f[ctx].items():
                agg[k][0 if b else 1] += 1
                if not b and len(malos) < 14:
                    malos.append([f["run"], f["anio"], k, dl])
        R[ctx] = {k: f"ok {v[0]} / falla {v[1]}" for k, v in sorted(agg.items())}
        R[ctx + "_ejemplos_falla"] = malos
    # consistencia entre archivos consecutivos: «anterior» de N frente a «actual» de N-1
    idx = {(f["run"], f["anio"]): f for f in ok}
    igual = difiere = 0
    ej = []
    for (run, aa), f in idx.items():
        p = idx.get((run, aa - 1))
        if not p:
            continue
        for k in ("TotalActivo", "TotalPasivo", "ActivoNetoAtribuibleALosParticipes",
                  "UtilidadPerdidaDeLaOperacionAntesDeImpuesto"):
            a, b = f["anterior"].get(k), p["actual"].get(k)
            if a is None or b is None:
                continue
            if a == b:
                igual += 1
            else:
                difiere += 1
                if len(ej) < 12:
                    ej.append([run, aa, k, a, b])
    R["consecutivos_anterior_vs_actual"] = {"iguales": igual, "difieren": difiere, "ejemplos_difieren": ej}
    R["controles_contra_html_ya_leido"] = {f"{f['run']}-{f['anio']}": f["control_html"] for f in filas if "control_html" in f}
    R["total_activo_cero"] = sum(1 for f in ok if f["actual"].get("TotalActivo") == 0)
    R["sin_enlace_xml_muestras"] = [f.get("muestra_html") for f in filas if f["clase"] == "ficha_sin_enlace_xml"][:3]
    R["xml_ilegible_muestras"] = [[f["run"], f["anio"], f.get("parse"), f.get("muestra_xml")] for f in filas
                                  if f["clase"] == "xml_ilegible"][:4]
    return R


def anotar(titulo: str, obj) -> None:
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)
    txt = txt.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    for i in range(0, len(txt), 28000):
        print(f"::notice title={titulo} {i // 28000 + 1}::{txt[i:i + 28000]}", flush=True)


def main() -> int:
    muestra = json.loads((AQUI / "muestra.json").read_text(encoding="utf-8"))
    limite = int(os.environ.get("SONDA_LIMITE", "0")) or len(muestra)
    muestra = muestra[:limite]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=int(os.environ.get("SONDA_HILOS", "4"))) as ex:
        filas = list(ex.map(seguro, muestra))
    seg = round(time.time() - t0, 1)
    out = AQUI / "out"
    out.mkdir(exist_ok=True)
    (out / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, default=str), encoding="utf-8")
    R = resumir(filas)
    R["duracion_total_s"] = seg
    R["peticiones_aprox"] = len(filas) + sum(1 for f in filas if "est_xml" in f)
    anotar("SONDA FFMM resumen", R)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        import traceback
        anotar("SONDA FFMM excepcion", {"error": repr(e), "traza": traceback.format_exc()[-1500:]})
        sys.exit(0)
