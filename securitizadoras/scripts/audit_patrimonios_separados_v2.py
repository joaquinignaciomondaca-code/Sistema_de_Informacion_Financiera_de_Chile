"""
Auditoría v2 — Securitizadoras y Patrimonios Separados (CMF).

Valida sustancia (no sólo forma): procedencia, claves, RUT, cuadre, placeholders, plausibilidad y
consistencia con la web. Exit 1 si hay FAIL.

Uso: python securitizadoras/scripts/audit_patrimonios_separados_v2.py [--json salida.json]   (PS_OUT_DIR=<dir> para otro directorio)
Dependencias: duckdb.
"""
import os, re, sys, json, glob, argparse

try:
    import duckdb
except ImportError:
    print("Falta duckdb: pip install duckdb"); sys.exit(2)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.environ.get("PS_OUT_DIR") or os.path.join(BASE_DIR, "docs", "outputs", "securitizadoras")  # PS_OUT_DIR permite auditar una rama de resultados
SCRIPTS_DIR = os.path.join(BASE_DIR, "securitizadoras", "scripts")
RESULTS = []


def report(check, status, detail, evidence=None):
    RESULTS.append({"check": check, "status": status, "detail": detail, "evidence": evidence})
    print(f"  [{status}] {check}: {detail}")
    for e in (evidence or [])[:8]:
        print(f"         - {e}")


def dv_m11(body):
    s, m = 0, 2
    for c in reversed(str(body)):
        s += int(c) * m; m = m + 1 if m < 7 else 2
    r = 11 - (s % 11)
    return {11: "0", 10: "K"}.get(r, str(r))


def rut_ok(v):
    v = str(v)
    if not re.fullmatch(r"\d{7,8}-[\dK]", v):
        return False
    b, d = v.split("-")
    return dv_m11(b) == d


def q(con, sql):
    return con.execute(sql).fetchall()


def cols_of(con, f):
    return [r[0] for r in q(con, f"describe select * from '{f}'")]


def tablas():
    return {os.path.basename(f)[:-8]: f for f in sorted(glob.glob(os.path.join(OUT_DIR, "*.parquet")))}


