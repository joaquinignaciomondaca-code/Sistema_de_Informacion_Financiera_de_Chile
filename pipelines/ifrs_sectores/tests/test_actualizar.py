"""Pruebas de `pipelines/ifrs_sectores/actualizar.py` con TXT sintéticos.

El extractor no se puede probar contra la CMF desde un entorno de desarrollo (la red del
sandbox no la alcanza), así que aquí se construyen archivos con el mismo formato y se
comprueba lo que de verdad importa: a qué sector va cada sociedad, cómo se cuentan el
orden y la repetición, qué pasa con un importe que no es entero, y —sobre todo— que una
relectura peor **no** pueda borrar lo ya publicado.

Cada caso es un TXT de una línea por cuenta, con los campos en el orden de la CMF:
periodo;rut;nombre;I|C;moneda;cuenta;valor;taxonomia;estado
"""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

import pyarrow.parquet as pq  # noqa: E402

from pipelines.ifrs_sectores import actualizar  # noqa: E402
from pipelines.auto import cuadratura  # noqa: E402


def txt(lineas: list[str]) -> bytes:
    return ("\n".join(lineas) + "\n").encode("utf-8")


def fila(periodo="202503", rut="76034728", nombre="HMC S.A. ADMINISTRADORA GENERAL DE FONDOS",
         tipo="I", moneda="CLP", cuenta="Total de activos", valor="1000", tax="TAX CI",
         estado="ESF C/NC") -> str:
    return ";".join([periodo, rut, nombre, tipo, moneda, cuenta, valor, tax, estado])


# Balances y resultados mínimos y cuadrados de dos AGF.
def sociedad(rut, nombre, activos=1000, pasivos=400, patrimonio=600, ganancia=100,
             periodo="202503", tipo="I", prefijo_estado="ESF C/NC"):
    return [
        fila(periodo, rut, nombre, tipo, "CLP", "Total de activos", str(activos), estado=prefijo_estado),
        fila(periodo, rut, nombre, tipo, "CLP", "Total de pasivos", str(pasivos), estado=prefijo_estado),
        fila(periodo, rut, nombre, tipo, "CLP", "Patrimonio total", str(patrimonio), estado=prefijo_estado),
        fila(periodo, rut, nombre, tipo, "CLP", "Ingresos de actividades ordinarias", "500", estado="ERFG"),
        fila(periodo, rut, nombre, tipo, "CLP", "Costo de ventas", "300", estado="ERFG"),
        fila(periodo, rut, nombre, tipo, "CLP", "Ganancia bruta", "200", estado="ERFG"),
        fila(periodo, rut, nombre, tipo, "CLP", "Ganancia (pérdida)", str(ganancia), estado="ERFG"),
        fila(periodo, rut, nombre, tipo, "CLP", "Ganancia (pérdida)", str(ganancia), estado="ERI"),
        fila(periodo, rut, nombre, tipo, "CLP", "Resultado integral total", str(ganancia), estado="ERI"),
    ]


def relleno(cuantas=55, periodo="202503"):
    """Sociedades de otros giros: el extractor exige al menos 50 en el archivo."""
    return [fila(periodo=periodo, rut=str(90000000 + i), nombre=f"EMPRESA {i} SPA",
                 cuenta="Total de activos", valor="1", estado="ESF C/NC") for i in range(cuantas)]


def leer(lineas, periodo="202503", listas=None):
    """Lee un TXT sintético completo con el relleno que la guarda de cobertura exige."""
    return actualizar.leer_archivo(txt(lineas + relleno(periodo=periodo)), periodo, listas or LISTAS)


LISTAS_COMPLETAS = {s: {} for s in list(actualizar.SECTORES) + list(actualizar.SOLO_LISTA)}
LISTAS_COMPLETAS["agf"] = {"76034728": "HMC AGF"}


def _datos_agf(ruts):
    """Filas ya parseadas de las AGF indicadas (3 de balance y 6 de resultados por sociedad)."""
    lineas = []
    for r in ruts:
        lineas += sociedad(r, f"AGF {r}")
    datos, _est, _a = leer(lineas)
    return datos["agf"]


LISTAS = {
    "agf": {"76034728": "HMC AGF"},
    "securitizadoras": {"96948880": "BCI Securitizadora"},
    "cajas_compensacion": {"81826800": "CCAF Los Andes"},
    "factoring_leasing": {"96655860": "Factoring Security"},
}


