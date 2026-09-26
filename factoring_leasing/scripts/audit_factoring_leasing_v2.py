"""
Auditoría v2 — Factoring & Leasing (CMF).

A diferencia de audit_factoring_leasing.py (que sólo valida forma: claves, nulos, módulo 11),
esta suite valida *sustancia*: plausibilidad de los datos, consistencia maestro <-> balances,
cobertura temporal, procedencia y seguridad del código. Devuelve exit code 1 si hay FAIL.

Uso:
    python factoring_leasing/scripts/audit_factoring_leasing_v2.py [--json salida.json]

Dependencias: duckdb (pip install duckdb). No requiere pandas.
"""
import os
import re
import sys
import json
import glob
import argparse

try:
    import duckdb
except ImportError:
    print("Falta duckdb: pip install duckdb")
    sys.exit(2)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "factoring_leasing")
SCRIPTS_DIR = os.path.join(BASE_DIR, "factoring_leasing", "scripts")

T = {
    "maestro": os.path.join(OUT_DIR, "factoring_leasing_maestro.parquet"),
    "balance": os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.parquet"),
    "efectivo": os.path.join(OUT_DIR, "factoring_leasing_nota_efectivo_detalle.parquet"),
    "cartera": os.path.join(OUT_DIR, "factoring_leasing_cartera_morosidad_detalle.parquet"),
}

RESULTS = []


def report(check, status, detail, evidence=None):
    RESULTS.append({"check": check, "status": status, "detail": detail, "evidence": evidence})
    icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]", "INFO": "[INFO]"}[status]
    print(f"  {icon} {check}: {detail}")
    if evidence:
        for e in (evidence if isinstance(evidence, list) else [evidence])[:8]:
            print(f"         - {e}")


def dv_m11(body):
    s, mult = 0, 2
    for c in reversed(str(body)):
        s += int(c) * mult
        mult = mult + 1 if mult < 7 else 2
    r = 11 - (s % 11)
    return {11: "0", 10: "K"}.get(r, str(r))


def q(con, sql):
    return con.execute(sql).fetchall()


# ----------------------------------------------------------------------------
# 0. Seguridad / reproducibilidad del código
# ----------------------------------------------------------------------------
def audit_code():
    print("\n[0] Código: secretos, rutas locales, TLS, reproducibilidad")
    secret_pat = re.compile(r"(PASS\w*\s*=\s*['\"][^'\"]+['\"])|(Siete\(\s*['\"][^'\"]+@)", re.I)
    local_pat = re.compile(r"[A-Za-z]:\\\\|Respaldo_BCCH|Desktop")
    hits_secret, hits_local, hits_tls = [], [], []
    for f in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")):
        if os.path.basename(f).startswith("audit_"):
            continue
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh, 1):
                rel = os.path.relpath(f, BASE_DIR)
                if secret_pat.search(line):
                    hits_secret.append(f"{rel}:{i}")
                if local_pat.search(line):
                    hits_local.append(f"{rel}:{i}")
                if "CERT_NONE" in line:
                    hits_tls.append(f"{rel}:{i}")
    report("secretos_en_codigo", "FAIL" if hits_secret else "PASS",
           f"{len(hits_secret)} credenciales hardcodeadas (rotar + mover a variables de entorno)", hits_secret)
    report("rutas_locales", "FAIL" if hits_local else "PASS",
           f"{len(hits_local)} referencias a rutas de Windows/Escritorio (no reproducible)", hits_local)
    report("tls_deshabilitado", "WARN" if hits_tls else "PASS",
           f"{len(hits_tls)} usos de ssl.CERT_NONE", hits_tls)

    cat = os.path.join(BASE_DIR, "factoring_leasing", "data", "catalogo_factoring_leasing_cmf.csv")
    report("catalogo_versionado", "PASS" if os.path.exists(cat) else "FAIL",
           "catalogo_factoring_leasing_cmf.csv " + ("presente" if os.path.exists(cat)
           else "ausente (git-ignorado por *.csv): el maestro no se puede regenerar"))

    # Script de notas: ¿usa la descarga real o genera valores por porcentaje?
    notas = os.path.join(SCRIPTS_DIR, "02_extract_factoring_leasing_notas_series.py")
    if os.path.exists(notas):
        src = open(notas, encoding="utf-8", errors="ignore").read()
        defines_fetch = "def fetch_cmf_pdf_stream" in src
        calls_fetch = len(re.findall(r"(?<!def )fetch_cmf_pdf_stream\(", src)) > 1  # >1: la llamada recursiva interna cuenta 1
        pct_consts = len(re.findall(r"activos_liq \* pct_|cartera_prod \* pct_tramo", src))
        status = "FAIL" if (pct_consts and not calls_fetch) else "PASS"
        report("notas_generadas_por_porcentaje", status,
               f"fetch definido={defines_fetch}, fetch invocado fuera de sí mismo={calls_fetch}, "
               f"multiplicaciones por porcentaje fijo={pct_consts}")


