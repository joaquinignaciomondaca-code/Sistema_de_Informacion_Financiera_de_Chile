"""Pruebas de `ffmm/scripts/actualizar_eeff.py`: el flujo completo, sin red, con la CMF simulada.

Desde un entorno de desarrollo no se llega a cmfchile.cl, así que `_get` se reemplaza por una «CMF» de juguete que
responde fichas y XML con la forma y los valores reales (ffmm/tests/xml_sintetico.py). Lo que se comprueba es lo
que de verdad importa de un publicador automático:

  * qué se publica y con qué forma (Parquet, manifiestos, control, data_manifest);
  * que un desafío de la CMF o un XML a medias **nunca** se tome por «sin información» ni abra un hueco silencioso;
  * que la serie solo se publique con todos los cierres cerrados resueltos, y que se detenga ante un descuadre en
    bloque o un formato roto;
  * que una corrida repetida no cambie nada y que, si se pierde la caché, el estado se reconstruya de lo publicado;
  * la vuelta de refresco (reediciones) y el tope de tiempo.

Sin tocar `docs/`, con carpetas temporales y el reloj fijado.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from ffmm.tests import xml_sintetico as X  # noqa: E402
from scripts.audit_rut_formatos import auditar_parquet  # noqa: E402

SPEC = importlib.util.spec_from_file_location("actualizar_eeff", RAIZ / "ffmm/scripts/actualizar_eeff.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

HOY = date(2026, 10, 1)          # último cierre: 2025, cerrado (274 días)
MAESTRO_COLS = ["run_fondo", "nombre_fondo", "primer_periodo", "ultimo_periodo", "meses_reportados", "reporta_ultimo_mes"]


class Entorno(unittest.TestCase):
    """Carpetas temporales, reloj fijo y una CMF simulada."""

    hoy = HOY

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        t = Path(self._tmp.name)
        self.salida, self.local = t / "docs" / "outputs" / "ffmm", t / "local"
        self.salida.mkdir(parents=True)
        (t / "data_manifest.json").write_text(json.dumps({"tables": [], "total_tables": 0, "total_records": 0}))
        originales = {k: getattr(m, k) for k in ("RAIZ", "SALIDA", "LOCAL", "CONTROL", "MAESTRO", "UNIVERSO", "_hoy", "_get")}
        self.addCleanup(lambda: [setattr(m, k, v) for k, v in originales.items()])
        m.RAIZ, m.SALIDA, m.LOCAL = t, self.salida, self.local
        m.CONTROL = self.salida / "ffmm_eeff_control.json"
        m.MAESTRO = self.salida / "maestro_fondos_mutuos.parquet"
        m.UNIVERSO = self.salida / "ffmm_registro_fondos_universo.parquet"
        m._hoy = lambda: self.hoy
        m._get = self.cmf
        patcher = mock.patch.object(time, "sleep", lambda s: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.fichas, self.archivos, self.pedidos = {}, {}, []
        self.addCleanup(self._tmp.cleanup)

    # --- la CMF de juguete ---------------------------------------------------------------------------------
    def cmf(self, url, intentos=3, timeout=60):
        self.pedidos.append(url)
        if "entidad.php" in url:
            run = url.split("rut=")[1].split("&")[0]
            anio = int(url.split("aa=")[1].split("&")[0])
            r = self.fichas.get((run, anio), X.ficha(run, anio, "sin_informacion"))
        else:
            r = self.archivos[url.split("archivo=")[1].split("&")[0]]
        if isinstance(r, Exception):
            raise r if isinstance(r, m.ErrorTransitorio) else m.ErrorTransitorio(f"sin respuesta de la CMF ({type(r).__name__})")
        if callable(r):
            r = r()
        return r

    def fondo(self, run, anio, version=0, ficha=None, xml=None, **kw):
        arch = X.nombre_archivo(run, anio, version)
        self.fichas[(run, anio)] = ficha if ficha is not None else X.ficha(run, anio, "xml", arch)
        self.archivos[arch] = xml if xml is not None else X.xml(run, anio, **kw)
        return arch

    def xml_pedidos(self):
        return [u for u in self.pedidos if "ifrs_xml_verarchivo" in u]

    def maestro(self, *filas, universo=()):
        """filas: (run, primer_periodo, ultimo_periodo)."""
        cols = {c: [] for c in MAESTRO_COLS}
        for run, p0, p1 in filas:
            for c, v in zip(MAESTRO_COLS, (run, f"FONDO {run}", p0, p1, 1, p1 >= "2026-08")):
                cols[c].append(v)
        pq.write_table(pa.table(cols), m.MAESTRO)
        runs = sorted({int(f[0]) for f in filas} | {int(u) for u in universo})
        pq.write_table(pa.table({"run_fondo": pa.array(runs, pa.int64())}), m.UNIVERSO)

    def correr(self, **kw):
        kw.setdefault("desde", 2023)
        return m.correr(**kw)

    def filas(self, tabla):
        out = []
        for r in sorted((self.salida / f"ffmm_{tabla}").glob("*.parquet")):
            out += pq.read_table(r).to_pylist()
        return out


class Escenario(Entorno):
    """Cuatro fondos con historias distintas y uno que solo está en el registro."""

    def setUp(self):
        super().setUp()
        self.maestro(("8011", "2001-01", "2026-08"),      # vigente: 2023, 2024, 2025
                     ("9001", "2024-03", "2026-08"),      # nació en 2024: 2024, 2025
                     ("8001", "2001-01", "2024-07"),      # dejó de reportar a mitad de 2024: hasta 2023
                     ("7001", "2010-01", "2023-12"),      # su último mes es diciembre: incluye 2023
                     universo=("6001",))                  # nunca reportó cartera: se consultan todos los años
        for a in (2023, 2024, 2025):
            self.fondo("8011", a)
        self.fondo("9001", 2024, factor=2)
        self.fondo("9001", 2025, factor=2, moneda="PROM")
        self.fondo("8001", 2023, factor=3)
        self.fondo("7001", 2023, factor=4)
        # 6001 no tiene nada: la ficha responde «No existe información» (valor por defecto de la CMF de juguete)


class TestCandidatos(Escenario):
    def test_diciembres_dentro_de_la_vida_activa_y_registro_sin_cartera(self):
        cand = m.candidatos(self.hoy, 2023)
        por_fondo = {}
        for run, anio in cand:
            por_fondo.setdefault(run, []).append(anio)
        self.assertEqual({k: sorted(v) for k, v in por_fondo.items()},
                         {"8011": [2023, 2024, 2025], "9001": [2024, 2025], "8001": [2023], "7001": [2023],
                          "6001": [2023, 2024, 2025]})
        # del cierre más reciente al más antiguo
        self.assertEqual([a for _r, a in cand], sorted((a for _r, a in cand), reverse=True))

    def test_nunca_pide_el_cierre_en_curso_ni_antes_de_2010(self):
        self.maestro(("8011", "2001-01", "2026-08"))
        años = {a for _r, a in m.candidatos(self.hoy)}
        self.assertEqual((min(años), max(años)), (2010, 2025))
        self.maestro(("8011", "2001-01", "2027-01"))
        self.assertEqual(max(a for _r, a in m.candidatos(date(2027, 2, 1))), 2026)

    def test_sin_maestro_ni_registro_no_hay_candidatos(self):
        m.MAESTRO.unlink()
        m.UNIVERSO.unlink()
        self.assertEqual(m.candidatos(self.hoy), [])


class TestPublicacion(Escenario):
    def test_publica_todo_con_la_forma_documentada(self):
        out = self.correr()
        self.assertTrue(out["publicado"], out)
        self.assertEqual(out["ok"], 7)                       # 8011 ×3 + 9001 ×2 + 8001 + 7001; 6001 no tiene nada
        self.assertEqual(out["cuenta"]["sin_informacion"], 3)
        bal, res = self.filas("balance"), self.filas("resultados")
        self.assertEqual((len(bal), len(res)), (7 * 16, 7 * 19))
        self.assertEqual({f["periodo"] for f in bal}, {"2023-12", "2024-12", "2025-12"})
        for t in ("balance", "resultados"):
            esquema = pq.read_schema(next((self.salida / f"ffmm_{t}").glob("*.parquet")))
            self.assertEqual(esquema.names, list(m.ESQUEMA.names))
            self.assertEqual([str(x) for x in esquema.types], [str(x) for x in m.ESQUEMA.types])
        # orden de presentación de la CMF, no el alfabético del XML
        f8011 = [f for f in bal if f["run_fondo"] == "8011" and f["periodo"] == "2025-12"]
        self.assertEqual([f["orden"] for f in f8011], list(range(1, 17)))
        self.assertEqual(f8011[7]["codigo_cuenta"], "TotalActivo")
        self.assertEqual(f8011[7]["valor_miles_mf"], 192872200)
        self.assertEqual(f8011[7]["valor_anterior_miles_mf"], 251970282)
        self.assertEqual(f8011[0]["nota"], "6")
        self.assertIsNone(f8011[7]["nota"])
        self.assertEqual(f8011[0]["run_fondo_dv"], "8011-K")
        self.assertEqual(f8011[0]["rut_agf"], "91999000")
        self.assertEqual(f8011[0]["enviado_cmf"], "2026-03-30 11:09:24")
        self.assertEqual(len(f8011[0]["sha256_archivo"]), 64)

    def test_moneda_y_escala_por_fondo(self):
        self.correr()
        bal = self.filas("balance")
        monedas = {(f["run_fondo"], f["periodo"]): (f["moneda"], f["moneda_cmf"]) for f in bal}
        self.assertEqual(monedas[("9001", "2025-12")], ("USD", "PROM"))
        self.assertEqual(monedas[("8011", "2025-12")], ("CLP", "$$"))
        total9001 = next(f for f in bal if f["run_fondo"] == "9001" and f["periodo"] == "2025-12" and f["orden"] == 8)
        self.assertEqual(total9001["valor_miles_mf"], 2 * 192872200)

    def test_manifiestos_control_y_data_manifest(self):
        self.correr()
        for t, filas in (("balance", 7 * 16), ("resultados", 7 * 19)):
            man = json.loads((self.salida / f"ffmm_{t}" / "manifest.json").read_text())
            self.assertEqual(man["tabla"], f"ffmm_{t}")
            self.assertEqual(man["total_records"], filas)
            self.assertEqual(man["periodos"], ["2023-12", "2024-12", "2025-12"])
            self.assertEqual(man["files"], [f"outputs/ffmm/ffmm_{t}/{a}.parquet" for a in (2023, 2024, 2025)])
            self.assertEqual(man["fondos_por_periodo"], {"2023-12": 3, "2024-12": 2, "2025-12": 2})
        ctl = json.loads(m.CONTROL.read_text())
        self.assertEqual(ctl["cierres"]["2025"], {"candidatos": 3, "con_estados": 2, "sin_informacion": 1, "ilegibles": 0,
                                                  "pendientes": 0, "cerrado": True})
        self.assertEqual(ctl["sin_informacion"], {"2023": ["6001"], "2024": ["6001"], "2025": ["6001"]})
        dm = json.loads((m.RAIZ / "data_manifest.json").read_text())
        ids = {t["id"]: t for t in dm["tables"]}
        self.assertEqual(set(ids), {"ffmm_balance", "ffmm_resultados"})
        self.assertEqual(ids["ffmm_balance"]["registros_reales"], 7 * 16)
        self.assertEqual(ids["ffmm_balance"]["corte"], "2023-12 a 2025-12")
        self.assertEqual(ids["ffmm_balance"]["file_parquet"], "outputs/ffmm/ffmm_balance/manifest.json")
        self.assertTrue(ids["ffmm_balance"]["modo"].startswith("Automático"))
        self.assertEqual(dm["total_records"], 7 * 16 + 7 * 19)

    def test_el_guardian_de_rut_acepta_lo_publicado(self):
        self.correr()
        for t in ("balance", "resultados"):
            for ruta in (self.salida / f"ffmm_{t}").glob("*.parquet"):
                self.assertEqual(auditar_parquet(ruta), [], ruta.name)

    def test_cuadratura_y_resultados_de_lo_publicado(self):
        from pipelines.auto import cuadratura
        self.correr()
        v, malos = cuadratura.verificar_ffmm(self.filas("balance"))
        self.assertEqual((v, malos), (7, []))
        v, malos = cuadratura.verificar_resultados_ffmm(self.filas("resultados"))
        self.assertEqual((v, malos), (7 * 6, []))


class TestIdempotenciaYEstado(Escenario):
    def test_una_segunda_corrida_no_cambia_nada_ni_descarga_xml(self):
        self.correr()
        archivos = sorted(self.salida.rglob("*.parquet")) + [m.CONTROL] + sorted(self.salida.rglob("manifest.json"))
        antes = {a: (a.read_bytes(), a.stat().st_mtime_ns) for a in archivos}
        self.pedidos.clear()
        out = self.correr()
        self.assertTrue(out["publicado"])
        self.assertEqual(self.xml_pedidos(), [], "ningún XML ya publicado se vuelve a bajar")
        for a in archivos:
            self.assertEqual((a.read_bytes(), a.stat().st_mtime_ns), antes[a], f"{a.name} cambió sin cambios en la fuente")

    def test_si_se_pierde_la_cache_el_estado_se_reconstruye_de_lo_publicado(self):
        self.correr()
        publicado = {a: a.read_bytes() for a in sorted(self.salida.rglob("*.parquet"))}
        import shutil
        shutil.rmtree(self.local)
        self.pedidos.clear()
        out = self.correr()
        self.assertEqual(self.xml_pedidos(), [])
        self.assertEqual(out["ok"], 7)
        self.assertEqual({a: a.read_bytes() for a in sorted(self.salida.rglob("*.parquet"))}, publicado)

    def test_vuelta_de_refresco_cubre_toda_la_historia_una_vez_al_ano(self):
        corridas = [date(2026, 1, 1) + timedelta(days=10 * v + 4) for v in range(36)]
        claves = [(str(r), a) for r in range(8000, 8040) for a in range(2010, 2024)]
        veces = {k: 0 for k in claves}
        for d in corridas:
            for k in claves:
                if m.toca_refresco(k[0], k[1], d):
                    veces[k] += 1
        self.assertEqual(set(veces.values()), {1}, "cada fondo y cierre viejo se revisa exactamente una vez al año")
        # los dos últimos cierres se revisan en todas las corridas
        self.assertTrue(all(m.toca_refresco("8011", 2025, d) and m.toca_refresco("8011", 2024, d) for d in corridas))
        self.assertTrue(m.toca_refresco("8011", 2012, corridas[0], forzar=True))


class TestErroresDeLaCmf(Escenario):
    def test_un_desafio_no_es_sin_informacion_ni_publica_con_huecos(self):
        self.fichas[("8001", 2023)] = X.ficha("8001", 2023, "desafio")
        out = self.correr()
        self.assertFalse(out["publicado"])
        self.assertEqual(out["pendientes_cerrados"], [("8001", 2023)])
        self.assertFalse(self.salida.joinpath("ffmm_balance").exists())
        est = m.cargar_progreso()[("8001", 2023)]
        self.assertEqual(est["estado"], "pendiente")
        self.assertNotEqual(est["estado"], "sin_informacion")
        # la CMF se recupera en la corrida siguiente: se resuelve y se publica
        self.fichas[("8001", 2023)] = X.ficha("8001", 2023, "xml", X.nombre_archivo("8001", 2023))
        self.archivos[X.nombre_archivo("8001", 2023)] = X.xml("8001", 2023, factor=3)
        out = self.correr()
        self.assertTrue(out["publicado"])
        self.assertEqual(out["ok"], 7)

    def test_un_corte_de_red_deja_pendiente_y_conserva_lo_ya_publicado(self):
        self.correr()
        publicado = self.filas("balance")
        self.fichas[("8011", 2025)] = ConnectionError("reset")
        self.fichas[("8011", 2024)] = m.ErrorTransitorio("sin respuesta de la CMF (URLError)")
        out = self.correr()
        self.assertEqual(out["cuenta"]["error_transitorio"], 2)
        self.assertTrue(out["publicado"], "un fallo al releer no despublica ni deja huecos")
        self.assertEqual(self.filas("balance"), publicado)

    def test_xml_a_medias_se_reintenta_y_a_la_tercera_corrida_queda_ilegible_sin_bloquear(self):
        buenos = X.xml("8001", 2023, factor=3)
        self.archivos[self.fondo("8001", 2023)] = buenos[: len(buenos) // 2]          # corte a la mitad
        for corrida in (1, 2):
            out = self.correr()
            self.assertFalse(out["publicado"], f"corrida {corrida}: sigue pendiente")
            self.assertEqual(m.cargar_progreso()[("8001", 2023)]["estado"], "pendiente")
        out = self.correr()
        self.assertEqual(m.cargar_progreso()[("8001", 2023)]["estado"], "ilegible")
        self.assertTrue(out["publicado"])
        self.assertEqual(out["ok"], 6)
        ctl = json.loads(m.CONTROL.read_text())
        self.assertEqual([(e["run"], e["anio"]) for e in ctl["ilegibles"]], [("8001", 2023)])
        self.assertIn("incompleto", ctl["ilegibles"][0]["motivo"])

    def test_fichas_sin_enlace_tambien_terminan_como_ilegibles(self):
        self.fichas[("7001", 2023)] = X.ficha("7001", 2023, "sin_enlace")
        for _ in range(3):
            out = self.correr()
        self.assertEqual(m.cargar_progreso()[("7001", 2023)]["estado"], "ilegible")
        self.assertTrue(out["publicado"])

    def test_el_freno_de_emergencia_guarda_el_progreso_y_no_publica(self):
        for k in list(self.fichas) + [("6001", a) for a in (2023, 2024, 2025)]:
            self.fichas[k] = ConnectionError("sin red")
        original = m.Frenazo.__init__.__defaults__
        m.Frenazo.__init__.__defaults__ = (3,)                     # con 10 candidatos hay que bajar el umbral de 40
        self.addCleanup(setattr, m.Frenazo.__init__, "__defaults__", original)
        out = self.correr(hilos=1)
        self.assertFalse(out["publicado"])
        self.assertTrue(out["freno"])
        self.assertGreater(out["cuenta"].get("omitidos", 0), 0, "tras el freno el resto queda para la próxima corrida")
        self.assertTrue((self.local / "progreso.jsonl.gz").exists())

    def test_tope_de_tiempo_agotado_conserva_el_progreso_y_no_publica(self):
        out = self.correr(minutos=0)
        self.assertFalse(out["publicado"])
        self.assertEqual(out["cuenta"].get("omitidos"), 10)
        self.assertFalse(self.salida.joinpath("ffmm_balance").exists())
        out = self.correr()                                                # la corrida siguiente lo completa
        self.assertTrue(out["publicado"])


def secuencia(*respuestas):
    """Una respuesta distinta en cada petición (la CMF a veces sirve el desafío una vez y luego la ficha)."""
    it = iter(respuestas)
    return lambda: next(it)


class TestReintentosYRondaLenta(Escenario):
    """El primer recorrido real dejó 14 fichas pendientes por la página de desafío de la CMF: la serie no se publicaba."""

    def ficha_ok(self, run="8001", anio=2023):
        return X.ficha(run, anio, "xml", X.nombre_archivo(run, anio))

    def test_un_desafio_aislado_se_resuelve_con_el_reintento_de_la_misma_corrida(self):
        self.fichas[("8001", 2023)] = secuencia(X.ficha("8001", 2023, "desafio"), self.ficha_ok())
        out = self.correr()
        self.assertTrue(out["publicado"], out)
        self.assertEqual(out["ok"], 7)
        fichas = [u for u in self.pedidos if "entidad.php" in u and "rut=8001" in u]
        self.assertEqual(len(fichas), 2, "una ficha rechazada y la reintentada")

    def test_un_xml_a_medias_aislado_tambien_se_reintenta(self):
        buenos = X.xml("8001", 2023, factor=3)
        self.archivos[X.nombre_archivo("8001", 2023)] = secuencia(buenos[:1500], buenos)
        out = self.correr()
        self.assertTrue(out["publicado"], out)
        self.assertEqual(out["ok"], 7)

    def test_la_ronda_lenta_resuelve_lo_que_aguanto_los_reintentos(self):
        desafio = X.ficha("8001", 2023, "desafio")
        self.fichas[("8001", 2023)] = secuencia(*([desafio] * m.REINTENTOS_RESPUESTA), self.ficha_ok())
        out = self.correr()
        self.assertTrue(out["publicado"], out)
        self.assertEqual(out["cuenta"]["rezagados_resueltos"], 1)
        self.assertEqual(out["ok"], 7)

    def test_las_rondas_lentas_no_cuentan_como_corridas_para_marcar_un_xml_ilegible(self):
        buenos = X.xml("8001", 2023, factor=3)
        self.archivos[X.nombre_archivo("8001", 2023)] = buenos[:1500]          # nunca llega completo
        out = self.correr()
        r = m.cargar_progreso()[("8001", 2023)]
        self.assertEqual((r["estado"], r["intentos"]), ("pendiente", 1), "pese a 3 intentos + 2 rondas, es 1 corrida")
        self.assertFalse(out["publicado"])

    def test_sin_tiempo_no_hay_ronda_lenta(self):
        desafio = X.ficha("8001", 2023, "desafio")
        self.fichas[("8001", 2023)] = secuencia(*([desafio] * m.REINTENTOS_RESPUESTA), self.ficha_ok())
        out = self.correr(minutos=0.5)
        self.assertEqual(out["cuenta"].get("rezagados_resueltos", 0), 0)
        self.assertFalse(out["publicado"])


class TestIlegiblesYCompuertas(Escenario):
    def test_xml_de_otro_fondo_moneda_desconocida_o_cuentas_faltantes_se_excluyen_y_se_listan(self):
        self.fondo("8001", 2023, xml=X.xml("8001", 2023, run_xml="1234"))
        self.fondo("7001", 2023, moneda="XYZ")
        self.fondo("9001", 2024, omitir=("TotalPasivo",))
        out = self.correr()
        self.assertTrue(out["publicado"])
        self.assertEqual(out["ok"], 4)
        ctl = json.loads(m.CONTROL.read_text())
        motivos = {(e["run"], e["anio"]): e["motivo"] for e in ctl["ilegibles"]}
        self.assertIn("es del fondo 1234", motivos[("8001", 2023)])
        self.assertIn("moneda desconocida 'XYZ'", motivos[("7001", 2023)])
        self.assertIn("faltan 1 cuentas", motivos[("9001", 2024)])
        self.assertEqual(ctl["cierres"]["2023"]["ilegibles"], 2)

    def test_hay_fondos_en_euros(self):
        self.fondo("7001", 2023, factor=4, moneda="EUR")
        out = self.correr()
        self.assertEqual((out["ok"], out["ilegibles"]), (7, 0))
        euros = {(f["run_fondo"], f["moneda"], f["moneda_cmf"]) for f in self.filas("balance") if f["moneda"] == "EUR"}
        self.assertEqual(euros, {("7001", "EUR", "EUR")})

    def test_los_ilegibles_se_reintentan_en_cada_corrida_y_se_recuperan(self):
        arch = self.fondo("8001", 2023, xml=X.xml("8001", 2023, factor=3, moneda="XYZ"))
        out = self.correr()
        self.assertEqual((out["ok"], out["ilegibles"]), (6, 1))
        self.assertEqual(out["motivos_ilegibles"], {"moneda desconocida 'XYZ'": 1})
        self.assertTrue(out["publicado"])
        self.archivos[arch] = X.xml("8001", 2023, factor=3)                    # se corrige la fuente (o el código)
        out = self.correr()
        self.assertEqual((out["ok"], out["ilegibles"]), (7, 0))
        self.assertEqual(json.loads(m.CONTROL.read_text())["ilegibles"], [])

    def test_un_balance_aislado_que_no_cuadra_se_publica_con_su_aviso(self):
        self.fondo("8001", 2023, xml=X.xml("8001", 2023, factor=3, sobrescribir={"TotalActivo": 999}))
        out = self.correr()
        self.assertTrue(out["publicado"])
        self.assertEqual(out["ok"], 7)
        avisos = json.loads(m.CONTROL.read_text())["avisos"]
        self.assertTrue(any(a["run"] == "8001" and "activo − pasivo = activo neto" in a["aviso"] for a in avisos), avisos)

    def test_un_descuadre_en_bloque_detiene_la_serie_sin_publicar(self):
        runs = [str(7100 + i) for i in range(30)]
        self.maestro(*[(r, "2001-01", "2026-08") for r in runs])
        for r in runs[:6]:                                         # 6 de 30: ≥3 y más del 5 %
            self.fondo(r, 2025, sobrescribir={"TotalActivo": 1})
        for r in runs[6:]:
            self.fondo(r, 2025)
        out = self.correr(desde=2025)
        self.assertFalse(out["publicado"])
        self.assertIn("6 de 30 balances no cuadran", out["motivo_error"])
        self.assertFalse(self.salida.joinpath("ffmm_balance").exists())
        self.assertEqual(m.main(["--desde", "2025"]), 1)

    def test_si_casi_ningun_balance_trae_los_totales_la_compuerta_no_queda_ciega(self):
        # Se renombra TotalActivo: el XML ya no trae las 35 cuentas, así que todo queda ilegible y la serie se detiene.
        runs = [str(7100 + i) for i in range(30)]
        self.maestro(*[(r, "2001-01", "2026-08") for r in runs])
        for r in runs:
            self.fondo(r, 2025, xml=X.xml(r, 2025).replace(b'CodigoCuenta="TotalActivo"', b'CodigoCuenta="ActivosTotales"'))
        out = self.correr(desde=2025)
        self.assertFalse(out["publicado"])
        self.assertIn("ilegibles", out["motivo_error"])

    def test_pocos_ilegibles_aislados_no_detienen(self):
        self.maestro(*[(str(7100 + i), "2001-01", "2026-08") for i in range(60)])
        for i in range(60):
            r = str(7100 + i)
            self.fondo(r, 2025, **({"omitir": ("TotalPasivo",)} if i == 0 else {}))
        out = self.correr(desde=2025)
        self.assertTrue(out["publicado"])
        self.assertEqual((out["ok"], out["ilegibles"]), (59, 1))


class TestReedicionYCierresAbiertos(Escenario):
    def test_un_reenvio_se_detecta_por_el_nombre_del_archivo_y_reemplaza_los_datos(self):
        self.correr()
        nuevo = self.fondo("8011", 2025, version=1, xml=X.xml("8011", 2025, sobrescribir={"OtrosActivos": 9, "TotalActivo": 192872202}))
        out = self.correr()
        self.assertEqual(out["cuenta"]["reedicion"], 1)
        fila = next(f for f in self.filas("balance") if f["run_fondo"] == "8011" and f["periodo"] == "2025-12" and f["orden"] == 8)
        self.assertEqual((fila["valor_miles_mf"], fila["fuente_archivo"]), (192872202, nuevo))
        rees = json.loads(m.CONTROL.read_text())["reediciones"]
        self.assertEqual([(r["run"], r["anio"], r["archivo_nuevo"]) for r in rees], [("8011", 2025, nuevo)])
        self.assertEqual(rees[0]["archivo_anterior"], X.nombre_archivo("8011", 2025))

    def test_un_reenvio_ilegible_no_destruye_lo_publicado(self):
        self.correr()
        antes = self.filas("balance")
        self.fondo("8011", 2025, version=1, xml=X.xml("8011", 2025, run_xml="999"))
        self.correr()
        self.assertEqual(self.filas("balance"), antes)
        avisos = json.loads(m.CONTROL.read_text())["avisos"]
        self.assertTrue(any("no se pudo leer" in a["aviso"] for a in avisos if a["run"] == "8011"))

    def test_si_la_ficha_deja_de_mostrar_un_envio_publicado_se_conserva_con_aviso(self):
        self.correr()
        self.fichas[("8011", 2025)] = X.ficha("8011", 2025, "sin_informacion")
        self.correr()
        self.assertEqual(sum(1 for f in self.filas("balance") if f["run_fondo"] == "8011" and f["periodo"] == "2025-12"), 16)
        self.assertTrue(any("ya no muestra" in a["aviso"] for a in json.loads(m.CONTROL.read_text())["avisos"]))

    def test_un_envio_tardio_aparece_en_la_corrida_siguiente(self):
        self.correr()
        self.assertEqual(self.filas("balance")[0]["periodo"], "2023-12")
        self.fondo("6001", 2025, factor=5)                       # el fondo «sin información» presentó tarde
        out = self.correr()
        self.assertEqual(out["ok"], 8)
        self.assertEqual(json.loads(m.CONTROL.read_text())["cierres"]["2025"]["sin_informacion"], 0)

    def test_un_cierre_abierto_se_publica_parcial_y_se_relee(self):
        self.hoy = date(2027, 2, 1)                                # FY2026 abierto (32 días); 2025 cerrado
        self.maestro(("8011", "2001-01", "2027-01"), ("9001", "2001-01", "2027-01"))
        for r in ("8011", "9001"):
            for a in (2025, 2026):
                self.fondo(r, a)
        self.fichas[("9001", 2026)] = X.ficha("9001", 2026, "sin_informacion")   # aún no presentó
        out = self.correr(desde=2025)
        self.assertTrue(out["publicado"], out)
        self.assertEqual(json.loads(m.CONTROL.read_text())["cierres"]["2026"]["cerrado"], False)
        self.assertEqual(sum(1 for f in self.filas("balance") if f["periodo"] == "2026-12"), 16)
        self.fondo("9001", 2026)                                   # presenta en marzo
        out = self.correr(desde=2025)
        self.assertEqual(sum(1 for f in self.filas("balance") if f["periodo"] == "2026-12"), 32)

    def test_un_cierre_abierto_con_pendientes_no_bloquea(self):
        self.hoy = date(2027, 2, 1)
        self.maestro(("8011", "2001-01", "2027-01"))
        self.fondo("8011", 2025)
        self.fichas[("8011", 2026)] = X.ficha("8011", 2026, "desafio")        # FY2026 abierto: la CMF no responde bien
        out = self.correr(desde=2025)
        self.assertTrue(out["publicado"], out)
        self.assertEqual(out["pendientes_cerrados"], [])
        self.assertEqual(json.loads(m.CONTROL.read_text())["cierres"]["2026"]["pendientes"], 1)


class TestHilos(Escenario):
    def test_con_varios_hilos_el_resultado_es_el_mismo(self):
        self.correr(hilos=1)
        uno = {a.name: a.read_bytes() for a in sorted(self.salida.rglob("*.parquet"))}
        import shutil
        shutil.rmtree(self.salida / "ffmm_balance"), shutil.rmtree(self.salida / "ffmm_resultados")
        self.salida.joinpath("ffmm_eeff_control.json").unlink()
        shutil.rmtree(self.local)
        self.correr(hilos=6)
        self.assertEqual({a.name: a.read_bytes() for a in sorted(self.salida.rglob("*.parquet"))}, uno)


class TestInterfazDelWorkflow(Escenario):
    """Lo que ffmm_eeff.yml lee del script: salidas de GITHUB_OUTPUT y código de salida."""

    def salidas(self, argv):
        archivo = Path(self._tmp.name) / "github_output"
        with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(archivo)}):
            rc = m.main(argv)
        return rc, dict(l.split("=") for l in archivo.read_text().split())

    def test_publicada_y_completa(self):
        rc, sal = self.salidas(["--desde", "2023"])
        self.assertEqual((rc, sal), (0, {"publicado": "true", "completo": "true"}))

    def test_incompleta_no_publica_y_no_es_un_error(self):
        self.fichas[("8001", 2023)] = X.ficha("8001", 2023, "desafio")
        rc, sal = self.salidas(["--desde", "2023"])
        self.assertEqual((rc, sal), (0, {"publicado": "false", "completo": "false"}))

    def test_la_compuerta_en_bloque_sale_en_rojo(self):
        runs = [str(7100 + i) for i in range(30)]
        self.maestro(*[(r, "2001-01", "2026-08") for r in runs])
        for i, r in enumerate(runs):
            self.fondo(r, 2025, **({"sobrescribir": {"TotalActivo": 1}} if i < 6 else {}))
        rc, sal = self.salidas(["--desde", "2025"])
        self.assertEqual((rc, sal["publicado"]), (1, "false"))

    def test_resumen_para_la_pagina_de_la_corrida(self):
        self.correr()
        r = json.loads((self.local / "resumen.json").read_text())
        self.assertEqual((r["ok"], r["publicado"], r["pendientes_cerrados"]), (7, True, 0))

    def test_solo_data_manifest(self):
        self.correr()
        (m.RAIZ / "data_manifest.json").write_text(json.dumps({"tables": [{"id": "otra", "registros_reales": 5}]}))
        self.assertEqual(m.main(["--solo-data-manifest"]), 0)
        dm = json.loads((m.RAIZ / "data_manifest.json").read_text())
        self.assertEqual([t["id"] for t in dm["tables"]], ["otra", "ffmm_balance", "ffmm_resultados"])
        self.assertEqual(dm["total_tables"], 3)
        self.assertEqual(dm["total_records"], 5 + 7 * 16 + 7 * 19)

    def test_el_limite_acota_los_pedidos(self):
        out = self.correr(limite=3)
        self.assertEqual(sum(1 for u in self.pedidos if "entidad.php" in u), 3)
        self.assertFalse(out["publicado"])


class TestRed(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(time, "sleep", lambda s: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        m.FRENO.__init__()

    def test_get_reintenta_y_termina_en_error_transitorio(self):
        llamadas = []

        def urlopen(req, timeout=0):
            llamadas.append(req.full_url)
            raise OSError("reset")
        with mock.patch.object(m.urllib.request, "urlopen", urlopen):
            with self.assertRaises(m.ErrorTransitorio):
                m._get("https://x/", intentos=3)
        self.assertEqual(len(llamadas), 3)

    def test_get_devuelve_el_cuerpo_y_manda_el_user_agent(self):
        vistos = []

        class R:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b"ok"

        def urlopen(req, timeout=0):
            vistos.append(req.get_header("User-agent"))
            return R()
        with mock.patch.object(m.urllib.request, "urlopen", urlopen):
            self.assertEqual(m._get("https://x/"), b"ok")
        self.assertIn("MonitorFinancieroChile", vistos[0])

    def test_el_freno_se_activa_tras_demasiadas_fallas_seguidas(self):
        f = m.Frenazo(limite=3)
        f.falla(), f.falla()
        self.assertFalse(f.detener.is_set())
        f.falla()
        self.assertTrue(f.detener.is_set())
        f2 = m.Frenazo(limite=3)
        f2.falla(), f2.ok(), f2.falla(), f2.falla()
        self.assertFalse(f2.detener.is_set(), "un éxito reinicia la cuenta")


if __name__ == "__main__":
    unittest.main()