class LeerArchivoTest(unittest.TestCase):
    def test_reparte_por_estado_y_cuenta_orden_y_repeticion(self):
        lineas = [
            fila(cuenta="Efectivo", valor="10"),
            fila(cuenta="Total de activos", valor="20"),
            fila(cuenta="Ganancia (pérdida)", valor="7", estado="ERFG"),
            fila(cuenta="Ganancia (pérdida)", valor="7", estado="ERI"),
        ]
        datos, est, avisos = leer(lineas)
        bal = datos["agf"]["balance"]
        self.assertEqual([f["cuenta"] for f in bal], ["Efectivo", "Total de activos"])
        self.assertEqual([f["orden"] for f in bal], [1, 2])
        # La misma glosa en dos estados distintos no es una repetición: son contextos distintos.
        er = [f for f in datos["agf"]["resultados"] if f["estado_financiero"] == "ERFG"]
        eri = [f for f in datos["agf"]["resultados"] if f["estado_financiero"] == "ERI"]
        self.assertEqual([f["repeticion"] for f in er], [1])
        self.assertEqual([f["repeticion"] for f in eri], [1])
        self.assertGreaterEqual(est["sociedades"], 50)  # incluye el relleno de otros giros
        self.assertEqual(avisos, [])

    def test_repeticion_cuenta_la_segunda_aparicion_de_la_misma_cuenta(self):
        lineas = [fila(cuenta="Ganancia (pérdida)", valor="7", estado="ERFG")] * 2
        datos, _est, _a = leer(lineas)
        self.assertEqual([f["repeticion"] for f in datos["agf"]["resultados"]], [1, 2])

    def test_orden_se_cuenta_por_taxonomia(self):
        """Dos taxonomías del mismo estado no intercalan sus cuentas."""
        lineas = [
            fila(cuenta="Efectivo", valor="1", tax="TAX CI"),
            fila(cuenta="Total de activos", valor="2", tax="TAX HB"),
        ]
        datos, _est, _a = leer(lineas)
        self.assertEqual([(f["taxonomia"], f["orden"]) for f in datos["agf"]["balance"]],
                         [("TAX CI", 1), ("TAX HB", 1)])

    def test_valor_no_entero_queda_nulo_con_su_texto(self):
        lineas = [fila(cuenta="Ganancia por acción", valor="14.5821", estado="ERFG")]
        datos, _est, _a = leer(lineas)
        f = datos["agf"]["resultados"][0]
        self.assertIsNone(f["valor"])
        self.assertEqual(f["valor_no_numerico"], "14.5821")

    def test_sector_por_rut_y_sector_por_nombre(self):
        lineas = sociedad("76034728", "HMC AGF")                        # por RUT
        lineas += sociedad("76111111", "NUEVA AGF S.A. ADMINISTRADORA GENERAL DE FONDOS")
        datos, _est, _a = leer(lineas)
        self.assertEqual(len(datos["agf"]["balance"]), 6)
        marcas = {(f["rut"], f["en_lista_entidades"]) for f in datos["agf"]["balance"]}
        self.assertEqual(marcas, {("76034728", True), ("76111111", False)})

    def test_sociedad_de_otro_giro_no_entra_y_si_es_factoring_se_candidatiza(self):
        lineas = sociedad("76000000", "BANCO DE CHILE")
        lineas += sociedad("76999999", "FACTORING NUEVO S.A.")
        datos, est, _a = leer(lineas)
        self.assertEqual(sum(len(datos[s]["balance"]) for s in actualizar.SECTORES), 0)
        self.assertEqual([c["rut"] for c in est["solo_lista_fuera"]["factoring_leasing"]], ["76999999-K"])

    def test_fluir_de_efectivo_no_se_publica(self):
        lineas = [fila(cuenta="Efectivo al inicio", valor="5", estado="EFMI")]
        datos, _est, _a = leer(lineas)
        self.assertEqual(datos["agf"]["balance"], [])
        self.assertEqual(datos["agf"]["resultados"], [])

    def test_html_de_error_no_pasa_como_txt(self):
        with self.assertRaises(actualizar.ErrorFuente):
            actualizar.leer_archivo(b"<html><body>accion no permitida</body></html>", "202503", LISTAS)

    def test_archivo_con_pocas_sociedades_se_rechaza(self):
        with self.assertRaises(actualizar.ErrorContenido):
            actualizar.leer_archivo(txt(sociedad("76034728", "HMC AGF")), "202503", LISTAS)

    def test_sin_filas_del_trimestre_pedido_se_rechaza(self):
        with self.assertRaises(actualizar.ErrorContenido):
            actualizar.leer_archivo(txt([fila(periodo="202412")] * 60), "202503", LISTAS)


