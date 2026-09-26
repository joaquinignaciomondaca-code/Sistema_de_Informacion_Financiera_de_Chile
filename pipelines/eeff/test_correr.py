"""Si se corta, la próxima corrida sigue. Un fallo no borra lo ya leído."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff import parse_md
from pipelines.eeff.correr import correr
from pipelines.eeff.estado import Store

UNO = """rut: 1-9
razon_social: UNO
periodo: 2026-03
fecha_corte: 2026-03-31
tipo_eeff: Individual
fuente: test

## BALANCE
nombre|nota|monto_miles|comparativo_miles|clase
Efectivo y equivalentes al efectivo|4|1000|900|Activo
Total de activos||1000|900|Total
Total de pasivos||400|300|Total
Patrimonio total||600|600|Total

## RESULTADOS
nombre|nota|monto_miles|comparativo_miles|clase
Ganancia del periodo||10|9|Resultado

## NOTAS_INDICE
numero|titulo|pagina
4|Efectivo y equivalentes al efectivo|1
13|Préstamos que devengan intereses|2
20|Movimientos de patrimonio|3

## NOTA 4 Efectivo y equivalentes al efectivo
| Concepto | Saldo 31/12/2025 M$ | Saldo 31/03/2026 M$ |
| --- | --- | --- |
| Caja | 900 | 1.000 |
"""

DOS = """rut: 2-7
razon_social: DOS
periodo: 2026-03
fecha_corte: 2026-03-31
tipo_eeff: Individual
fuente: test

## BALANCE
nombre|nota|monto_miles|comparativo_miles|clase
Total de activos||50|40|Total
Total de pasivos||20|10|Total
Patrimonio total||30|30|Total

## RESULTADOS
nombre|nota|monto_miles|comparativo_miles|clase
Ganancia del periodo||1|1|Resultado

## NOTAS_INDICE
numero|titulo|pagina
1|Antecedentes de la Sociedad|1
"""


def _escribir(fuentes: Path):
    fuentes.mkdir(parents=True)
    (fuentes / "1-9_2026-03.md").write_text(UNO, encoding="utf-8")
    (fuentes / "2-7_2026-03.md").write_text(DOS, encoding="utf-8")


def test_reanuda_y_no_se_cae_con_un_fallo(tmp: Path):
    fuentes = tmp / "fuentes"
    _escribir(fuentes)
    store = Store(tmp / "estado")
    out = tmp / "out"
    original = parse_md.parse_documento

    def boom(text, meta):
        if meta.get("rut") == "2-7":
            raise RuntimeError("corte de prueba")
        return original(text, meta)

    parse_md.parse_documento = boom
    try:
        primero = correr(fuentes, store, out, publicar=True)
    finally:
        parse_md.parse_documento = original
    assert primero["ok"] == 1, primero
    assert primero["error"] == 1, primero
    efectivo = store.leer_todo()["nota_efectivo"]
    assert len(efectivo) == 1
    assert efectivo[0]["saldo_miles"] == 1000
    assert efectivo[0]["saldo_comparativo_miles"] == 900
    cobertura = {row["tabla"]: row for row in store.leer_todo()["cobertura"] if row["rut"] == "1-9"}
    assert cobertura["efectivo"]["estado"] == "leida"
    assert cobertura["efectivo"]["cuadre"] == "OK"
    assert cobertura["pasivos_financieros"]["estado"] == "en_indice_sin_tabla"
    assert cobertura["pasivos_financieros"]["titulo_nota"] == "Préstamos que devengan intereses"
    assert cobertura["patrimonio"]["titulo_nota"] == "Movimientos de patrimonio"
    assert cobertura["deudores"]["estado"] == "indice_incompleto"

    segundo = correr(fuentes, store, out)
    assert segundo["skip"] == 1, segundo
    assert segundo["ok"] == 1, segundo
    assert segundo["error"] == 0
    docs = {row["rut"]: row for row in store.leer_todo()["documentos"]}
    assert docs["1-9"]["estado_extraccion"] == "PDF_CON_NOTAS"
    assert docs["2-7"]["lineas_balance"] == 3
    nota_lineas = (out / "factoring_leasing_nota_lineas.json").read_text(encoding="utf-8")
    assert nota_lineas.strip() == "[]"
    print("OK reanuda, aísla el fallo y no publica nota_lineas")


def test_forzar_y_olvidar(tmp: Path):
    fuentes = tmp / "fuentes"
    _escribir(fuentes)
    store = Store(tmp / "estado")
    out = tmp / "out"
    correr(fuentes, store, out)
    (fuentes / "2-7_2026-03.md").unlink()
    correr(fuentes, store, out, olvidar_ausentes=True)
    ruts = {row["rut"] for row in store.leer_todo()["documentos"]}
    assert ruts == {"1-9"}, ruts
    print("OK olvidar ausentes no toca al que sigue en disco")


def test_no_marca_completa_una_caratula_o_un_resultado_que_no_suma(tmp: Path):
    fuentes = tmp / "fuentes"
    fuentes.mkdir(parents=True)
    (fuentes / "3-5_2026-03.md").write_text(
        """rut: 3-5
