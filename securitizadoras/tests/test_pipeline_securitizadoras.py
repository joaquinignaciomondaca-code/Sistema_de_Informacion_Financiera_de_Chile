"""
Pruebas sin red del pipeline v2 de securitizadoras / patrimonios separados.
Ejecutar: python securitizadoras/tests/test_pipeline_securitizadoras.py   (exit 1 si falla)
Los textos simulan la salida de pymupdf (una celda por línea) de un EEFF anual de PS y una FECU IFRS HTML de gestora.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import pipeline_securitizadoras as P

PAGINA_PORTADA = "TRANSA SECURITIZADORA S.A.\nPATRIMONIO SEPARADO N° 12\nInscripción Registro de Valores N° 345\nEstados Financieros al 31 de diciembre de 2024\n"
PAGINA_BALANCE = """BALANCE GENERAL
Al 31 de diciembre de 2024 y 2023
ACTIVOS
Nota
2024
M$
2023
M$
Disponible
5
1.250
980
Valores negociables
6
3.400
2.100
Activo securitizado corto plazo
7
12.000
11.500
Total activo circulante
16.650
14.580
Activo securitizado largo plazo
7
83.350
90.420
TOTAL ACTIVOS
100.000
105.000
PASIVOS
Obligaciones por títulos de deuda corto plazo
8
9.000
8.500
Total pasivo circulante
9.500
9.000
Obligaciones por títulos de deuda largo plazo
8
88.000
94.000
Total pasivo largo plazo
88.000
94.000
Excedentes acumulados
2.500
2.000
TOTAL PASIVOS Y PATRIMONIO
100.000
105.000
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

print("balance"); bal = P.parse_balance_ps([PAGINA_PORTADA, PAGINA_BALANCE], 2024)
check(len(bal) == 2 and bal[0]["periodo"] == "2024-12" and bal[1]["periodo"] == "2023-12", "dos columnas de año")
check(bal[0]["total_activos_mclp"] == 100000 and bal[1]["total_activos_mclp"] == 105000, "total activos por columna")
check(bal[0]["disponible_mclp"] == 1250 and bal[0]["deuda_bonos_largo_plazo_mclp"] == 88000, "cuentas de detalle (salta nº de nota)")
check(bal[0]["cuadre_contable_ok"] and bal[1]["cuadre_contable_ok"], "cuadre real activos = pasivos+patrimonio")
bal2 = P.parse_balance_ps(["BALANCE\nDISPONIBLE\n10\nTOTAL ACTIVOS\n(texto)\n"], 2024)
check(bal2 == [] or bal2[0]["total_activos_mclp"] is None, "sin total → NULL, nunca se copia el otro total")

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

print(f"\n{len(fallos)} fallos"); sys.exit(1 if fallos else 0)