class CuadraturaAntesDePublicarTest(unittest.TestCase):
    def test_balances_y_resultados_de_una_sociedad_se_verifican(self):
        lineas = sociedad("76034728", "HMC AGF")
        datos, _est, _a = leer(lineas)
        v, malos = cuadratura.verificar_ifrs(datos["agf"]["balance"])
        self.assertEqual((v, malos), (1, []))
        vr, mr = cuadratura.verificar_resultados_ifrs(datos["agf"]["resultados"])
        self.assertEqual(mr, [])
        self.assertEqual(vr, 2)  # ERI = ER, y ganancia bruta = ingresos − costo

    def test_resultado_integral_que_no_arrastra_la_ganancia_se_detecta(self):
        lineas = sociedad("76034728", "HMC AGF", ganancia=100)
        lineas = [l.replace(";100;TAX CI;ERI", ";999;TAX CI;ERI") for l in lineas]
        datos, _est, _a = leer(lineas)
        _vr, mr = cuadratura.verificar_resultados_ifrs(datos["agf"]["resultados"])
        self.assertEqual(len(mr), 1)
        self.assertIn("ERI", mr[0])

    def test_compuerta_se_enciende_si_las_glosas_cambian(self):
        """Si los totales dejan de reconocerse, la compuerta avisa en vez de callar."""
        lineas = []
        for i in range(30):
            rut = f"{76000000 + i}"
            lineas += sociedad(rut, "HMC AGF", activos=1000, pasivos=400, patrimonio=600)
        datos, _est, _a = leer(lineas)
        for f in datos["agf"]["balance"]:
            f["cuenta"] = f["cuenta"].replace("Total de activos", "Activo total consolidado")
        totales = cuadratura.contar_grupos(datos["agf"]["balance"], cuadratura.CLAVES_IFRS)
        v, _malos = cuadratura.verificar_ifrs(datos["agf"]["balance"])
        self.assertEqual(totales, 30)
        self.assertEqual(v, 0)
        self.assertTrue(cuadratura.debe_detener(v, [], balances_totales=totales))