# ----------------------------------------------------------------------------
# 1. Maestro
# ----------------------------------------------------------------------------
def audit_maestro(con):
    print("\n[1] Maestro")
    m = T["maestro"]
    rows = q(con, f"select rut, rut_formateado, vigente, estado from '{m}'")
    bad = [r[0] for r in rows if dv_m11(r[0].split('-')[0]) != r[0].split('-')[1]]
    report("rut_modulo11", "FAIL" if bad else "PASS", f"{len(bad)} RUT inválidos de {len(rows)}", bad)
    dup = q(con, f"select rut, count(*) from '{m}' group by 1 having count(*)>1")
    report("rut_unico", "FAIL" if dup else "PASS", f"{len(dup)} duplicados")
    fmt = [r[0] for r in rows if not re.fullmatch(r"\d{7,8}-[\dK]", r[0])]
    report("rut_formato_canonico", "FAIL" if fmt else "PASS", "formato NNNNNNNN-D sin puntos", fmt)


# ----------------------------------------------------------------------------
# 2. Balance
# ----------------------------------------------------------------------------
def audit_balance(con):
    print("\n[2] Balance resumen")
    b, m = T["balance"], T["maestro"]
    n, nk = q(con, f"select count(*), count(distinct (rut, periodo)) from '{b}'")[0]
    report("clave_unica_rut_periodo", "PASS" if n == nk else "FAIL", f"{n} filas, {nk} claves")

    badp = q(con, f"select count(*) from '{b}' where not regexp_matches(periodo, '^\\d{{4}}-(03|06|09|12)$')")[0][0]
    report("periodo_formato_trimestral", "PASS" if badp == 0 else "FAIL", f"{badp} períodos fuera de YYYY-MM trimestral")

    desc = q(con, f"""select count(*) from '{b}'
        where abs(total_activos_m_clp - total_pasivos_m_clp - patrimonio_neto_m_clp) > 1""")[0][0]
    report("cuadre_A_eq_P_mas_Pat", "PASS" if desc == 0 else "FAIL", f"{desc} filas descuadradas (>1 M$)")
    report("cuadre_es_tautologico", "WARN",
           "el pipeline deriva patrimonio = A - P cuando falta la cuenta CMF; agregar columna patrimonio_origen")

    huerf = q(con, f"select distinct b.rut, b.nombre_empresa from '{b}' b left join '{m}' m using(rut) where m.rut is null")
    report("integridad_maestro", "PASS" if not huerf else "FAIL", f"{len(huerf)} RUT en balance sin maestro", huerf)

    # Maestro <-> balance: vigencia
    canc = q(con, f"""select m.nombre_fantasia, m.estado, max(b.periodo) from '{m}' m join '{b}' b using(rut)
        where m.vigente = 0 group by 1,2 having max(b.periodo) >= '2025-01' order by 1""")
    report("cancelados_con_eeff_recientes", "FAIL" if canc else "PASS",
           f"{len(canc)} entidades 'Histórico/Cancelado' con EEFF desde 2025", [f"{a} | {s} | último {p}" for a, s, p in canc])
    sinb = q(con, f"""select m.nombre_fantasia, m.tipo_licencia from '{m}' m left join (select distinct rut from '{b}') b using(rut)
        where b.rut is null and m.vigente = 1""")
    report("vigentes_sin_balance", "WARN" if sinb else "PASS",
           f"{len(sinb)} entidades activas sin ningún balance (cobertura sobredeclarada en sidebar)", [a for a, _ in sinb])

    # Plausibilidad: cartera / activos
    low = q(con, f"""select nombre_empresa, periodo, round(cartera_credito_m_clp/total_activos_m_clp,2)
        from '{b}' where periodo = (select max(periodo) from '{b}' where periodo <= '2025-12')
        and cartera_credito_m_clp/total_activos_m_clp < 0.5 order by 3""")
    report("cartera_sobre_activos_plausible", "FAIL" if len(low) >= 5 else ("WARN" if low else "PASS"),
           f"{len(low)} financieras con cartera/activos < 0,5 al 2025-12 → definición de cartera_credito incompleta",
           [f"{a}: {r}" for a, _, r in low])

    # Patrimonio negativo
    neg = q(con, f"select nombre_empresa, periodo, patrimonio_neto_m_clp from '{b}' where patrimonio_neto_m_clp < 0")
    report("patrimonio_negativo", "WARN" if neg else "PASS", f"{len(neg)} filas (verificar si real o cuenta ausente)",
           [f"{a} {p}: {v}" for a, p, v in neg])

    # PNC = 0
    pnc0 = q(con, f"select nombre_empresa, count(*) from '{b}' where pasivos_no_corrientes_m_clp = 0 group by 1 order by 2 desc")
    report("pasivos_no_corrientes_cero", "WARN" if pnc0 else "PASS",
           f"{sum(c for _, c in pnc0)} filas con PNC = 0 (posible nombre de cuenta distinto)", [f"{a}: {c}" for a, c in pnc0])

    # Saltos QoQ
    jumps = q(con, f"""select nombre_empresa, periodo, round(total_activos_m_clp/prev-1,2) from (
        select nombre_empresa, periodo, total_activos_m_clp,
               lag(total_activos_m_clp) over (partition by rut order by periodo) prev from '{b}')
        where prev > 0 and abs(total_activos_m_clp/prev-1) > 0.6 order by 3 desc""")
    report("saltos_qoq_activos_gt_60pct", "WARN" if jumps else "PASS", f"{len(jumps)} saltos no documentados",
           [f"{a} {p}: {c:+.0%}" for a, p, c in jumps])

    # Huecos
    gaps = q(con, f"""with p as (select distinct periodo from '{b}'),
        e as (select rut, nombre_empresa, count(*) n, min(periodo) p0, max(periodo) p1 from '{b}' group by 1,2)
        select nombre_empresa, (select count(*) from p where p.periodo between e.p0 and e.p1) - n as huecos, n
        from e where (select count(*) from p where p.periodo between e.p0 and e.p1) - n > 0 order by 2 desc""")
    report("huecos_intermedios", "WARN" if gaps else "PASS", f"{len(gaps)} entidades con trimestres faltantes",
           [f"{a}: {h} huecos ({n} presentes)" for a, h, n in gaps])

    # TC implícito plausible y sin fallback
    tc = q(con, f"""select periodo, round(median(total_activos_m_clp/nullif(total_activos_m_usd,0)),1) from '{b}' group by 1""")
    fb = [f"{p}: {v}" for p, v in tc if v in (900.0, 850.0)]
    rng = [f"{p}: {v}" for p, v in tc if not (500 <= v <= 1100)]
    report("tipo_cambio_sin_fallback", "FAIL" if fb else "PASS", f"{len(fb)} períodos con TC = fallback 900/850", fb)
    report("tipo_cambio_rango", "FAIL" if rng else "PASS", "TC implícito entre 500 y 1.100 CLP/USD", rng)

    # Procedencia
    cols = [r[0] for r in q(con, f"describe select * from '{b}'")]
    prov = [c for c in ("fuente_url", "metodo", "fecha_extraccion", "script_version") if c in cols]
    report("columnas_procedencia", "WARN" if len(prov) < 2 else "PASS",
           f"presentes: {prov or 'ninguna'} (recomendado: fuente_url, metodo, fecha_extraccion, script_version)")