razon_social: CARA
periodo: 2026-03
fecha_corte: 2026-03-31
tipo_eeff: Individual
fuente: test

## BALANCE
nombre|nota|monto_miles|comparativo_miles|clase
Efectivo y equivalentes al efectivo|4|100|90|Activo
Deudores comerciales y otras cuentas por cobrar|5|200|180|Activo
Activos corrientes totales||400|300|Total
Total de activos||400|300|Total
Total de pasivos||150|100|Total
Patrimonio total||250|200|Total

## RESULTADOS
nombre|nota|monto_miles|comparativo_miles|clase
Ingresos de actividades ordinarias||10|9|Ingreso
Ganancia bruta||10|9|Resultado
Ganancia del periodo||10|9|Resultado

## NOTAS_INDICE
numero|titulo|pagina
1|Antecedentes|1
""",
        encoding="utf-8",
    )
    (fuentes / "4-3_2026-03.md").write_text(
        """rut: 4-3
razon_social: RESULTADO
periodo: 2026-03
fecha_corte: 2026-03-31
tipo_eeff: Individual
fuente: test

## BALANCE
nombre|nota|monto_miles|comparativo_miles|clase
Efectivo y equivalentes al efectivo|4|50|40|Activo
Total de activos||50|40|Total
Total de pasivos||20|10|Total
Patrimonio total||30|30|Total

## RESULTADOS
nombre|nota|monto_miles|comparativo_miles|clase
Ingresos de actividades ordinarias||10|8|Ingreso
Ganancia bruta||10|8|Resultado
Gastos de administración||-3|-1|Gasto
Ganancia antes de impuestos||4|5|Resultado

## NOTAS_INDICE
numero|titulo|pagina
1|Antecedentes|1
""",
        encoding="utf-8",
    )
    store = Store(tmp / "estado")
    correr(fuentes, store, tmp / "out", publicar=False)
    docs = {row["rut"]: row for row in store.leer_todo()["documentos"]}
    assert docs["3-5"]["estado_extraccion"] == "PDF_PARCIAL", docs["3-5"]
    assert docs["3-5"]["cuadre_balance"] == "OK"
    assert docs["3-5"]["cuadre_caratula"] == "FALTAN_LINEAS"
    assert "Activos corrientes totales" in docs["3-5"]["hueco"]
    assert docs["4-3"]["estado_extraccion"] == "PDF_PARCIAL", docs["4-3"]
    assert docs["4-3"]["cuadre_caratula"] == "OK"
    assert docs["4-3"]["cuadre_resultados"] == "FALTAN_LINEAS"
    assert "comparativo" in docs["4-3"]["hueco"]
    print("OK una carátula o un resultado que no suma no queda como leído completo")


def test_lock(tmp: Path):
    store = Store(tmp / "estado")
    lock = store.root / "LOCK"
    store.root.mkdir(parents=True)
    lock.write_text('{"pid": 999999}', encoding="utf-8")
    with store.lock():
        assert not lock.exists() or "999999" not in lock.read_text(encoding="utf-8")
    print("OK el lock de un pid muerto no bloquea la reanudación")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        test_reanuda_y_no_se_cae_con_un_fallo(Path(tmp) / "a")
    with tempfile.TemporaryDirectory() as tmp:
        test_forzar_y_olvidar(Path(tmp) / "b")
    with tempfile.TemporaryDirectory() as tmp:
        test_no_marca_completa_una_caratula_o_un_resultado_que_no_suma(Path(tmp) / "d")
    with tempfile.TemporaryDirectory() as tmp:
        test_lock(Path(tmp) / "c")
