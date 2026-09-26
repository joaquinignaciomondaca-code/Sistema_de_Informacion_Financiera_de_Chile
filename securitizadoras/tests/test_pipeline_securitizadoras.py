"""
Pruebas sin red del pipeline v2 de securitizadoras / patrimonios separados.
Ejecutar: python securitizadoras/tests/test_pipeline_securitizadoras.py   (exit 1 si falla)
Los textos simulan la salida de pymupdf (una celda por línea) de un EEFF anual de PS y una FECU IFRS HTML de gestora.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import pipeline_securitizadoras as P

PAGINA_PORTADA = "TRANSA SECURITIZADORA S.A.\nPATRIMONIO SEPARADO N° 12\nInscripción Registro de Valores N° 345\nEstados Financieros al 31 de diciembre de 2024\n"
# Layout A (Volcom BVOLS 12/2024, KPMG): glosas sin código, una celda por línea — cifras reales del PDF CMF
PAGINA_BALANCE_ACT = """VOLCOM SECURITIZADORA S.A. PATRIMONIO SEPARADO BVOLS
Balances Generales del Patrimonio Separado
Al 31 de diciembre de 2024 y 2023
(En Miles de pesos chilenos – M$)
ACTIVOS
Notas
31-12-2024
M$
31-12-2023
M$
Activos Circulantes
Disponible
5
119.969
15.615
Valores negociables
6
1.231.126
901.211
Activo securitizado (corto plazo)
9
4.335.870
1.976.576
Otros activos circulantes
11
6.488.572
18.756
Total activos circulantes
12.175.537
2.912.158
Otros Activos
Activo securitizado (largo plazo)
9
89.303.250
62.382.002
Total otros activos
89.303.250
62.382.002
Total Activos
101.478.787
65.294.160
"""
PAGINA_BALANCE_PAS = """VOLCOM SECURITIZADORA S.A. PATRIMONIO SEPARADO BVOLS
Balances Generales del Patrimonio Separado
PASIVOS
Pasivos Circulantes
Remuneración por pagar por administración y custodia de los activos
12
959.863
771.782
Otros acreedores (corto plazo)
13
6.360.033
75.137
Obligaciones por títulos de deuda de securitización (corto plazo)
14
954.601
821.869
Total pasivos circulantes
8.295.205
1.668.788
Pasivos a largo plazo
Obligaciones por títulos de deuda de securitización (largo plazo)
14
91.908.328
62.399.145
Total pasivos largo plazo
91.908.328
62.399.145
Excedentes acumulados
Reservas de excedentes anteriores
15
1.226.227
720.363
Excedentes del ejercicio
15
49.027
505.864
Total excedentes acumulados
1.275.254
1.226.227
Total Pasivos
101.478.787
65.294.160
"""
PAGINA_PASIVO_SIN_PLAZO = """BALANCE GENERAL
PASIVOS
Pasivos circulantes
Obligaciones por títulos de deuda de securitización
1.000
900
Otros acreedores
1.010
909
Total pasivos circulantes
2.010
1.809
Pasivos largo plazo
Obligaciones por títulos de deuda de securitización
5.000
6.000
Otros acreedores
2.020
3.030
Total pasivos largo plazo
5.020
6.030
Total pasivos
6.030
6.939
"""
PAGINA_NOTA_MORA_TABLA = """Nota 7 - Activos securitizados en mora
Cuotas
1 a 3
120
80.000
4 o más
15
9.000
Totales
135
89.000
"""
PAGINA_EXCEDENTES = """Estado de Determinación de Excedentes del Patrimonio Separado
Por los años comprendidos entre el 01 de enero y el 31 de diciembre de 2024 y 2023
Ingresos
Intereses por activo securitizado
16
2.918.171
2.770.392
Total ingresos
2.918.171
2.770.392
Gastos
Remuneración por administración y custodia
17
(400.000)
(350.000)
Total gastos
(2.869.144)
(2.264.528)
Excedente del ejercicio
49.027
505.864
"""
# Layout B (Security BSECS-9 12/2023): formato FECU-PS con códigos y fila completa por línea
PAGINA_FECU_CODIGOS = """SECURITIZADORA SECURITY S.A. PATRIMONIO SEPARADO BSECS-9
BALANCE GENERAL
ACTIVOS  Antecedentes al  31-12-2023  31-12-2022
11.010 Disponible 879.861 875.566
11.020 Valores negociables 94.886 167.393
11.100 Activo securitizado (corto plazo) 2.850.328 2.961.632
11.000 TOTAL ACTIVOS CIRCULANTES 5.031.192 5.204.985
13.100 Activo securitizado (largo plazo) 7.306.158 9.999.988
13.000 TOTAL OTROS ACTIVOS 7.306.158 9.999.988
10.000 TOTAL ACTIVOS 12.337.350 15.204.973
21.000 TOTAL PASIVOS CIRCULANTES 1.000.000 1.100.000
22.000 TOTAL PASIVOS LARGO PLAZO 10.000.000 12.000.000
23.000 TOTAL PATRIMONIO 1.337.350 2.104.973
20.000 TOTAL PASIVOS 12.337.350 15.204.973
"""
PAGINA_EFECTIVO = "NOTA 5 - DISPONIBLE\nBanco de Chile\n1.000\nBanco Santander\n250\nHonorarios por pagar\n300\n"
PAGINA_MORA = """NOTA 7 - ACTIVO SECURITIZADO EN MORA
Tramo
N° deudores
Cartera M$
Provisión M$
Al día
120
80.000
400
1 a 30 días
15
9.000
450
31 a 60 días
4
5.000
1.000
Más de 180 días
2
1.350
9.999
Total
141
95.350
1.850
"""
FECU_HTML = """[210000] Estado de situación financiera
<td><div>Total de activos</div></td><td class="derecha"><div>12.345.678</div></td>
<td><div>Total de pasivos</div></td><td class="derecha"><div>2.345.678</div></td>
<td><div>Patrimonio total</div></td><td class="derecha"><div>10.000.000</div></td>
<td><div>Efectivo y equivalentes al efectivo</div></td><td class="derecha"><div>500.000</div></td>
[310000] <td><div>Ganancia (pérdida)</div></td><td class="derecha"><div>-150.000</div></td>
"""

fallos = []
def check(cond, msg):
    (print("  ok  ", msg) if cond else (fallos.append(msg), print("  FAIL", msg)))

print("meta"); m = P.meta_desde_texto(PAGINA_PORTADA, "Patrimonios Separados al 12/2024", "96765170", "TRANSA SECURITIZADORA S.A.")
check(m["codigo_emision"] == "PS-12" and m["id_patrimonio"] == "96765170_ps_12", "código PS-12 e id estable")
check(m["rut_administradora"] == "96765170-2", "RUT con DV correcto (96765170-2)")
check(m["nro_registro_cmf"] == "345", "número de registro")
check(P.meta_desde_texto("Texto sin identificación", "EEFF", "96765170", "X") is None, "sin código → None (no se inventa PS-GEN)")

print("etiqueta web CMF")
for et, esp in [("Patrimonios Separados - BVOLS 3 al 12/2024", "BVOLS-3"), ("Patrimonios Separados - BSECS 9 al 12/2025", "BSECS-9"),
                ("Patrimonios Separados - N° 12 al 12/2024", "PS-12"), ("Patrimonios Separados - PS 35 al 12/2024", "PS-35"),
                ("Patrimonios Separados al 12/2024", None), ("Patrimonios Separados - PATRIMONIO SEPARADO N°35 al 12/2024", "PS-35"),
                ("Patrimonios Separados - Patrimonio 10 al 03/2022", "PS-10"), ("Patrimonios Separados - PS7 firmadp al 09/2023", "PS-7"),
                ("Patrimonios Separados - BVOLS3 al 12/2025", "BVOLS-3"), ("Patrimonios Separados - V al 12/2021", "PS-5"),
                ("Patrimonios Separados - Patrimonio Separado NA-2 al 06/2022", "PS-2"), ("Patrimonios Separados - BBICS-U al 12/2023", "BBICS-U")]:
    check(P.codigo_desde_etiqueta_web(et) == esp, f"{et!r} → {esp}")
m2 = P.meta_desde_texto("N° INSCRIPCION DE LA EMISION EN EL REGISTRO: 1245\n", "Patrimonios Separados - BSECS 9 al 12/2025", "96847360", "SECURITY")
check(m2["codigo_emision"] == "BSECS-9" and m2["nro_registro_cmf"] == "1245", "etiqueta web prevalece sobre typos del PDF; nº inscripción")

print("eeff líneas — layout glosas (Volcom)")
lin = P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_BALANCE_ACT, PAGINA_BALANCE_PAS, PAGINA_EXCEDENTES])
v = {l["cuenta_canonica"]: l for l in lin if l["cuenta_canonica"]}
check(v["ACTIVO_SECURITIZADO_CP"]["monto_mclp"] == 4335870 and v["ACTIVO_SECURITIZADO_CP"]["nota"] == "9", "nota 9 separada del monto (v1 leía 94.335.870)")
check(v["TOTAL_ACTIVOS"]["monto_mclp"] == 101478787 and v["TOTAL_ACTIVOS"]["monto_anterior_mclp"] == 65294160, "total activos año actual y anterior")
check(v["TOTAL_PASIVOS_Y_PATRIMONIO"]["monto_mclp"] == 101478787, "'Total Pasivos' mapeado a 20.000")
check(v["OTROS_PASIVOS_CIRCULANTES"]["monto_mclp"] == 6360033, "'Otros acreedores (corto plazo)' → 21.200")
check(v["EXCEDENTE_DEL_EJERCICIO"]["estado"] == "BALANCE" and v["EXCEDENTE_NETO_DEL_PERIODO"]["estado"] == "EXCEDENTES", "misma glosa, distinto estado")
check(v["GASTO_REMUNERACIONES_ADMINISTRACION"]["monto_mclp"] == -400000, "paréntesis → negativo")
lsp = {(l["glosa"], l["monto_mclp"]): l["cuenta_canonica"] for l in P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_PASIVO_SIN_PLAZO])}
check(lsp.get(("Obligaciones por títulos de deuda de securitización", 1000)) == "OBLIG_TITULOS_DEUDA_CP" and
      lsp.get(("Obligaciones por títulos de deuda de securitización", 5000)) == "OBLIG_TITULOS_DEUDA_LP" and
      lsp.get(("Otros acreedores", 2020)) == "OTROS_ACREEDORES_LP", f"glosas sin plazo se resuelven por sección: {lsp}")
check(P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_NOTA_MORA_TABLA]) == [], "página de nota (sin línea de total reconocida) descartada")
no_rec = [l["glosa"] for l in lin if not l["cuenta_canonica"]]
check(no_rec == [], f"todas las glosas reconocidas: {no_rec}")
conc = P.conciliar(lin)
check(conc == {"activos_igual_pasivos": True, "activos_igual_componentes": True, "pasivos_igual_componentes": True}, f"conciliaciones {conc}")
res = P.derivar_resumen(lin)
check(res["disponible_mclp"] == 119969 and res["cuadre_contable_ok"] and res["excedente_neto_periodo_mclp"] == 49027, "resumen derivado de las líneas")

print("eeff líneas — layout FECU con códigos (Security)")
lin2 = P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_FECU_CODIGOS])
v2 = {l["codigo_fecu"]: l for l in lin2}
check(set(v2) >= {"11.010", "11.100", "10.000", "20.000", "23.000"}, f"códigos leídos: {sorted(v2)}")
check(v2["11.100"]["cuenta_canonica"] == "ACTIVO_SECURITIZADO_CP" and v2["11.100"]["monto_mclp"] == 2850328, "mapeo por código")
check(P.conciliar(lin2)["activos_igual_pasivos"] is True, "cuadre con códigos")
check(P.parse_eeff_lineas(["Índice\nBalances Generales........4\n1.000\n2.000\n3.000"]) == [], "página de índice ignorada")
check(P.parse_eeff_lineas(["BALANCE\nDISPONIBLE\n10\nTOTAL ACTIVOS\n(texto)\n"]) == [] or P.derivar_resumen(P.parse_eeff_lineas(["BALANCE\nDISPONIBLE\n10\nTOTAL ACTIVOS\n(texto)\n"]))["total_activos_mclp"] is None, "sin total → NULL, nunca se copia el otro total")

print("nota efectivo"); efe = P.parse_nota_efectivo_ps([""] * 3 + [PAGINA_EFECTIVO])
check([e["concepto"] for e in efe] == ["Banco de Chile", "Banco Santander"], "bancos extraídos, pasivos excluidos")
check(sum(e["monto_mclp"] for e in efe) == 1250, "suma = disponible del balance (1.250)")
check(P.parse_nota_efectivo_ps([""] * 3 + ["DISPONIBLE\nBanco Estado\n500\n"]) == [], "sin número de nota → no se publica")

print("nota morosidad"); mor, desc = P.parse_nota_morosidad_ps([""] * 3 + [PAGINA_MORA])
tramos = {r["tramo_mora"]: r for r in mor}
check(set(tramos) == {"AL_DIA", "1_30", "31_60", "TOTAL"}, f"tramos del catálogo cerrado: {sorted(tramos)}")
check(desc == 1, "tramo con provisión > cartera descartado y contado")
check(tramos["1_30"]["numero_deudores"] == 15 and tramos["1_30"]["porcentaje_provision_pct"] == 5.0, "deudores y % provisión")

print("fecu gestora"); f = P.parse_fecu_gestora(FECU_HTML)
check(f["total_activos_m_clp"] == 12345.678 and f["patrimonio_neto_m_clp"] == 10000 and f["patrimonio_neto_es_derivado"] is False, "totales en miles, patrimonio leído")
check(f["ganancia_perdida_ejercicio_m_clp"] == -150, "ganancia (pérdida) negativa capturada")
check(P.parse_fecu_gestora("<html>sin fecu</html>") is None, "html sin FECU → None")
H310 = '<td><div>Ganancia (pérdida) [sinopsis]</div></td></tr><tr><td><div>Ganancia (pérdida), antes de impuestos</div></td><td class="x"><div>492.160</div></td></tr><tr><td><div>Ganancia (pérdida)</div></td><td class="x"><div>397.783</div></td>'
check(P.parse_fecu_gestora(FECU_HTML.split("Ganancia")[0] + H310)["ganancia_perdida_ejercicio_m_clp"] == 397.783, "ganancia: estructura del estado de resultados [310000] (fallback genérico)")
check(P.parse_fecu_gestora(FECU_HTML.replace("pérdida", "p&eacute;rdida"))["ganancia_perdida_ejercicio_m_clp"] == -150, "entidades HTML (p&eacute;rdida) resueltas")
check(P.parse_fecu_gestora(FECU_HTML.replace("Ganancia (pérdida)", "Otra cosa"))["ganancia_perdida_ejercicio_m_clp"] is None, "ganancia ausente → NULL (no 0)")

print("utilidades")
check(P.rut_completo("96765170") == "96765170-2" and P.rut_completo("76965774") == "76965774-6", "módulo 11")
check(P.parse_num("(1.234,5)") == -1234.5 and P.parse_num("-") is None and P.parse_num("abc") is None, "parse_num")


# ---- casos reales de la corrida de diagnóstico 2023-2025 (texto pymupdf tal cual) ----
print("período según PDF")
check(P.periodo_segun_pdf(["Estados financieros intermedios terminados\nal 30 de junio de 2026 y 2025", "Balance al 30 de junio de 2026", "31.12.2025"]) == "2026-06", "fecha de cierre más frecuente")
check(P.periodo_segun_pdf(["sin fechas"]) is None, "sin fecha → None")

print("layouts reales (diagnóstico)")
PAG_EF_2COL = """RAZON SOCIAL: EF SECURITIZADORA S.A.
BALANCE DEL PATRIMONIO SEPARADO
PASIVOS
Nota
Pasivo circulante
Remuneraciones por pagar por auditoria externa
11
         14.503         11.020 