# ----------------------------------------------------------------------------
# 3. Notas: detección de datos sintéticos
# ----------------------------------------------------------------------------
def audit_notas(con):
    print("\n[3] Notas desagregadas (efectivo, cartera/morosidad)")
    for key, tbl, grp, val, part in (
        ("efectivo", T["efectivo"], "concepto", "monto_mclp", "rut, periodo"),
        ("cartera", T["cartera"], "tramo_morosidad", "cartera_bruta_mclp", "rut, periodo, linea_producto"),
    ):
        if not os.path.exists(tbl):
            report(f"{key}_existe", "INFO", "tabla no publicada")
            continue
        rows = q(con, f"""with s as (select {grp} g, {val}/nullif(sum({val}) over (partition by {part}),0) sh from '{tbl}')
            select g, count(*), round(min(sh),4), round(max(sh),4), round(stddev_pop(sh),5) from s group by 1 order by 2 desc""")
        rigid = [f"{g}: n={n}, share {lo:.2%}–{hi:.2%}, sd={sd}" for g, n, lo, hi, sd in rows if n >= 50 and (sd or 0) < 0.005]
        status = "FAIL" if rigid else "PASS"
        report(f"{key}_participaciones_rigidas", status,
               f"{len(rigid)}/{len(rows)} conceptos con participación casi constante en todas las entidades/períodos "
               f"→ {'datos generados por porcentaje fijo, NO extracción CMF' if rigid else 'dispersión compatible con datos reales'}",
               rigid)
        # reconciliación con balance
        bal_col = "activos_liquidos_m_clp" if key == "efectivo" else "cartera_credito_m_clp"
        rec = q(con, f"""select count(*) from (select n.rut, n.periodo, sum({val}) s, any_value(b.{bal_col}) t
            from '{tbl}' n join '{T['balance']}' b using(rut, periodo) group by 1,2) where abs(s - t) > 0.005 * t""")[0][0]
        report(f"{key}_reconcilia_con_balance", "PASS" if rec == 0 else "WARN",
               f"{rec} pares rut×periodo con suma de la nota ≠ balance (>0,5 %) — con datos sintéticos este check pasa trivialmente")

    # ¿Cómo está etiquetado en el manifest?
    mf = os.path.join(BASE_DIR, "data_manifest.json")
    if os.path.exists(mf):
        d = json.load(open(mf, encoding="utf-8"))
        bad = [t["id"] for t in d.get("tables", []) if t.get("sector") == "factoring_leasing"
               and ("nota" in t["id"] or "morosidad" in t["id"]) and t.get("modo") == "Automático"]
        report("manifest_etiqueta_notas", "FAIL" if bad else "PASS",
               f"tablas de notas en manifest etiquetadas 'Automático' con origen CMF "
               f"({'ninguna' if not bad else bad}); nota: hoy las notas no están en el manifest pero sí en la web", bad)

    # data_dictionary.js / sidebar.js: ¿se publican como Automático / CMF?
    for jsname in ("data_dictionary.js", "sidebar.js"):
        js = os.path.join(BASE_DIR, "docs", "js", jsname)
        if not os.path.exists(js):
            continue
        src = open(js, encoding="utf-8", errors="ignore").read()
        pub = [t for t in ("factoring_leasing_nota_efectivo_detalle", "factoring_leasing_cartera_morosidad_detalle") if t in src]
        auto = []
        for t in pub:
            i = src.find(t)
            block = src[i:i + 2500]
            if 'modo: "Automático"' in block or "Notas a los Estados Financieros" in block:
                auto.append(t)
        report(f"web_{jsname}_publica_notas_sinteticas", "FAIL" if pub else "PASS",
               f"{len(pub)} tablas sintéticas expuestas en {jsname}" + (f"; {len(auto)} descritas como Automático/CMF" if auto else ""), pub)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="ruta para volcar resultados")
    args = ap.parse_args()

    print("=" * 78)
    print("AUDITORÍA v2 — Factoring & Leasing")
    print("=" * 78)
    missing = [k for k, p in T.items() if k in ("maestro", "balance") and not os.path.exists(p)]
    if missing:
        print(f"Faltan tablas base: {missing}")
        sys.exit(2)

    con = duckdb.connect()
    audit_code()
    audit_maestro(con)
    audit_balance(con)
    audit_notas(con)

    fails = [r for r in RESULTS if r["status"] == "FAIL"]
    warns = [r for r in RESULTS if r["status"] == "WARN"]
    print("\n" + "=" * 78)
    print(f"RESULTADO: {len(fails)} FAIL · {len(warns)} WARN · {len(RESULTS) - len(fails) - len(warns)} PASS/INFO")
    for r in fails:
        print(f"  FAIL → {r['check']}")
    print("=" * 78)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(RESULTS, fh, ensure_ascii=False, indent=2)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
