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

print("eeff líneas — layout glosas (Volcom)")
lin = P.parse_eeff_lineas([PAGINA_PORTADA, PAGINA_BALANCE_ACT, PAGINA_BALANCE_PAS, PAGINA_EXCEDENTES])
v = {l["cuenta_canonica"]: l for l in lin if l["cuenta_canonica"]}
check(v["ACTIVO_SECURITIZADO_CP"]["monto_mclp"] == 4335870 and v["ACTIVO_SECURITIZADO_CP"]["nota"] == "9", "nota 9 separada del monto (v1 leía 94.335.870)")
check(v["TOTAL_ACTIVOS"]["monto_mclp"] == 101478787 and v["TOTAL_ACTIVOS"]["monto_anterior_mclp"] == 65294160, "total activos año actual y anterior")
check(v["TOTAL_PASIVOS_Y_PATRIMONIO"]["monto_mclp"] == 101478787, "'Total Pasivos' mapeado a 20.000")
check(v["OTROS_PASIVOS_CIRCULANTES"]["monto_mclp"] == 6360033, "'Otros acreedores (corto plazo)' → 21.200")
check(v["EXCEDENTE_DEL_EJERCICIO"]["estado"] == "BALANCE" and v["EXCEDENTE_NETO_DEL_PERIODO"]["estado"] == "EXCEDENTES", "misma glosa, distinto estado")
check(v["GASTO_REMUNERACIONES_ADMINISTRACION"]["monto_mclp"] == -400000, "paréntesis → negativo")
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
check(P.parse_fecu_gestora(FECU_HTML.replace("Ganancia (pérdida)", "Otra cosa"))["ganancia_perdida_ejercicio_m_clp"] is None, "ganancia ausente → NULL (no 0)")

print("utilidades")
check(P.rut_completo("96765170") == "96765170-2" and P.rut_completo("76965774") == "76965774-6", "módulo 11")
check(P.parse_num("(1.234,5)") == -1234.5 and P.parse_num("-") is None and P.parse_num("abc") is None, "parse_num")


# ---- flujo completo del paso ps sin red (HTTP y PDF simulados) ----
print("paso ps end-to-end (simulado)")
import tempfile, types, pandas as pd
class _FakeDoc:
    def __init__(self, pags): self.p = pags
    def __len__(self): return len(self.p)
    def __getitem__(self, i): return types.SimpleNamespace(get_text=lambda: self.p[i])
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
check(len(res) == 2 and bool(res["cuadre_contable_ok"].all()) and res["rut_administradora"].iloc[0] == "96765170-2", "resumen: 2 balances, cuadran, RUT con DV")
check(set(["fuente_url", "metodo", "fecha_extraccion", "script_version", "pdf_sha256"]) <= set(lin.columns), "procedencia en líneas")
check(list(cob["estado"]) == ["ok", "ok"] and cob["lineas_eeff"].iloc[0] == 23, "cobertura registra ok + nº de líneas")
check(sorted(nts["periodo"].unique()) == ["2024-12"] and len(nts) == 6, "notas sólo en diciembre (2 efectivo + 4 mora)")
print(f"\n{len(fallos)} fallos"); sys.exit(1 if fallos else 0)