# --------------------------------------------------------------------------------------
def audit_codigo(T):
    print("\n[0] Código y reproducibilidad")
    scripts = [f for f in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")) if not os.path.basename(f).startswith("audit_")]
    src_all = ""
    for f in scripts:
        src_all += open(f, encoding="utf-8", errors="ignore").read()
    huerfanas = [t for t in T if t not in src_all]
    report("tablas_con_script_generador", "FAIL" if huerfanas else "PASS",
           f"{len(huerfanas)} de {len(T)} tablas publicadas no son mencionadas por ningún script del sector (irreproducibles)", huerfanas)
    hits = []
    for f in scripts:
        for i, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
            # `else 0.39`, `else 974.15`, `else 30`, `else "Cumple / SI"`: valor de negocio inventado cuando falta el dato
            if re.search(r"""else\s+(\d+\.\d+|[1-9]\d+|"[^"]*(Cumple|Banco Central|Soberana|Regulada)[^"]*")""", line) or re.search(r'"cumplimiento_calificacion":\s*"Cumple', line):
                hits.append(f"{os.path.basename(f)}:{i}: {line.strip()[:90]}")
    report("defaults_inventados_en_parser", "FAIL" if hits else "PASS",
           f"{len(hits)} líneas que rellenan con valores por defecto cuando no se pudo extraer", hits)
    tls = [os.path.basename(f) for f in scripts if "CERT_NONE" in (src := open(f, encoding="utf-8", errors="ignore").read()) and "MFC_CMF_INSECURE_TLS" not in src]
    report("tls_deshabilitado", "WARN" if tls else "PASS", f"{len(tls)} scripts con ssl.CERT_NONE incondicional (permitido sólo tras opt-in MFC_CMF_INSECURE_TLS)", tls)
    sec = [f"{os.path.basename(f)}" for f in scripts if re.search(r"""(PASS|Siete\()\w*\s*[=(]\s*['"]""", open(f, encoding="utf-8", errors="ignore").read())]
    report("secretos_en_codigo", "FAIL" if sec else "PASS", f"{len(sec)} scripts con credenciales", sec)


def audit_identidad(con, T):
    print("\n[1] Identidad: RUT, claves, períodos")
    bad_tables = []
    for t, f in T.items():
        c = cols_of(con, f)
        rc = next((x for x in ("rut_administradora", "rut_completo", "rut") if x in c), None)
        if not rc:
            continue
        vals = [r[0] for r in q(con, f"select distinct {rc} from '{f}'")]
        bad = [v for v in vals if not rut_ok(v)]
        if bad:
            bad_tables.append(f"{t}.{rc}: {len(bad)}/{len(vals)} inválidos, ej. {bad[:2]}")
    report("rut_valido_modulo11_con_dv", "FAIL" if bad_tables else "PASS",
           f"{len(bad_tables)} tablas con RUT inválidos o sin DV", bad_tables)

    fmt = {}
    for t, f in T.items():
        if "periodo" in cols_of(con, f):
            v = q(con, f"select periodo from '{f}' where periodo is not null limit 1")
            if v:
                fmt.setdefault(re.sub(r"\d", "9", str(v[0][0])), []).append(t)
    report("periodo_formato_unico", "PASS" if len(fmt) <= 1 else "FAIL",
           f"{len(fmt)} formatos de periodo en el sector: " + ", ".join(f"{k} ({len(v)} tablas)" for k, v in fmt.items()))

    ids = {t: {r[0] for r in q(con, f"select distinct id_patrimonio from '{f}'")} for t, f in T.items() if "id_patrimonio" in cols_of(con, f)}
    if ids:
        n = {t: len(s) for t, s in ids.items()}
        muchos = [f"{t}: {k} ids" for t, k in n.items() if k > 120]
        report("id_patrimonio_cardinalidad_plausible", "FAIL" if muchos else "PASS",
               "≈60 PS reales; tablas con >120 ids tienen claves inestables (mismo PS con varios slugs)", muchos)
        for otra in ("patrimonios_separados_balance_lineas", "patrimonios_separados_eeff_lineas", "patrimonios_separados_notas_detalle"):
            if "patrimonios_separados_balance_resumen" in ids and otra in ids:
                inter = len(ids["patrimonios_separados_balance_resumen"] & ids[otra])
                report(f"id_patrimonio_cruza:{otra[22:]}", "FAIL" if inter == 0 else "PASS",
                       f"{inter} ids en común entre balance_resumen y {otra[22:]} ({len(ids[otra])} ids)")


def audit_placeholders(con, T):
    print("\n[2] Placeholders y datos sintéticos")
    checks = [
        ("patrimonios_separados_nota_bonos_detalle", "fecha_vencimiento = fecha", "fecha_vencimiento = fecha del período (placeholder)"),
        ("patrimonios_separados_nota_bonos_detalle", "monto_colocado_mclp = saldo_insoluto_mclp", "monto_colocado = saldo_insoluto"),
        ("patrimonios_separados_nota_sobrecolateral_detalle", "valor_activos_mclp = 0 and valor_pasivos_bonos_mclp = 0", "activos y pasivos en 0"),
        ("patrimonios_separados_repos_detalle", "plazo_dias = 0 or tasa_interes_anual_pct in (0, 0.39) or cumplimiento_calificacion = 'Cumple / SI'", "plazo/tasa/cumplimiento por defecto"),
        ("patrimonios_separados_cartera_morosidad_detalle", "porcentaje_provision_pct > 100", "provisión > 100 %"),
        ("patrimonios_separados_nota_morosidad_detalle", "porcentaje_provision_pct > 100", "provisión > 100 %"),
        ("securitizadoras_balance_resumen", "coalesce(ganancia_perdida_ejercicio_m_clp, 0) = 0", "ganancia/pérdida nula o 0 (columna vacía)"),
    ]
    for t, cond, desc in checks:
        if t not in T:
            report(f"{t[22:] if t.startswith('patrimonios') else t}_placeholder", "INFO", f"tabla no publicada ({desc})"); continue
        n, k = q(con, f"select count(*), sum(case when {cond} then 1 else 0 end) from '{T[t]}'")[0]
        pct = (k or 0) / n if n else 0
        st = "FAIL" if pct >= 0.5 else ("WARN" if pct > 0.05 else "PASS")
        report(f"{t}:{desc}", st, f"{k}/{n} filas ({pct:.0%})")
    # participaciones rígidas en cualquier *_detalle con concepto/tramo
    for t, f in T.items():
        c = cols_of(con, f)
        grp = next((x for x in ("tramo_mora", "tipo_instrumento", "concepto_comision") if x in c), None)
        val = next((x for x in ("monto_cartera_mclp", "saldo_mclp", "gasto_periodo_mclp") if x in c), None)
        if grp and val and "id_patrimonio" in c and "periodo" in c:
            rows = q(con, f"""with s as (select {grp} g, {val}/nullif(sum({val}) over (partition by id_patrimonio, periodo),0) sh from '{f}')
                select g, count(*), round(stddev_pop(sh),5) from s group by 1 having count(*)>=50""")
            rig = [f"{g}: n={n}, sd={sd}" for g, n, sd in rows if sd is not None and sd < 0.005]
            report(f"{t}:participaciones_rigidas", "FAIL" if rig else "PASS",
                   f"{len(rig)} conceptos con participación constante (síntoma de porcentajes fijos)", rig)
    if "patrimonios_separados_nota_morosidad_detalle" in T:
        v = q(con, f"select count(distinct tramo_mora) from '{T['patrimonios_separados_nota_morosidad_detalle']}'")[0][0]
        report("tramos_mora_normalizados", "FAIL" if v > 10 else "PASS", f"{v} variantes textuales de tramo (esperado ≤ 8 con catálogo cerrado)")


def audit_contable(con, T):
    print("\n[3] Cuadre y cobertura")
    if "patrimonios_separados_balance_lineas" in T:
        f = T["patrimonios_separados_balance_lineas"]
        n, sin, cuadra, cero = q(con, f"""with t as (select id_patrimonio, periodo,
            sum(case when codigo_cuenta='10.000' then monto_m_clp end) a,
            sum(case when codigo_cuenta in ('21.000','22.000','23.000') then monto_m_clp else 0 end) p from '{f}' group by 1,2)
            select count(*), sum(case when a is null then 1 else 0 end),
                   sum(case when a is not null and abs(a-p)<=0.01*a then 1 else 0 end), sum(case when a=0 then 1 else 0 end) from t""")[0]
        report("balance_lineas_cuadre", "FAIL" if cuadra / n < 0.9 else "PASS",
               f"cuadran {cuadra}/{n} balances (±1 %); sin TOTAL ACTIVOS: {sin}; activos = 0: {cero}")
        cob = q(con, f"select substr(periodo,1,4), count(distinct periodo) from '{f}' group by 1 having count(distinct periodo) < 4 and substr(periodo,1,4) < '2026' order by 1")
        report("balance_lineas_cobertura_trimestral", "WARN" if cob else "PASS",
               f"{len(cob)} años con menos de 4 trimestres", [f"{y}: {k}" for y, k in cob])
    if "patrimonios_separados_eeff_lineas" in T:
        f = T["patrimonios_separados_eeff_lineas"]
        n, rec = q(con, f"select count(*), sum(case when cuenta_canonica is not null then 1 else 0 end) from '{f}'")[0]
        report("eeff_lineas_glosas_reconocidas", "FAIL" if rec / n < 0.5 else ("WARN" if rec / n < 0.8 else "PASS"),
               f"{rec}/{n} líneas mapeadas al catálogo ({rec/n:.0%}); revisar glosas no reconocidas y ampliar catalogo_fecu_ps.json")
        top = q(con, f"select glosa, count(*) c from '{f}' where cuenta_canonica is null group by 1 order by 2 desc limit 8")
        if top: report("eeff_lineas_glosas_no_reconocidas_top", "INFO", "más frecuentes", [f"{g}: {c}" for g, c in top])
        bp, cu = q(con, f"""select count(*), sum(case when cuadre_contable_ok then 1 else 0 end) from '{T.get("patrimonios_separados_balance_resumen", f)}'""")[0] if "patrimonios_separados_balance_resumen" in T else (0, 0)
        if bp:
            report("eeff_cuadre_por_balance", "FAIL" if cu / bp < 0.5 else ("WARN" if cu / bp < 0.8 else "PASS"), f"{cu}/{bp} balances con activos = pasivos+excedentes")
        ps, per = q(con, f"select count(distinct id_patrimonio), count(distinct periodo) from '{f}'")[0]
        report("eeff_lineas_cobertura", "INFO", f"{ps} patrimonios separados, {per} períodos")
    # correcciones manuales: cada fila debe citar PDF+página+justificación, corresponder a un balance publicado y dejarlo cuadrado
    csvp = os.path.join(BASE_DIR, "securitizadoras", "data", "correcciones_manuales.csv")
    if os.path.exists(csvp) and "patrimonios_separados_balance_resumen" in T:
        import csv
        rows = [r for r in csv.DictReader(open(csvp, encoding="utf-8")) if r.get("id_patrimonio") and not r["id_patrimonio"].startswith("#")]
        incompletas = [f"{r['id_patrimonio']} {r['periodo']} {r['cuenta_canonica']}" for r in rows if not (r.get("fuente_url") and r.get("pagina_pdf") and r.get("justificacion") and r.get("autor"))]
        fb = T["patrimonios_separados_balance_resumen"]
        cols = [c[0] for c in q(con, f"describe select * from '{fb}'")]
        if "correcciones_manuales" in cols:
            mal = q(con, f"select id_patrimonio, periodo from '{fb}' where coalesce(correcciones_manuales,0) > 0 and not cuadre_contable_ok")
            sin = q(con, f"select count(*) from '{fb}' where coalesce(correcciones_manuales,0) > 0")[0][0]
        else:
            mal, sin = [], 0
        claves = {(r[0], r[1]) for r in q(con, f"select id_patrimonio, periodo from '{fb}'")}
        huerfanas = [f"{r['id_patrimonio']} {r['periodo']}" for r in rows if (r["id_patrimonio"], r["periodo"]) not in claves]
        report("correcciones_manuales", "FAIL" if (incompletas or mal) else ("WARN" if huerfanas else "PASS"),
               f"{len(rows)} correcciones en CSV; {sin} balances las usan; {len(mal)} no cuadran tras aplicarlas; {len(incompletas)} sin cita completa; {len(huerfanas)} sin balance",
               [f"no cuadra: {a} {b}" for a, b in mal] + [f"sin cita: {x}" for x in incompletas] + [f"sin balance: {x}" for x in huerfanas])
    if "securitizadoras_balance_resumen" in T:
        f = T["securitizadoras_balance_resumen"]
        n, d = q(con, f"select count(*), sum(case when abs(total_activos_m_clp-total_pasivos_m_clp-patrimonio_neto_m_clp)>0.01*total_activos_m_clp then 1 else 0 end) from '{f}'")[0]
        report("securitizadoras_cuadre", "PASS" if d == 0 else "FAIL", f"{d}/{n} descuadres")
    if "patrimonios_separados_balance_resumen" in T:
        f = T["patrimonios_separados_balance_resumen"]
        r = q(con, f"select count(*), count(distinct id_patrimonio), min(periodo), max(periodo) from '{f}'")[0]
        report("ps_balance_resumen_cobertura", "WARN" if r[1] < 40 or r[2] > "2015" else "PASS",
               f"{r[0]} filas, {r[1]} PS, {r[2]} → {r[3]} (balance_lineas cubre desde 2010 y 11 administradoras)")
    cob = os.path.join(OUT_DIR, "patrimonios_separados_cobertura.parquet")
    report("tabla_cobertura_publicada", "PASS" if os.path.exists(cob) else "WARN", "existe" if os.path.exists(cob) else "ausente")


def audit_procedencia(con, T):
    print("\n[4] Procedencia")
    falt = []
    for t, f in T.items():
        c = cols_of(con, f)
        miss = [x for x in ("fuente_url", "metodo", "fecha_extraccion", "script_version") if x not in c]
        if miss:
            falt.append(f"{t}: faltan {miss}")
    report("columnas_procedencia", "FAIL" if falt else "PASS", f"{len(falt)}/{len(T)} tablas sin trazabilidad completa", falt)


def audit_web(T):
    print("\n[5] Publicación web / manifest")
    mf = json.load(open(os.path.join(BASE_DIR, "data_manifest.json"), encoding="utf-8"))
    en_manifest = {t["id"] for t in mf["tables"]}
    no_cat = [t for t in T if t not in en_manifest]
    report("tablas_en_manifest", "WARN" if no_cat else "PASS", f"{len(no_cat)} tablas publicadas sin entrada en data_manifest.json", no_cat)
    side = open(os.path.join(BASE_DIR, "docs", "js", "sidebar.js"), encoding="utf-8").read()
    dic = open(os.path.join(BASE_DIR, "docs", "js", "data_dictionary.js"), encoding="utf-8").read()
    fails = [t for t in T if t in side and t in dic and t.startswith("patrimonios_separados_") and t not in ("patrimonios_separados_maestro", "patrimonios_separados_balance_resumen")]
    # sólo informa: la decisión de despublicar depende de los checks anteriores
    report("tablas_ps_expuestas_en_web", "INFO", f"{len(fails)} tablas de detalle de PS expuestas en sidebar+diccionario", fails)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
    print("=" * 78 + "\nAUDITORÍA v2 — Securitizadoras y Patrimonios Separados\n" + "=" * 78)
    T = tablas()
    con = duckdb.connect()
    audit_codigo(T); audit_identidad(con, T); audit_placeholders(con, T); audit_contable(con, T); audit_procedencia(con, T); audit_web(T)
    fails = [r for r in RESULTS if r["status"] == "FAIL"]; warns = [r for r in RESULTS if r["status"] == "WARN"]
    print("\n" + "=" * 78 + f"\nRESULTADO: {len(fails)} FAIL · {len(warns)} WARN · {len(RESULTS)-len(fails)-len(warns)} PASS/INFO")
    for r in fails: print(f"  FAIL → {r['check']}")
    print("=" * 78)
    if a.json:
        json.dump(RESULTS, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