class GuardasTest(unittest.TestCase):
    def test_periodo_anterior_y_quien_dejo_de_informar(self):
        control = {"periodos": {
            "202412": {"ruts": {"agf": ["1", "2"]}},
            "202503": {"ruts": {"agf": ["1"]}},
        }}
        self.assertEqual(actualizar.periodo_anterior(control, "202503"), "202412")
        self.assertEqual(actualizar.dejaron_de_informar(control, "202503", "agf", {"1"}), ["2"])
        self.assertEqual(actualizar.dejaron_de_informar(control, "202503", "agf", {"1", "2"}), [])
        self.assertIsNone(actualizar.periodo_anterior(control, "202412"))

    def test_cerrado_a_150_dias(self):
        from datetime import date
        self.assertFalse(actualizar.cerrado("202606", date(2026, 10, 1)))   # 93 días
        self.assertTrue(actualizar.cerrado("202606", date(2026, 12, 1)))    # 154 días

    def test_relectura_parcial_no_borra_el_trimestre(self):
        """F8: si la relectura pierde las filas de una tabla, el Parquet no se toca.

        La guarda antigua comparaba solo la cantidad de entidades; como la sociedad seguía
        apareciendo en resultados, `escribir(sec, "balance", periodo, [])` borraba el balance
        del trimestre publicado. Aquí se comprueba que eso ya no pasa.
        """
        with TemporaryDirectory() as tmp:
            real = actualizar.ruta_tabla
            actualizar.ruta_tabla = lambda sec, tabla: Path(tmp) / sec / tabla
            try:
                listas = {"agf": {"76034728": "HMC AGF", "76111111": "NUEVA AGF"}}
                control = {"periodos": {}}
                completo = _datos_agf(["76034728", "76111111"])
                datos = {s: {"balance": [], "resultados": []} for s in actualizar.SECTORES}
                datos["agf"] = completo
                resumen, ruts, avisos = actualizar.publicar_sector(
                    "agf", datos, {}, listas, control, "202503")
                self.assertEqual(avisos, [])
                self.assertEqual(resumen["filas"], {"balance": 6, "resultados": 12})
                self.assertEqual(ruts, ["76034728", "76111111"])
                ruta = Path(tmp) / "agf" / "balance" / "2025.parquet"
                self.assertTrue(ruta.exists())
                antes = (ruta.stat().st_mtime_ns, len(pq.read_table(ruta)))

                # Segunda corrida: el trimestre se vuelve a leer, pero el balance cae entero
                # en avisos (cambio de glosas) y solo llegan los resultados.
                control["periodos"]["202503"] = {"sectores": {"agf": resumen}, "ruts": {"agf": ruts}}
                datos["agf"] = {"balance": [], "resultados": completo["resultados"]}
                resumen2, ruts2, avisos2 = actualizar.publicar_sector(
                    "agf", datos, {"agf": resumen}, listas, control, "202503")
                self.assertIn("pierde filas en balance", avisos2[0])
                self.assertEqual(resumen2, resumen)          # se conserva lo publicado
                self.assertEqual(ruts2, ruts)                # nadie aparece como «dejó de informar»
                self.assertEqual((ruta.stat().st_mtime_ns, len(pq.read_table(ruta))), antes)

                # Con el balance de vuelta, sí se vuelve a escribir.
                datos["agf"] = completo
                _r, _u, avisos3 = actualizar.publicar_sector(
                    "agf", datos, {"agf": resumen}, listas, control, "202503")
                self.assertEqual(avisos3, [])
                self.assertEqual(len(pq.read_table(ruta)), 6)
            finally:
                actualizar.ruta_tabla = real

    def test_relectura_con_menos_entidades_se_conserva(self):
        control = {"periodos": {"202503": {"ruts": {"agf": ["76034728", "76111111"]}}}}
        previo = {"agf": {"entidades": 2, "filas": {"balance": 6, "resultados": 12}}}
        datos = {s: {"balance": [], "resultados": []} for s in actualizar.SECTORES}
        datos["agf"] = _datos_agf(["76034728"])
        resumen, ruts, avisos = actualizar.publicar_sector(
            "agf", datos, previo, {"agf": {}}, control, "202503")
        self.assertEqual(resumen, previo["agf"])
        self.assertIn("trae 1 entidades (antes 2)", avisos[0])
        self.assertEqual(ruts, ["76034728", "76111111"])

    def test_indice_de_trimestre_redondea(self):
        """El orden de los trimestres debe ser reversible (un '-06' mal cortado no avisa)."""
        for p in ("2010-06", "2024-12", "2025-03", "2026-06"):
            self.assertEqual(actualizar._periodo(actualizar._indice(p)), p)
        self.assertGreater(actualizar._indice("2025-03"), actualizar._indice("2024-12"))
        self.assertEqual(actualizar._periodo(actualizar._indice("2026-06") - 8), "2024-06")

    def test_periodos_del_indice(self):
        html = b'<html><a href="ver_archivo.php?inicio=202503&amp;termino=202503">x</a>' \
               b'<a href="ver_archivo.php?inicio=202403&amp;termino=202412">a</a></html>'
        periodos, anual = actualizar.periodos_indice(html)
        self.assertIn("202503", periodos)
        self.assertEqual(anual.get("202409"), ("202403", "202412"))
        self.assertNotIn("202405", periodos)  # solo cierres trimestrales


