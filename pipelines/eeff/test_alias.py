"""La llave es el nombre, no el número. Incluye los títulos que ya hicieron tropezar."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff.alias import clasificar_nota, cuenta_cara, fold
from pipelines.eeff.parse_md import cargar_md

FUENTES = ROOT / "factoring_leasing" / "eeff_fuentes"
OCHO = {
    "efectivo", "deudores", "pasivos_financieros", "cuentas_por_pagar",
    "relacionadas", "impuestos", "patrimonio", "ppe",
}


def test_tropiezos():
    assert clasificar_nota("Préstamos que devengan intereses")["tabla"] == "pasivos_financieros"
    assert clasificar_nota("Movimientos de patrimonio")["tabla"] == "patrimonio"
    assert clasificar_nota("Capital y reservas")["tabla"] == "patrimonio"
    assert clasificar_nota("Patrimonio")["tabla"] == "patrimonio"
    assert clasificar_nota("Transacciones con entidades relacionadas")["tabla"] == "relacionadas"
    assert clasificar_nota("Deudores comerciales y otras cuentas por cobrar")["tabla"] == "deudores"
    assert clasificar_nota("Cuentas comerciales por cobrar y otras cuentas por cobrar")["tabla"] == "deudores"
    valor = clasificar_nota("Activos financieros a valor razonable con cambios en patrimonio")
    assert valor["tabla"] == ""
    assert valor["familia"] != "patrimonio"
    assert clasificar_nota("Política de provisiones de deudores comerciales")["tabla"] == ""
    assert clasificar_nota("Otros pasivos no financieros")["tabla"] == ""
    assert clasificar_nota("Otros pasivos financieros corrientes")["tabla"] == "pasivos_financieros"
    assert clasificar_nota("Otros pasivos financieros no corrientes")["tabla"] == "pasivos_financieros"
    assert clasificar_nota("Vencimiento de activos y pasivos financieros")["tabla"] == ""
    assert clasificar_nota("Cuentas por pagar a entidades relacionadas")["tabla"] == "relacionadas"
    assert clasificar_nota("Cuentas por pagar comerciales y otras cuentas por pagar")["tabla"] == "cuentas_por_pagar"
    assert clasificar_nota("Gastos por arrendamientos")["tabla"] == ""
    assert clasificar_nota("Propiedades, planta y equipo")["tabla"] == "ppe"
    assert clasificar_nota("Propiedad planta y equipos")["tabla"] == "ppe"
    assert clasificar_nota("Efectivo y equivalente al efectivo")["tabla"] == "efectivo"
    assert clasificar_nota("Ingresos y costos")["tabla"] == ""
    print("OK alias de los tropiezos")


def test_caratula():
    assert cuenta_cara("Deudores comerciales y otras cuentas por cobrar, corrientes") == "deudores"
    assert cuenta_cara("Deudores comerciales y otras cuentas por cobrar, no corrientes") == "deudores_no_corriente"
    assert cuenta_cara("Total pasivos corrientes") == "total_pasivos_corrientes"
    assert cuenta_cara("Total de pasivos") == "total_pasivos"
    assert cuenta_cara("Total de patrimonio y pasivos") == "total_pasivo_patrimonio"
    assert cuenta_cara("Ganancia (pérdida) del periodo", "resultado") == "ganancia_periodo"
    assert cuenta_cara("Ganancia antes de impuestos", "resultado") == ""
    assert cuenta_cara("Ingresos", "resultado") == "ingresos"
    assert cuenta_cara("Ingresos financieros", "resultado") == ""
    assert cuenta_cara("Otros pasivos financieros no corrientes") == "pasivos_financieros_no_corriente"
    assert cuenta_cara("Costos de ventas", "resultado") == "costo_ventas"
    print("OK cuentas de carátula")


def test_indices_de_marzo():
    faltas = []
    for path in sorted(FUENTES.glob("*_2026-03.md")):
        meta, text = cargar_md(path)
        inicio = text.split("## NOTAS_INDICE", 1)[-1].split("## NOTA", 1)[0]
        tablas = set()
        for line in inicio.splitlines():
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or not cells[0].isdigit():
                continue
            titulo = cells[1]
            clas = clasificar_nota(titulo)
            blob = fold(titulo)
            if "valor razonable" in blob or "valores razonables" in blob:
                assert clas["tabla"] not in {"patrimonio", "pasivos_financieros"}, titulo
            if "vencimiento" in blob:
                assert clas["tabla"] != "pasivos_financieros", titulo
            if "arrendamiento" in blob:
                assert clas["tabla"] not in {"ppe", "pasivos_financieros"}, titulo
            if "politica de provisiones" in blob:
                assert clas["tabla"] != "deudores", titulo
            if clas["tabla"]:
                tablas.add(clas["tabla"])
        if path.name.startswith("96861280-8"):
            assert tablas == {"efectivo", "deudores"}, tablas
            continue
        if tablas != OCHO:
            faltas.append((path.name, sorted(OCHO - tablas)))
    assert not faltas, faltas
    print("OK las ocho familias en los índices de marzo, salvo el índice cortado de Eurocapital")


if __name__ == "__main__":
    test_tropiezos()
    test_caratula()
    test_indices_de_marzo()
