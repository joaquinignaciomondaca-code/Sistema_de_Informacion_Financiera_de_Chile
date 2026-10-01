"""Pruebas de `corredoras_bolsa/scripts/actualizar_eeff.py` con Excel FECU sintéticos.

El extractor no se puede probar contra la CMF desde un entorno de desarrollo (la red del sandbox
no la alcanza), así que aquí se arman Excel con el mismo formato —una fila por sociedad, una
columna por cuenta FECU «11.01.00Nombre»— y se comprueba lo que de verdad importa: qué cuentas
se publican, qué se rechaza de la fuente y, sobre todo, que la compuerta contable **no deje pasar
a ciegas** un trimestre cuando cambian los códigos de los totales.

Sin red, sin tocar `docs/`: todo va a carpetas temporales y con el reloj fijado.
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

import openpyxl
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from pipelines.auto import cuadratura  # noqa: E402

SPEC = importlib.util.spec_from_file_location("actualizar_eeff", RAIZ / "corredoras_bolsa/scripts/actualizar_eeff.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

ACTIVOS = [f"11.{i:02d}.00" for i in range(1, 21)] + [f"12.{i:02d}.00" for i in range(1, 11)]
TOTALES = ["10.00.00", "20.00.00", "21.00.00", "22.00.00"]
RESULTADOS = ["30.00.00", "30.10.00", "30.20.00", "30.50.00", "30.70.00", "31.00.00", "32.00.00"]
FLUJO = ["50.00.00", "51.00.00"]


def rut(i: int) -> tuple[str, str]:
    """RUT con dígito verificador válido: (texto con puntos, cuerpo)."""
    cuerpo = str(76100000 + i)
    d = m.dv(cuerpo)
    return f"{cuerpo[:2]}.{cuerpo[2:5]}.{cuerpo[5:]}-{d}", cuerpo


def excel(periodo: str, malos: int = 0, sociedades: int = 25, ciego: bool = False,
          fecha: str | None = None, tipo_rut_malo: bool = False, valor_raro: str | None = None,
          columnas_de_mas: bool = True) -> bytes:
    """Excel FECU de un trimestre. `malos` sociedades con el patrimonio descuadrado;
    `ciego` renombra los códigos de los totales (el caso «cambió el plan de cuentas»)."""
    codigos = ACTIVOS + (["10.00.01", "20.00.01", "21.00.01", "22.00.01"] if ciego else TOTALES) + RESULTADOS + FLUJO
    if columnas_de_mas:
        codigos = codigos + ["30.00.00"]            # el Excel repite 30.00.00 al inicio de los integrales
    wb = openpyxl.Workbook()
    ws = wb.active
    estados = ["", "", ""] + ["Estado de situación financiera"] + [""] * (len(ACTIVOS) + 3) \
        + ["Estado de resultados"] + [""] * 5 + ["Estado de otros resultados integrales"] + [""] * 4
    ws.append(estados[:3 + len(codigos)])
    ws.append(["", "", "", "Activos"] + [""] * (len(codigos) - 1))
    ws.append(["Fecha", "RUT", "Razón social"] + [f"{c}Cuenta{c.replace('.', '')}" for c in codigos])
    esperado = fecha or f"{periodo[5:]} / {periodo[:4]}"
    for i in range(sociedades):
        texto, cuerpo = rut(i)
        if tipo_rut_malo and i == 0:
            texto = texto[:-1] + ("0" if texto[-1] != "0" else "1")
        fila = [esperado, texto, f"CORREDORA {i} S.A."]
        for c in codigos:
            if c in ("10.00.00", "10.00.01"):
                v = 1000
            elif c in ("21.00.00", "21.00.01"):
                v = 400
            elif c in ("22.00.00", "22.00.01"):
                v = 100 if i < malos else 600
            elif c in ("20.00.00", "20.00.01"):
                v = 1000
            elif c == "30.00.00":
                v = 50
            else:
                v = 1
            if valor_raro is not None and i == 0 and c == "11.01.00":
                v = valor_raro
            fila.append(v)
        ws.append(fila)
    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


class LecturaDelExcelTest(unittest.TestCase):
    def test_publica_balance_y_resultados_y_deja_fuera_el_flujo(self):
        d = m.leer_excel(excel("2010-12"), "2010-12", 1, {"76100000"})
        cods_bal = {f["codigo_fecu"] for f in d["balance"]}
        cods_res = {f["codigo_fecu"] for f in d["resultados"]}
        self.assertTrue({"10.00.00", "21.00.00", "22.00.00", "11.01.00"} <= cods_bal)
        self.assertTrue({"30.00.00", "31.00.00", "32.00.00"} <= cods_res)
        self.assertFalse(any(c.startswith("5") for c in cods_bal | cods_res), "el flujo de efectivo no se publica")
        self.assertEqual(len(d["balance"]), 25 * 34)        # 20+10 de activos + 4 totales, por sociedad
        self.assertEqual(len(d["resultados"]), 25 * 7)

    def test_30_00_00_repetido_se_toma_una_sola_vez(self):
        d = m.leer_excel(excel("2010-12", sociedades=1), "2010-12", 1, set())
        self.assertEqual(sum(f["codigo_fecu"] == "30.00.00" for f in d["resultados"]), 1)

    def test_fila_de_ejemplo_completa(self):
        f = next(x for x in m.leer_excel(excel("2010-12", sociedades=2), "2010-12", 1, {"76100000"})["balance"]
                 if x["codigo_fecu"] == "10.00.00" and x["rut"] == "76100000")
        self.assertEqual(f["periodo"], "2010-12")
        self.assertEqual(f["valor_miles_clp"], 1000)
        self.assertEqual(f["tipo_intermediario"], "corredor de bolsa")
        self.assertTrue(f["en_lista_entidades"])
        self.assertEqual(f["rut_dv"], rut(0)[0].replace(".", ""))
        tipo2 = m.leer_excel(excel("2010-12", sociedades=1), "2010-12", 2, set())["balance"][0]
        self.assertEqual(tipo2["tipo_intermediario"], "agente de valores")
        self.assertFalse(tipo2["en_lista_entidades"])

    def test_rechaza_lo_que_no_es_un_excel(self):
        with self.assertRaisesRegex(m.ErrorFuente, "sin Excel"):
            m.leer_excel(b"<html>trimestre no publicado</html>", "2010-12", 1, set())

    def test_rechaza_una_fecha_que_no_es_la_pedida(self):
        with self.assertRaisesRegex(m.ErrorFuente, "fecha"):
            m.leer_excel(excel("2010-12", fecha="03 / 2011"), "2010-12", 1, set())

    def test_rechaza_un_rut_con_digito_verificador_invalido(self):
        with self.assertRaisesRegex(m.ErrorFuente, "dígito verificador"):
            m.leer_excel(excel("2010-12", tipo_rut_malo=True), "2010-12", 1, set())

    def test_rechaza_un_valor_no_entero(self):
        with self.assertRaisesRegex(m.ErrorFuente, "valor no entero"):
            m.leer_excel(excel("2010-12", valor_raro="12,5"), "2010-12", 1, set())

    def test_rechaza_un_excel_con_pocas_cuentas_o_sin_sociedades(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["", "", "", "Estado de situación financiera"])
        ws.append(["", "", "", "Activos"])
        ws.append(["Fecha", "RUT", "Razón social", "10.00.00Total", "21.00.00Total"])
        b = io.BytesIO(); wb.save(b)
        with self.assertRaisesRegex(m.ErrorFuente, "solo 2 cuentas FECU"):
            m.leer_excel(b.getvalue(), "2010-12", 1, set())
        with self.assertRaisesRegex(m.ErrorFuente, "sin sociedades"):
            m.leer_excel(excel("2010-12", sociedades=0), "2010-12", 1, set())

    def test_arregla_el_utf8_leido_como_latin1_y_separa_palabras(self):
        self.assertEqual(m.arreglar("RazÃ³n social"), "Razón social")
        self.assertEqual(m.arreglar(None), "")
        self.assertEqual(m.separar_palabras("EfectivoyEfectivoEquivalente"), "Efectivoy Efectivo Equivalente")
        self.assertEqual(m.separar_palabras("Activos"), "Activos")

    def test_nombres_y_niveles_del_informe_html(self):
        html = ("<html>{c:[{v:'Activos'}]} {v:'   11.01.00 Efectivo y efectivo equivalente'} "
                "{v:'         11.01.10 Caja'}</html>").encode()
        reales = (m._get, dict(m.ETIQUETAS))
        m._get = lambda url: html
        try:
            mapa = m.nombres_cuentas("2026-03")
        finally:
            m._get = reales[0]
            m.ETIQUETAS.clear(); m.ETIQUETAS.update(reales[1])
        self.assertEqual(mapa["11.01.00"], ("Efectivo y efectivo equivalente", 1))
        self.assertEqual(mapa["11.01.10"], ("Caja", 2))

    def test_calendario_de_trimestres(self):
        self.assertEqual(m.trimestres("2010-12", "2011-06"), ["2010-12", "2011-03", "2011-06"])
        self.assertEqual(m.ultimo_trimestre(date(2011, 7, 1)), "2011-06")
        self.assertEqual(m.ultimo_trimestre(date(2011, 1, 10)), "2010-12")
        self.assertFalse(m.cerrado("2011-06", date(2011, 7, 1)))
        self.assertTrue(m.cerrado("2010-12", date(2011, 7, 1)))      # 181 días


class CompuertaContableTest(unittest.TestCase):
    def test_sin_cobertura_la_compuerta_antigua_no_frenaba_nada(self):
        """Lo que arregla `balances_totales`: con los totales ilegibles, `verificados` es 0 y sin el
        total de balances la compuerta no tenía de qué desconfiar."""
        self.assertFalse(cuadratura.debe_detener(0, []))
        self.assertTrue(cuadratura.debe_detener(0, [], 25))


class CorridaCompletaTest(unittest.TestCase):
    """`main` sin red: Excel servidos desde memoria, salida y control en carpetas temporales."""

    def _correr(self, tmp, excel_por_periodo, hoy=date(2011, 4, 20), pedidas=None):
        tmp = Path(tmp)
        (tmp / "salida").mkdir(exist_ok=True)
        maestro = tmp / "salida" / "corredoras_bolsa_maestro.json"
        if not maestro.exists():
            maestro.write_text(json.dumps([{"rut": rut(0)[1]}]))

        def get(url):
            if "xls=n" in url:
                return b"<html></html>"
            aaaa = re.search(r"anno1=(\d{4})", url).group(1)
            mm = re.search(r"mes1=(\d{2})", url).group(1)
            periodo = f"{aaaa}-{mm}"
            if "tiposociedad=2" in url:
                return b"<html>sin agentes</html>"
            if pedidas is not None:
                pedidas.append(periodo)
            return excel_por_periodo(periodo)

        nombres = ("_get", "SALIDA", "CONTROL", "RAIZ", "_hoy")
        reales = {n: getattr(m, n) for n in nombres}
        m._get = get
        m.SALIDA = tmp / "salida"
        m.CONTROL = tmp / "salida" / "manifest.json"
        m.RAIZ = tmp                                # sin data_manifest.json: no toca el del repo
        m._hoy = lambda: hoy
        try:
            with redirect_stdout(io.StringIO()):
                codigo = m.main(["--minutos", "5"])
            control = json.loads(m.CONTROL.read_text()) if m.CONTROL.exists() else {"periodos": {}}
            return codigo, control
        finally:
            for n, v in reales.items():
                setattr(m, n, v)

    @staticmethod
    def _parquet(tmp, tabla, anio):
        return Path(tmp) / "salida" / f"corredoras_bolsa_{tabla}" / f"{anio}.parquet"

    def test_publica_los_trimestres_que_cuadran(self):
        with tempfile.TemporaryDirectory() as tmp:
            codigo, control = self._correr(tmp, lambda p: excel(p))
            self.assertEqual(codigo, 0)
            self.assertEqual(sorted(control["periodos"]), ["2010-12", "2011-03"])
            per = control["periodos"]["2011-03"]
            self.assertEqual((per["sociedades"], per["balances_verificados"], per["balances_totales"]), (25, 25, 25))
            self.assertEqual(pq.read_table(self._parquet(tmp, "balance", 2011)).num_rows, 25 * 34)
            self.assertEqual(pq.read_table(self._parquet(tmp, "resultados", 2010)).num_rows, 25 * 7)
            man = json.loads((Path(tmp) / "salida" / "corredoras_bolsa_balance" / "manifest.json").read_text())
            self.assertEqual(man["periodos"], ["2010-12", "2011-03"])

    def test_si_cambian_los_codigos_de_los_totales_no_se_publica_a_ciegas(self):
        with tempfile.TemporaryDirectory() as tmp:
            codigo, control = self._correr(tmp, lambda p: excel(p, ciego=True))
            self.assertEqual(control["periodos"], {})
            self.assertFalse(self._parquet(tmp, "balance", 2011).exists())
            self.assertEqual(codigo, 1, "un trimestre abierto que no pasa la compuerta deja la corrida en rojo")

    def test_una_falla_en_bloque_no_se_publica(self):
        with tempfile.TemporaryDirectory() as tmp:
            codigo, control = self._correr(tmp, lambda p: excel(p, malos=10))
            self.assertEqual(control["periodos"], {})
            self.assertEqual(codigo, 1)

    def test_un_descuadre_aislado_se_publica_con_aviso(self):
        with tempfile.TemporaryDirectory() as tmp:
            codigo, control = self._correr(tmp, lambda p: excel(p, malos=1))
            self.assertEqual(codigo, 0)
            avisos = control["periodos"]["2011-03"]["avisos"]
            self.assertTrue(any("balance no cuadra" in a for a in avisos), avisos)

    def test_un_cierre_defectuoso_ya_cerrado_avisa_pero_no_deja_la_corrida_en_rojo(self):
        """2010-12 lleva más de 150 días: es una fuente histórica defectuosa, no una falla nueva."""
        with tempfile.TemporaryDirectory() as tmp:
            codigo, control = self._correr(
                tmp, lambda p: excel(p, ciego=(p == "2010-12")), hoy=date(2011, 7, 1))
            self.assertEqual(codigo, 0)
            self.assertNotIn("2010-12", control["periodos"])
            self.assertEqual(sorted(control["periodos"]), ["2011-03", "2011-06"])

    def test_el_cierre_publicado_no_se_vuelve_a_pedir(self):
        with tempfile.TemporaryDirectory() as tmp:
            pedidas: list[str] = []
            self._correr(tmp, lambda p: excel(p), hoy=date(2011, 7, 1), pedidas=pedidas)
            self.assertEqual(sorted(set(pedidas)), ["2010-12", "2011-03", "2011-06"])
            pedidas.clear()
            self._correr(tmp, lambda p: excel(p), hoy=date(2011, 7, 1), pedidas=pedidas)
            self.assertNotIn("2010-12", pedidas)                  # cerrado: no se relee
            self.assertIn("2011-06", pedidas)                     # abierto: sí, por las presentaciones tardías

    def test_una_relectura_con_menos_sociedades_conserva_lo_publicado(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._correr(tmp, lambda p: excel(p, sociedades=25))
            antes = pq.read_table(self._parquet(tmp, "balance", 2011)).num_rows
            self._correr(tmp, lambda p: excel(p, sociedades=20))
            self.assertEqual(pq.read_table(self._parquet(tmp, "balance", 2011)).num_rows, antes)


if __name__ == "__main__":
    unittest.main()