class CoberturaTest(unittest.TestCase):
    """Oportunidad 6: la cobertura se calcula de lo publicado y se publica."""

    def _publicar(self, tmp, filas):
        """Escribe un Parquet mínimo de balance con (periodo, rut, razon_social)."""
        import pyarrow as pa
        ruta = Path(tmp) / "agf" / "balance"
        ruta.mkdir(parents=True, exist_ok=True)
        tabla = pa.table({"periodo": [f[0] for f in filas], "rut": [f[1] for f in filas],
                          "razon_social": [f[2] for f in filas]})
        pq.write_table(tabla, ruta / "2025.parquet")

    def test_quien_falta_y_quien_dejo_de_informar(self):
        with TemporaryDirectory() as tmp:
            real = actualizar.ruta_tabla
            actualizar.ruta_tabla = lambda sec, tabla: Path(tmp) / sec / tabla
            try:
                # 111 informa siempre; 222 se corta en 2025-09; 333 no aparece nunca.
                self._publicar(tmp, [("2025-06", "111", "PRESENTE AGF"), ("2025-06", "222", "SE VA AGF"),
                                     ("2025-09", "111", "PRESENTE AGF"), ("2025-09", "222", "SE VA AGF"),
                                     ("2025-12", "111", "PRESENTE AGF")])
                listas = {"agf": {"111": "PRESENTE", "222": "SE VA", "333": "NUNCA"}}
                cob = actualizar.cobertura(listas)["agf"]
                self.assertEqual(cob["ultimo_periodo"], "2025-12")
                self.assertEqual((cob["entidades"], cob["lista_total"]), (1, 3))
                self.assertEqual([d["rut"] for d in cob["dejaron_de_informar"]], ["222"])
                self.assertEqual(cob["dejaron_de_informar"][0]["ultimo_periodo"], "2025-09")
                # 222 y 333 faltan: la primera con historial, la segunda sin ningún trimestre.
                self.assertEqual(cob["sin_datos_total"], 2)
                self.assertEqual([(f["rut"], f["ultimo_periodo"]) for f in cob["sin_datos"]],
                                 [("222", "2025-09"), ("333", None)])
                texto = actualizar.texto_cobertura(cob)
                self.assertIn("informan 1 de las 3", texto)
                self.assertIn("SE VA AGF (último 2025-09)", texto)
            finally:
                actualizar.ruta_tabla = real

    def test_ausencia_vieja_no_es_novedad(self):
        """Alguien que se fue hace más de 8 trimestres sigue en sin_datos, no en novedades."""
        with TemporaryDirectory() as tmp:
            real = actualizar.ruta_tabla
            actualizar.ruta_tabla = lambda sec, tabla: Path(tmp) / sec / tabla
            try:
                self._publicar(tmp, [("2020-06", "222", "ANTIGUA AGF"), ("2025-12", "111", "PRESENTE AGF")])
                cob = actualizar.cobertura({"agf": {"111": "PRESENTE", "222": "ANTIGUA"}})["agf"]
                self.assertEqual(cob["dejaron_de_informar"], [])
                self.assertEqual([f["rut"] for f in cob["sin_datos"]], ["222"])
                self.assertNotIn("Dejaron de informar", actualizar.texto_cobertura(cob))
            finally:
                actualizar.ruta_tabla = real

    def test_se_escribe_en_el_diccionario_de_la_web_y_no_repite(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "data_dictionary.js"
            entrada = {"id": "agf_balance", "name": "agf.balance", "descripcion": "d",
                       "columnas": [{"name": "periodo"}]}
            ruta.write_text("const DATA_DICTIONARY = [\n  " + json.dumps(entrada, ensure_ascii=False)
                            + ",\n  {\"id\": \"otra\", \"name\": \"o\"},\n];\n", encoding="utf-8")
            real = actualizar.RUTA_DICCIONARIO
            actualizar.RUTA_DICCIONARIO = ruta
            try:
                cob = {"agf": {"ultimo_periodo": "2025-12", "entidades": 1, "lista_total": 2,
                               "sin_datos": [{"rut": "2", "razon_social": "FALTA AGF",
                                              "ultimo_periodo": None}],
                               "sin_datos_total": 1, "dejaron_de_informar": []}}
                self.assertTrue(actualizar.escribir_cobertura_web(cob))
                texto = ruta.read_text(encoding="utf-8")
                self.assertIn("Cobertura 2025-12: informan 1 de las 2", texto)
                self.assertIn("FALTA AGF", texto)
                # La ficha de otro sector queda intacta y la segunda corrida no reescribe.
                self.assertIn('{"id": "otra", "name": "o"},', texto)
                self.assertFalse(actualizar.escribir_cobertura_web(cob))
            finally:
                actualizar.RUTA_DICCIONARIO = real


class CorridaCompletaTest(unittest.TestCase):
    """La corrida completa, sin red: se sirve el índice y el TXT desde memoria.

    Es la única forma de revisar el pegamento (`main`): lectura, cuadratura, guardas,
    escritura de Parquet, control y manifiestos. Todo va a carpetas temporales.
    """

    def _correr(self, tmp, argv, veces=1):
        indice = (b'<html><a href="ver_archivo.php?inicio=202606&amp;termino=202606">202606</a></html>')
        raw = txt(sociedad("76034728", "HMC AGF", periodo="202606")
                  + sociedad("76111111", "OTRA AGF S.A. ADMINISTRADORA GENERAL DE FONDOS", periodo="202606")
                  + relleno(55, periodo="202606"))
        control = Path(tmp) / "control.json"
        diccionario = Path(tmp) / "data_dictionary.js"
        diccionario.write_text('const DATA_DICTIONARY = [\n];\n', encoding="utf-8")
        reales = {n: getattr(actualizar, n) for n in
                  ("_get", "CONTROL", "ruta_tabla", "RUTA_DICCIONARIO", "cargar_listas",
                   "actualizar_data_manifest", "agregar_altas")}
        actualizar._get = lambda url: indice if "estadisticas_ifrs.php" in url else raw
        actualizar.CONTROL = control
        actualizar.ruta_tabla = lambda sec, tabla: Path(tmp) / "salida" / sec / tabla
        actualizar.RUTA_DICCIONARIO = diccionario
        actualizar.cargar_listas = lambda: LISTAS_COMPLETAS
        actualizar.actualizar_data_manifest = lambda control: None   # no toca el repo
        actualizar.agregar_altas = lambda fuera, periodo: 0          # ni las listas de entidades
        try:
            with redirect_stdout(io.StringIO()):
                salida = [actualizar.main(argv) for _ in range(veces)]
            return salida[-1], json.loads(control.read_text(encoding="utf-8"))
        finally:
            for n, v in reales.items():
                setattr(actualizar, n, v)

    def test_corrida_publica_y_la_segunda_no_repite(self):
        with TemporaryDirectory() as tmp:
            codigo, control = self._correr(tmp, ["--max-periodos", "1"], veces=2)
            self.assertEqual(codigo, 0)
            per = control["periodos"]["202606"]
            self.assertEqual(per["sectores"]["agf"]["entidades"], 2)
            self.assertEqual(per["sectores"]["agf"]["filas"], {"balance": 6, "resultados": 12})
            self.assertEqual(per["balances_descuadrados"], 0)
            self.assertFalse(per["cerrado"])          # 202606 sigue abierto a 150 días
            self.assertEqual(len(pq.read_table(Path(tmp) / "salida" / "agf" / "balance" / "2026.parquet")), 6)
            self.assertTrue((Path(tmp) / "salida" / "agf" / "balance" / "manifest.json").exists())

    def test_relectura_parcial_en_una_corrida_no_borra(self):
        """F8 de punta a punta: si el TXT pierde el balance, el Parquet se queda como está."""
        with TemporaryDirectory() as tmp:
            self._correr(tmp, ["--max-periodos", "1"])
            ruta = Path(tmp) / "salida" / "agf" / "balance" / "2026.parquet"
            antes = len(pq.read_table(ruta))

            indice = b'<html><a href="ver_archivo.php?inicio=202606&amp;termino=202606">x</a></html>'
            # Mismas sociedades, pero sin líneas de balance: la guarda por tabla decide.
            solo_resultados = txt(
                [l for l in sociedad("76034728", "HMC AGF", periodo="202606")
                 + sociedad("76111111", "OTRA AGF S.A. ADMINISTRADORA GENERAL DE FONDOS", periodo="202606")
                 if not l.endswith(";ESF C/NC")] + relleno(55, periodo="202606"))
            reales = {n: getattr(actualizar, n) for n in
                      ("_get", "CONTROL", "ruta_tabla", "RUTA_DICCIONARIO", "cargar_listas",
                       "actualizar_data_manifest", "agregar_altas")}
            actualizar._get = lambda url: indice if "estadisticas_ifrs.php" in url else solo_resultados
            actualizar.CONTROL = Path(tmp) / "control.json"
            actualizar.ruta_tabla = lambda sec, tabla: Path(tmp) / "salida" / sec / tabla
            actualizar.RUTA_DICCIONARIO = Path(tmp) / "data_dictionary.js"
            actualizar.cargar_listas = lambda: LISTAS_COMPLETAS
            actualizar.actualizar_data_manifest = lambda control: None
            actualizar.agregar_altas = lambda fuera, periodo: 0
            try:
                with redirect_stdout(io.StringIO()):
                    actualizar.main(["--max-periodos", "1"])
            finally:
                for n, v in reales.items():
                    setattr(actualizar, n, v)
            self.assertEqual(len(pq.read_table(ruta)), antes)
            avisos = json.loads((Path(tmp) / "control.json").read_text())["periodos"]["202606"]["avisos"]
            self.assertTrue(any("pierde filas en balance" in a for a in avisos), avisos)


if __name__ == "__main__":
    unittest.main()
