"""Pruebas de `ffmm/scripts/valor_cuota.py`.

Cada caso reproduce una rareza **medida** en las 99.853 líneas de la sección B.3 de la Circular
1835 que el repositorio tiene publicadas (`docs/outputs/seguros/fondos_mutuos/`): series distintas
del mismo fondo con nemotécnicos distintos, disagreement entre aseguradoras, carteras tan chicas
que el redondeo del archivo domina la identidad, letras de serie vacías y la codificación rota de
los nombres de fondos mutuos. Los importes son los reales del fondo 8806 y del 8248.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

SPEC = importlib.util.spec_from_file_location("valor_cuota", RAIZ / "ffmm/scripts/valor_cuota.py")
VC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VC)


def linea(periodo, run, serie, nemot, unidades, cu, final_m, rut="76015592", moneda="$$"):
    """Una línea de la sección B.3, con `final_m` en miles como lo publica la CMF."""
    return {"periodo": periodo, "run_fondo": run, "serie": serie, "nemotecnico": nemot,
            "unidad_monetaria": moneda, "unidades": unidades, "valor_cuota": cu,
            "valor_final_m_clp": final_m, "rut_aseguradora": rut}


def marco(*lineas) -> pd.DataFrame:
    return pd.DataFrame(list(lineas))


class TestIdentidad(unittest.TestCase):
    """C1. La tolerancia mixta está calibrada sobre los datos reales, no elegida a ojo."""

    def test_cuadra_exacto(self):
        self.assertTrue(VC.identidad_ok(97277.797, 1394.8885, 135692))

    def test_redondeo_del_archivo_en_carteras_chicas(self):
        """La mediana de las líneas que fallan es de 4 miles: ahí manda el redondeo, no el error."""
        self.assertTrue(VC.identidad_ok(5.0, 1007.4, 5))
        self.assertTrue(VC.identidad_ok(0.8267, 1770.2542, 1))

    def test_falla_un_desvio_real(self):
        self.assertFalse(VC.identidad_ok(1000.0, 1000.0, 2_000_000))   # mil veces la cuenta
        self.assertFalse(VC.identidad_ok(0.0, 0.0, 5_000_000))         # sin unidades pero con valor

    def test_la_tolerancia_absoluta_manda_en_lo_chico_y_la_relativa_en_lo_grande(self):
        # 0,4 % de desviación en 1.000 millones: la relativa lo acepta.
        grande = 1_000_000_000.0
        self.assertTrue(VC.identidad_ok(1.0, grande, grande / 1000 * 0.996))
        # 40 % de desviación en 10.000: ni la absoluta ni la relativa lo aceptan.
        self.assertFalse(VC.identidad_ok(1.0, 10_000.0, 6_000.0))


class TestConsenso(unittest.TestCase):
    """C2. Cuando las aseguradoras no coinciden no se publica un número."""

    def test_coincidencia_exacta(self):
        valor, estado = VC._consenso([1042.3925, 1042.3925])
        self.assertEqual(estado, "ok")
        self.assertEqual(valor, 1042.3925)

    def test_diferencia_de_redondeo_se_acepta(self):
        """El 88,6 % de los desacuerdos reales son redondeo del archivo, no valores distintos."""
        valor, estado = VC._consenso([413613.0264, 413613.0266])
        self.assertEqual(estado, "ok")

    def test_diferencia_real_se_marca(self):
        valor, estado = VC._consenso([782975.2279, 787453.2544])
        self.assertEqual(estado, "discrepancia_cu")
        self.assertIsNone(valor, "no se promedia ni se elige la primera")

    def test_sin_datos(self):
        self.assertEqual(VC._consenso([]), (None, "sin_datos"))

    def test_un_cero_no_es_un_valor(self):
        """C3. La identidad no alcanza: 0 × 0 = 0 × 1.000, así que el cero la cierra y saldría
        publicado. En los datos reales son 94 líneas de 5 fondos que sí tienen valores normales."""
        valor, estado = VC._consenso([0.0, 0.0])
        self.assertEqual(estado, "valor_cuota_cero")
        self.assertIsNone(valor)

    def test_un_negativo_tampoco(self):
        self.assertEqual(VC._consenso([-12.5]), (None, "valor_cuota_cero"))


class TestGrano(unittest.TestCase):
    """El grano es (período, fondo, nemotécnico, serie). Antes era (período, fondo, serie) y
    producía 271 falsos desacuerdos: una sola aseguradora con varias líneas del mismo fondo."""

    def test_una_aseguradora_con_tres_series_no_es_un_desacuerdo(self):
        """El 8806 en 2016-11: series B, G y H reportadas por dos aseguradoras distintas."""
        df = marco(
            linea("2016-11", "8806", "B", "CFMSECCORB", 97277.797, 1394.8885, 135692, rut="76015592"),
            linea("2016-11", "8806", "G", "CFMSECCORG", 5003828.0829, 1042.3925, 5215953, rut="99301000"),
            linea("2016-11", "8806", "H", "CFMSECCORH", 1004.1948, 1027.558, 1032, rut="99301000"),
        )
        tabla, avisos = VC.agregar(df)
        self.assertEqual(len(tabla), 3, "son tres series distintas, no un desacuerdo")
        self.assertEqual(avisos, [])
        self.assertEqual(set(tabla["valor_cuota"]), {1394.8885, 1042.3925, 1027.558})

    def test_sin_serie_se_separa_por_nemotecnico(self):
        df = marco(
            linea("2016-11", "8170", "", "CFMA", 100.0, 751.9841, 75),
            linea("2016-11", "8170", "", "CFMB", 100.0, 1936.3576, 193),
            linea("2016-11", "8170", "", "CFMC", 100.0, 2622.2771, 262),
        )
        tabla, avisos = VC.agregar(df)
        self.assertEqual(len(tabla), 3)
        self.assertEqual(avisos, [], "sin nemotécnico no hay forma de saber si es la misma serie")

    def test_el_nemotecnico_manda_sobre_la_serie(self):
        """Mismo nemotécnico y series distintas: es un cambio de etiqueta en la fuente."""
        df = marco(
            linea("2016-11", "8806", "B", "CFMSECCORB", 100.0, 1000.0, 100),
            linea("2016-11", "8806", "", "CFMSECCORB", 100.0, 1000.0, 100),
        )
        tabla, _ = VC.agregar(df)
        self.assertEqual(len(tabla), 2, "la serie es parte de la clave, como el nemotécnico")


class TestCompuertas(unittest.TestCase):
    def test_consenso_entre_aseguradoras(self):
        df = marco(
            linea("2017-02", "8248", "UNICA", "CFMBCHCDFU", 1000.0, 787453.2544, 787453,
                  rut="76015592"),
            linea("2017-02", "8248", "UNICA", "CFMBCHCDFU", 2000.0, 787453.2555, 1574907,
                  rut="99301000"),
        )
        tabla, avisos = VC.agregar(df)
        self.assertEqual(tabla["estado"].tolist(), ["ok"])
        self.assertEqual(avisos, [])
        self.assertEqual(tabla["aseguradoras_reportantes"].tolist(), [2])

    def test_discrepancia_entre_aseguradoras(self):
        df = marco(
            linea("2017-02", "8248", "UNICA", "CFMBCHCDFU", 1000.0, 782975.2279, 782975),
            linea("2017-02", "8248", "UNICA", "CFMBCHCDFU", 2000.0, 787453.2544, 1574907,
                  rut="99301000"),
        )
        tabla, avisos = VC.agregar(df)
        self.assertEqual(tabla["estado"].tolist(), ["discrepancia_cu"])
        self.assertIsNone(tabla["valor_cuota"].iloc[0], "la fila se publica sin el número, no con uno elegido")
        self.assertEqual(avisos[0]["origen"], "varias_aseguradoras")
        self.assertEqual(avisos[0]["aseguradoras"], 2)

    def test_identidad_falla(self):
        """Una sola línea que no cierra con la identidad no se puede confirmar de ninguna manera."""
        df = marco(linea("2016-12", "8257", "01", "CFMBCIDCHC", 8233.3801, 813310.3158, 669629))
        tabla, avisos = VC.agregar(df)
        self.assertEqual(tabla["estado"].tolist(), ["identidad_falla"])
        self.assertIsNone(tabla["valor_cuota"].iloc[0])
        self.assertEqual(avisos[0]["origen"], "una_aseguradora_varias_lineas")

    def test_una_linea_mala_no_contamina_una_buena(self):
        """Si una de las dos aseguradoras cierra la identidad, esa es la que se puede publicar."""
        df = marco(
            linea("2026-01", "8011", "A", "CFMX", 1000.0, 5000.0, 5000, rut="76015592"),
            # 900 × 9.000 = 8.100.000 pero el archivo declara 1.000: la identidad no cierra.
            linea("2026-01", "8011", "A", "CFMX", 900.0, 9000.0, 1, rut="99301000"),
        )
        tabla, avisos = VC.agregar(df)
        self.assertEqual(tabla["estado"].tolist(), ["ok"])
        self.assertEqual(tabla["valor_cuota"].iloc[0], 5000.0)
        self.assertEqual(avisos, [])


class TestAgregados(unittest.TestCase):
    def test_suma_unidades_y_patrimonio(self):
        df = marco(
            linea("2026-01", "8011", "A", "CFMX", 1000.0, 5000.0, 5000, rut="76015592"),
            linea("2026-01", "8011", "A", "CFMX", 250.0, 5000.0, 1250, rut="99301000"),
        )
        tabla, _ = VC.agregar(df)
        self.assertEqual(tabla["unidades_aseguradoras"].iloc[0], 1250.0)
        self.assertEqual(tabla["patrimonio_aseguradoras_m"].iloc[0], 6250.0)

    def test_patrimonio_se_publica_aunque_el_valor_cuota_no(self):
        """Son hechos distintos: lo que la aseguradora declara tener no depende del consenso."""
        df = marco(
            linea("2026-01", "8011", "A", "CFMX", 1000.0, 5000.0, 5000, rut="76015592"),
            linea("2026-01", "8011", "A", "CFMX", 1.0, 1.0, 999, rut="99301000"),
        )
        tabla, _ = VC.agregar(df)
        self.assertEqual(tabla["patrimonio_aseguradoras_m"].iloc[0], 5999.0)
        self.assertEqual(tabla["unidades_aseguradoras"].iloc[0], 1001.0)

    def test_monedas_distintas_quedan_declaradas(self):
        df = marco(
            linea("2026-01", "8011", "A", "CFMX", 1000.0, 5000.0, 5000, moneda="$$"),
            linea("2026-01", "8011", "A", "CFMX", 10.0, 5000.0, 50, rut="99301000", moneda="PROM"),
        )
        tabla, _ = VC.agregar(df)
        self.assertEqual(tabla["unidad_monetaria"].iloc[0], "$$|PROM", "no se elige una moneda")


class TestCodificacion(unittest.TestCase):
    """206 de los 1.543 nombres del universo de fondos mutuos llegaron con el UTF-8 leído como
    latin-1. Se repara invirtiendo la decodificación; lo que no cuadra se deja como estaba."""

    def test_repara(self):
        self.assertEqual(VC.reparar_mojibake("FONDO MUTUO BCI ESTRATEGIA UF HASTA 3 AÃ\x91OS"),
                         "FONDO MUTUO BCI ESTRATEGIA UF HASTA 3 AÑOS")
        self.assertEqual(VC.reparar_mojibake("FONDO MUTUO BANCHILE INVERSIÃ\x93N USA"),
                         "FONDO MUTUO BANCHILE INVERSIÓN USA")

    def test_no_toca_lo_que_ya_esta_bien(self):
        self.assertEqual(VC.reparar_mojibake("FONDO MUTUO CAPITALISA ACCIONARIO"),
                         "FONDO MUTUO CAPITALISA ACCIONARIO")
        self.assertIsNone(VC.reparar_mojibake(None))

    def test_lo_ya_perdido_se_declara_en_vez_de_pasarse(self):
        """«DEPÃ¿SITO» decodifica sin error a «DEPÿSITO»: una cadena distinta y equivocada que
        aparenta estar reparada. Por eso la reparación se marca, no se da por buena."""
        self.assertEqual(VC.reparar_mojibake("DEPÃ¿SITO PLUS G"), "DEPÿSITO PLUS G")
        self.assertTrue(VC.reparado_con_huella("DEPÃ¿SITO PLUS G", "DEPÿSITO PLUS G"))
        self.assertFalse(VC.reparado_con_huella("INVERSIÃ\x93N", "INVERSIÓN"))

    def test_doble_corrupcion_no_se_arregla(self):
        """Con la corrupción en dos capas, invertir una vez deja rastro y se devuelve el original."""
        self.assertEqual(VC.reparar_mojibake("INVERSIÃ\x83Ã\x93N"), "INVERSIÃ\x83Ã\x93N")


class TestClasificacion(unittest.TestCase):
    def test_un_run_en_los_dos_padrones_manda_el_de_inversion(self):
        """Los 22 RUN en ambos son fondos de inversión duplicados en el universo de mutuos, con
        el nombre con la codificación rota. El maestro de inversión trae el tipo y el nombre limpio."""
        ffmm = {"9030": {"nombre_fondo": "FONDO DE INVERSIÃ\x93N BANCHILE EUROPE EQ"}}
        fi = {"9030": {"nombre_fondo": "FONDO DE INVERSIÓN BANCHILE EUROPE EQU", "tipo_entidad": "FIRES"}}
        sector, ficha = VC.clasificar("9030", ffmm, fi)
        self.assertEqual(sector, "fi")
        self.assertEqual(ficha["nombre_fondo"], "FONDO DE INVERSIÓN BANCHILE EUROPE EQU")

    def test_solo_mutuos(self):
        self.assertEqual(VC.clasificar("8011", {"8011": {}}, {})[0], "ffmm")

    def test_sin_padron(self):
        sector, ficha = VC.clasificar("2597", {}, {})
        self.assertEqual(sector, "sin_maestro")
        self.assertEqual(ficha, {})


class TestPropiedades(unittest.TestCase):
    """La agregación no puede inventar ni perder grupos: se toma la fuente completa de un año."""

    @classmethod
    def setUpClass(cls):
        anio = "2026"
        ruta = VC.ORIGEN_SEGUROS / f"{anio}.parquet"
        if not ruta.exists():
            raise unittest.SkipTest("no hayParquet de seguros publicado en este entorno")
        cls.fuente = VC.leer_fuente(ruta)
        cls.tabla, cls.avisos = VC.agregar(cls.fuente)

    def test_una_fila_por_grupo_de_la_fuente(self):
        esperados = set()
        for p, r, n, s in zip(self.fuente["periodo"], self.fuente["run_fondo"],
                              self.fuente["nemotecnico"], self.fuente["serie"]):
            esperados.add((p, str(r), n or "", s or ""))
        self.assertEqual(len(self.tabla), len(esperados), "no se duplica ni se pierde ningún grupo")

    def test_todo_aviso_corresponde_a_una_fila_sin_valor(self):
        sin_valor = self.tabla[self.tabla["valor_cuota"].isna()]
        self.assertEqual(len(sin_valor), len(self.avisos))
        self.assertTrue((sin_valor["estado"] != "ok").all())
        self.assertTrue((self.tabla[self.tabla["estado"] == "ok"]["valor_cuota"].notna()).all())

    def test_todo_valor_publicado_pasa_la_identidad(self):
        """Cada número publicado tiene que provenir de una línea que cerraba con la identidad.

        Se recorre grupo por grupo: lo que se publica es el consenso de las líneas que sí
        cerraban, y esa es justamente la propiedad que hay que medir sobre el año completo.
        """
        # Ojo: en una columna float64 de pandas, un valor ausente es `NaN`, no `None`, y
        # `NaN is not None` es True. El filtro tiene que ser `notna`, o entra como publicado un
        # valor que el publicador dejó deliberadamente en blanco.
        publicados = {(r["periodo"], str(r["run_fondo"]), r["nemotecnico"], r["serie"]): r["valor_cuota"]
                      for r in self.tabla.to_dict("records") if pd.notna(r["valor_cuota"])}
        self.assertTrue(publicados, "el año de prueba debe traer valores")

        # La clave tiene que ser la misma que arma `agregar`, y `agregar` llena los nulos: en la
        # prueba hay que hacerlo igual o se comparan grupos distintos (NaN es verdadero en Python).
        def texto(v):
            return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)

        lineas: dict[tuple, list[tuple[float, float, float]]] = {}
        for p, run, nem, serie, u, cu, fin in zip(self.fuente["periodo"], self.fuente["run_fondo"],
                                                  self.fuente["nemotecnico"], self.fuente["serie"],
                                                  self.fuente["unidades"], self.fuente["valor_cuota"],
                                                  self.fuente["valor_final_m_clp"]):
            lineas.setdefault((p, str(run), texto(nem), texto(serie)), []).append((u, cu, fin))

        for clave, valor in publicados.items():
            propias = lineas[clave]
            cerradas = [cu for u, cu, fin in propias if VC.identidad_ok(u, cu, fin)]
            self.assertTrue(cerradas, f"{clave}: se publicó un valor sin ninguna línea que cierre la identidad")
            for cu in cerradas:
                escala = max(abs(cu), abs(valor))
                desvio = 0.0 if escala == 0 else abs(cu - valor) / escala
                self.assertLessEqual(desvio, VC.IDENTIDAD_REL,
                                     f"{clave}: se publicó {valor} y había una línea que decía {cu}")


class TestEsquema(unittest.TestCase):
    def test_el_esquema_no_deriva_del_dataframe(self):
        self.assertEqual([f.name for f in VC.ESQUEMA][:4],
                         ["periodo", "run_fondo", "run_fondo_dv", "serie"])
        self.assertEqual(VC.ESQUEMA.field("valor_cuota").type, "double")
        self.assertTrue(VC.ESQUEMA.field("valor_cuota").nullable, "un valor sin confirmar es nulo, no cero")
        self.assertEqual(VC.ESQUEMA.field("aseguradoras_reportantes").type, "int64")


class TestCobertura(unittest.TestCase):
    """El desglose de cobertura por vigencia es el que responde si faltó procesar o si la fuente es finita."""

    def test_el_run_se_normaliza_entre_registro_y_publicado(self):
        # El registro CMF guarda el RUN como entero y lo publicado como cadena. Sin normalizar, el
        # cruce queda vacío y la cobertura por vigencia sale en 0,0 % sin ningún error: el peor tipo
        # de defecto, el que parece un resultado.
        from ffmm.scripts import actualizar_valor_cuota as AV
        for bruto, esperado in [(8001, "8001"), ("8001", "8001"), (8001.0, "8001"),
                                (" 8001 ", "8001"), (None, None), ("", None)]:
            self.assertEqual(AV._run(bruto), esperado, f"RUN {bruto!r}")

    def test_la_cobertura_por_vigencia_cuadra_con_el_total(self):
        import json
        from ffmm.scripts import actualizar_valor_cuota as AV
        control = json.loads(AV.CONTROL.read_text(encoding="utf-8"))
        ffmm = control["cobertura"]["ffmm"]
        desglose = ffmm["por_vigencia"]
        self.assertTrue(desglose, "el desglose por vigencia no se está publicando")
        self.assertEqual(sum(g["fondos"] for g in desglose.values()), ffmm["universo_registro"],
                         "el desglose no cubre el mismo universo que el total")
        self.assertEqual(sum(g["con_valor_cuota"] for g in desglose.values()), ffmm["fondos_con_valor_cuota"],
                         "el desglose no cubre los mismos fondos que el total")
        for nombre, g in desglose.items():
            self.assertIsNotNone(g["cobertura"], f"{nombre}: cobertura nula con {g['fondos']} fondos")
            self.assertGreaterEqual(g["cobertura"], 0.0, f"{nombre}: cobertura negativa")

    def test_los_periodos_publicados_son_todos_los_de_la_fuente(self):
        # La pregunta "20 % es poco, ¿no procesamos todos los periodos?" se responde acá: si la fuente
        # trae un periodo y el conjunto publicado no, es una pérdida real y no un efecto del denominador.
        import json
        from ffmm.scripts import actualizar_valor_cuota as AV
        m = json.loads((AV.SECTORES["ffmm"] / "manifest.json").read_text(encoding="utf-8"))
        control = json.loads(AV.CONTROL.read_text(encoding="utf-8"))
        self.assertEqual(len(control["cobertura"]["ffmm"]["periodos_fuente"]), len(m["periodos"]))
        fuente = VC.ORIGEN_SEGUROS
        if fuente.exists():
            periodos = sorted({str(p) for f in sorted(fuente.glob("*.parquet"))
                               for p in pq.read_table(f, columns=["periodo"])["periodo"].to_pylist() if p})
            self.assertEqual(set(periodos), set(m["periodos"]),
                             f"periodos de la fuente ausentes del manifiesto: "
                             f"{sorted(set(periodos) - set(m['periodos']))}")


if __name__ == "__main__":
    unittest.main()