Otros acreedores (corto plazo)
14
    6.528.686  10.982.312 
Total pasivos circulantes
   6.543.189  10.993.332 
Pasivo largo plazo
Obligaciones por títulos de deuda de securitización (largo plazo) 
10
  23.530.223  33.063.518 
Total pasivo largo plazo
  23.530.223  33.063.518 
Excedente acumulado del patrimonio separado
Reservas de excedentes anteriores
-
                   
                  - 
Excedente del período (déficit)
         14.394         63.737 
Total Excedente (Déficit) Acumulado
      14.394         63.737 
TOTAL PASIVOS
   30.087.806  44.120.587 
"""
d = {l["glosa"]: (l["monto_mclp"], l["monto_anterior_mclp"], l["cuenta_canonica"]) for l in P.parse_eeff_lineas([PAGINA_PORTADA, PAG_EF_2COL])}
check(d.get("Total pasivos circulantes") == (6543189, 10993332, "TOTAL_PASIVOS_CIRCULANTES") and d.get("TOTAL PASIVOS") == (30087806, 44120587, "TOTAL_PASIVOS_Y_PATRIMONIO")
      and d.get("Remuneraciones por pagar por auditoria externa")[0] == 14503, f"dos columnas en la misma línea + nota intermedia (EF): {d.get('TOTAL PASIVOS')}")
PAG_TRANSA = """PATRIMONIO SEPARADO BTRA 1-5
ACTIVOS
10.000
TOTAL  ACTIVOS 
429.477
465.919
PASIVOS
21.000
TOTAL PASIVOS CIRCULANTES
19.065.103
18.385.252
23.000
TOTAL EXCEDENTE ACUMULADO
(18.635.626)
(17.919.333)
23.000
TOTAL PASIVOS
429.477
465.919
"""
d = {l["glosa"]: l["cuenta_canonica"] for l in P.parse_eeff_lineas([PAGINA_PORTADA, PAG_TRANSA])}
check(d.get("TOTAL PASIVOS") == "TOTAL_PASIVOS_Y_PATRIMONIO" and d.get("TOTAL EXCEDENTE ACUMULADO") == "TOTAL_EXCEDENTES_ACUMULADOS", f"glosa prevalece sobre código FECU repetido (Transa 23.000): {d}")
PAG_SECURITY = """RAZON SOCIAL: SECURITIZADORA SECURITY S.A.
BALANCE DEL PATRIMONIO SEPARADO BSECS-5
A C T IVOS
11.010
Disponible
11.212
40.749
15.210
Otros activos circulantes
19.718
19.716
11.000
T OT A L A C T IVOS C IR C ULA N T ES
30.930
60.465
15.210
T OT A L A C T IVOS
30.930
60.465
"""
d = {l["glosa"]: l["cuenta_canonica"] for l in P.parse_eeff_lineas([PAGINA_PORTADA, PAG_SECURITY])}
check(d.get("T OT A L A C T IVOS") == "TOTAL_ACTIVOS" and d.get("T OT A L A C T IVOS C IR C ULA N T ES") == "TOTAL_ACTIVOS_CIRCULANTES", f"glosas con letras espaciadas (Security): {d}")
PAG_SUDAMERICANA = """SECURITIZADORA SUDAMERICANA S.A.
BALANCES GENERALES DEL PATRIMONIO SEPARADO N°2
ACTIVOS
Nota
31-12-2025
31-12-2024
11.010 Disponible
5
313.993
89.515
11.020 Valores negociables  
6
861.472
1.273.686
10.000 TOTAL ACTIVOS  
1.175.465
1.363.201
"""
d = {l["glosa"]: (l["codigo_fecu"], l["monto_mclp"], l["cuenta_canonica"]) for l in P.parse_eeff_lineas([PAGINA_PORTADA, PAG_SUDAMERICANA])}
check(d.get("Disponible") == ("11.010", 313993, "DISPONIBLE") and d.get("TOTAL ACTIVOS") == ("10.000", 1175465, "TOTAL_ACTIVOS"), f"código y glosa en la misma línea (Sudamericana): {d}")
PAG_NOTA7 = """EF SECURITIZADORA S.A.
NOTA 7 - ACTIVOS SECURITIZADOS
Concepto
Total de Activo
456
3.549.603
"""
r7 = P.derivar_resumen(P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_BALANCE_ACT, PAGINA_BALANCE_PAS, PAG_NOTA7]))
check(r7["total_activos_mclp"] != 456 and r7["cuadre_contable_ok"], "cuadro de nota ('Total de Activo' = nº de contratos) no pisa el total del balance")


# ---- flujo completo del paso ps sin red (HTTP y PDF simulados) ----
print("paso ps end-to-end (simulado)")
import tempfile, types, pandas as pd
class _FakeDoc:
    def __init__(self, pags): self.p = pags
    def __len__(self): return len(self.p)
    def __getitem__(self, i): return types.SimpleNamespace(get_text=lambda: self.p[i], get_images=lambda: [])
    def close(self): pass
sys.modules["fitz"] = types.SimpleNamespace(open=lambda stream, filetype: _FakeDoc([PAGINA_PORTADA, PAGINA_BALANCE_ACT, PAGINA_BALANCE_PAS, PAGINA_EXCEDENTES, PAGINA_EFECTIVO, PAGINA_MORA]))
P._listar_pdfs_ps = lambda op, sec, anio, mm: ("http://cmf/entidad", [("Patrimonios Separados - N° 12 al %s/%s" % (mm, anio), "http://cmf/pdf/%s%s" % (anio, mm))])
P.http_get = lambda *a, **k: b"%PDF-fake"
tmp = tempfile.mkdtemp(); P.OUT_DIR = tmp
secs = {"96765170": {"rut": "96765170", "rut_completo": "96765170-2", "razon_social": "TRANSA SECURITIZADORA S.A.", "estado_vigencia": "VIGENTE"}}
P.paso_ps(None, secs, 2024, 2024, ["09", "12"])
lin = pd.read_parquet(os.path.join(tmp, "patrimonios_separados_eeff_lineas.parquet"))
res = pd.read_parquet(os.path.join(tmp, "patrimonios_separados_balance_resumen.parquet"))
cob = pd.read_parquet(os.path.join(tmp, "patrimonios_separados_cobertura.parquet"))
nts = pd.read_parquet(os.path.join(tmp, "patrimonios_separados_notas_detalle.parquet"))
check(sorted(lin["periodo"].unique()) == ["2024-09", "2024-12"] and len(lin) == 2 * 23, f"líneas trimestrales: {len(lin)} filas")
check(cob["estado"].tolist() == ["ok", "ok"] and "paginas_ocr" in cob.columns and cob["paginas_ocr"].isna().all(), "cobertura ok sin OCR")

# ---- OCR: página de balance embebida como imagen (tesseract simulado) ----
print("ocr páginas imagen")
import subprocess as _sp, shutil as _sh
class _ImgDoc(_FakeDoc):
    def __getitem__(self, i):
        return types.SimpleNamespace(get_text=lambda: self.p[i], get_images=lambda: [("img",)] if i == 1 else [], get_drawings=lambda: [1] * 40 if i == 2 else [],
                                     get_pixmap=lambda dpi: types.SimpleNamespace(save=lambda f: open(f, "wb").write(b"png")))
_pags = [PAGINA_PORTADA, "EF SECURITIZADORA S.A.\nPATRIMONIO SEPARADO N° 7\n", "EF SECURITIZADORA S.A.\n", PAGINA_EXCEDENTES]
_ocr_txt = {1: PAGINA_BALANCE_ACT, 2: PAGINA_BALANCE_PAS}; _calls = []
def _fake_run(cmd, **k):
    _calls.append(cmd); n = len(_calls)
    return types.SimpleNamespace(returncode=0, stdout=_ocr_txt[1] if n == 1 else _ocr_txt[2])
_orig_run, _orig_which = _sp.run, _sh.which
_sp.run, _sh.which = _fake_run, (lambda x: "/usr/bin/tesseract")
pg2, hechos = P.ocr_paginas_imagen(_ImgDoc(_pags), _pags)
_sp.run, _sh.which = _orig_run, _orig_which
lin_ocr = P.parse_eeff_lineas(pg2); r_ocr = P.derivar_resumen(lin_ocr)
check(hechos == [2, 3] and len(_calls) == 2 and "-l" in _calls[0] and "spa" in _calls[0], f"OCR sólo en páginas sin cifras con imagen o tabla vectorial: {hechos}")
check(r_ocr["cuadre_contable_ok"] and r_ocr["total_activos_mclp"] == P.derivar_resumen(P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_BALANCE_ACT, PAGINA_BALANCE_PAS, PAGINA_EXCEDENTES]))["total_activos_mclp"], "balance leído desde OCR cuadra igual que el texto nativo")
_sh.which = lambda x: None
check(P.ocr_paginas_imagen(_ImgDoc(_pags), _pags) == (_pags, []), "sin tesseract → páginas sin cambios (no se inventa)")
_sh.which = _orig_which
check(len(res) == 2 and bool(res["cuadre_contable_ok"].all()) and res["rut_administradora"].iloc[0] == "96765170-2", "resumen: 2 balances, cuadran, RUT con DV")
check(set(["fuente_url", "metodo", "fecha_extraccion", "script_version", "pdf_sha256"]) <= set(lin.columns), "procedencia en líneas")
check(list(cob["estado"]) == ["ok", "ok"] and cob["lineas_eeff"].iloc[0] == 23, "cobertura registra ok + nº de líneas")
check(sorted(nts["periodo"].unique()) == ["2024-12"] and len(nts) == 6, "notas sólo en diciembre (2 efectivo + 4 mora)")
print(f"\n{len(fallos)} fallos"); sys.exit(1 if fallos else 0)
