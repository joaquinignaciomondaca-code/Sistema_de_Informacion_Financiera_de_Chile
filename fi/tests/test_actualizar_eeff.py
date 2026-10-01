"""Publicación FI de punta a punta con fuentes reales servidas desde memoria."""

from __future__ import annotations

import contextlib
import copy
import gzip
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlsplit

import pyarrow as pa
import pyarrow.parquet as pq

from fi.scripts import actualizar_eeff as m
from fi.scripts import eeff_xml as x
from fi.scripts.auditar_eeff import auditar, verificar_tablas
from fi.scripts.catalogos_eeff import actualizar_catalogos
from fi.tests.test_eeff_xml import cambiar, datos, registro

RAIZ = Path(__file__).resolve().parents[2]


def make_root(root):
    (root / "docs/js").mkdir(parents=True)
    for name in (
        "duckdb_client.js",
        "sidebar.js",
        "data_viewer.js",
        "data_dictionary.js",
        "erd_graph.js",
    ):
        shutil.copyfile(RAIZ / "docs/js" / name, root / "docs/js" / name)
    shutil.copyfile(RAIZ / "docs/vocabulario.json", root / "docs/vocabulario.json")
    shutil.copyfile(RAIZ / "docs/index.html", root / "docs/index.html")
    (root / "data_manifest.json").write_text(
        json.dumps(
            {
                "tables": [{"id": "otra_tabla", "registros_reales": 17}],
                "total_tables": 1,
                "total_records": 17,
            }
        )
    )
    return m.Config(raiz=root)


def proveedor(raw=None, html=None, llamadas=None):
    raw0, html0, _ = datos()
    raw = raw0 if raw is None else raw
    html = html0 if html is None else html

    def get(url):
        if llamadas is not None:
            llamadas.append(url)
        q = parse_qs(urlsplit(url).query)
        return raw if "archivo" in q else html

    return get


def correr(cfg, fetcher=None, **kwargs):
    with (
        mock.patch.object(m, "_hoy", return_value=date(2026, 10, 1)),
        mock.patch.object(m.time, "sleep"),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        return m.correr(
            cfg,
            minutos=1,
            hilos=1,
            desde="2026-06",
            hasta="2026-06",
            registro={"7002": {"run": "7002", "tipo_entidad": "FINRE"}},
            fetcher=fetcher or proveedor(),
            **kwargs,
        )


class CorridaTest(unittest.TestCase):
    def test_publica_las_dos_tablas_y_control_con_fuente_hash_y_exclusiones(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            r = correr(cfg)
            self.assertEqual(r["publicados"], ["2026-06"])
            self.assertEqual(
                pq.read_table(cfg.docs / "fi_balance/2026-06.parquet").num_rows, 84
            )
            self.assertEqual(
                pq.read_table(cfg.docs / "fi_resultados/2026-06.parquet").num_rows, 120
            )
            self.assertEqual(auditar(cfg.docs)["errores"], [])
            ctl = json.loads(cfg.control.read_text())
            self.assertEqual(ctl["periodos"]["2026-06"]["reglas_verificadas"], 44)
            self.assertTrue(ctl["periodos"]["2026-06"]["sha256_parquet"])
            for t in ("balance", "resultados"):
                fs = pq.read_table(cfg.docs / f"fi_{t}/2026-06.parquet").to_pylist()
                self.assertTrue(
                    all(f["sha256_archivo"] == registro()["sha256"] for f in fs)
                )
                self.assertTrue(all(type(f["valor_miles_mf"]) is int for f in fs))
            man = json.loads((cfg.raiz / "data_manifest.json").read_text())
            self.assertEqual(man["total_records"], 17 + 84 + 120)
            self.assertEqual(
                man["tables"][0], {"id": "otra_tabla", "registros_reales": 17}
            )

    def test_json_desafio_xml_incompleto_no_publican(self):
        for raw, html in (
            (b'{"error":"caido"}', None),
            (b"<IFRS>", None),
            (None, b"<html><script>challenge()</script></html>"),
        ):
            with self.subTest(raw=raw, html=html), tempfile.TemporaryDirectory() as tmp:
                cfg = make_root(Path(tmp))
                r = correr(cfg, proveedor(raw, html))
                self.assertEqual(r["publicados"], [])
                self.assertFalse(cfg.control.exists())
                self.assertEqual(r["periodos"]["2026-06"]["pendientes"], 1)

    def test_resultado_actual_malo_no_publica_aunque_cuadre_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            r = correr(cfg, proveedor(cambiar("InteresesYReajustes", valor=1)))
            self.assertEqual(r["publicados"], [])
            self.assertTrue(r["errores"])
            self.assertFalse(cfg.control.exists())

    def test_comparativo_malo_se_excluye_con_motivo_antes_de_publicar(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            r = correr(
                cfg, proveedor(cambiar("TotalActivo", "PeriodoAnualAnterior", valor=1))
            )
            self.assertEqual(r["publicados"], ["2026-06"])
            self.assertEqual(
                pq.read_table(cfg.docs / "fi_balance/2026-06.parquet").num_rows, 42
            )
            man = json.loads((cfg.docs / "fi_balance/manifest.json").read_text())
            self.assertEqual(man["contextos_excluidos"][0]["run_fondo"], "7002")
            self.assertEqual(auditar(cfg.docs)["errores"], [])

    def test_cotejo_fallido_no_publica(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            html = datos()[1].replace(b"3.560.527", b"3.560.528", 1)
            r = correr(cfg, proveedor(html=html), forzar=True)
            self.assertTrue(r["errores"])
            self.assertEqual(r["publicados"], [])

    def test_relectura_identica_es_idempotente_y_no_baja_xml_otra_vez(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            paths = [
                cfg.control,
                cfg.docs / "fi_balance/2026-06.parquet",
                cfg.docs / "fi_resultados/2026-06.parquet",
                cfg.raiz / "data_manifest.json",
            ]
            before = {p: p.read_bytes() for p in paths}
            calls = []
            r = correr(cfg, proveedor(llamadas=calls))
            self.assertEqual(len(calls), 0)
            self.assertEqual(r["publicados"], [])
            for p, b in before.items():
                self.assertEqual(p.read_bytes(), b)

    def test_reenvio_que_pierde_comparativo_conserva_todo_documento_previo(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            p = cfg.docs / "fi_balance/2026-06.parquet"
            antes = p.read_bytes()
            old = datos()[2]["archivo"]
            new = old.replace("_20260911_", "_20260912_")
            html = datos()[1].replace(old.encode(), new.encode())
            correr(
                cfg,
                proveedor(
                    cambiar("TotalActivo", "PeriodoAnualAnterior", valor=1), html
                ),
                forzar=True,
            )
            self.assertEqual(p.read_bytes(), antes)
            ctl = json.loads(cfg.control.read_text())
            r = ctl["periodos"]["2026-06"]["registros"]["7002"]
            self.assertEqual(r["archivo"], old)
            self.assertIn("pierde", r["actualizacion_rechazada"]["motivo"])

    def test_fuente_desaparecida_o_desafio_conservan_datos_previos(self):
        for html in (
            b"<html>Informacion Financiera. No existe informacion de la entidad para el periodo se\xc3\xb1alado.</html>",
            b"<html>challenge()</html>",
        ):
            with self.subTest(html=html), tempfile.TemporaryDirectory() as tmp:
                cfg = make_root(Path(tmp))
                correr(cfg)
                p = cfg.docs / "fi_balance/2026-06.parquet"
                before = p.read_bytes()
                correr(cfg, proveedor(html=html), forzar=True)
                self.assertEqual(p.read_bytes(), before)
                self.assertEqual(auditar(cfg.docs)["errores"], [])

    def test_sin_informacion_inicial_no_crea_cifras_ni_tablas_vacias(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            r = correr(
                cfg,
                proveedor(
                    html=b"<html>No existe informacion de la entidad para el periodo se\xc3\xb1alado.</html>"
                ),
            )
            self.assertEqual(r["publicados"], [])
            self.assertFalse(cfg.control.exists())
            self.assertEqual(
                m.cargar_progreso(cfg, "2026-06")["7002"]["estado"], "sin_informacion"
            )

    def test_sin_publicar_guarda_progreso_y_no_toca_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            r = correr(cfg, publicar=False)
            self.assertEqual(r["publicados"], [])
            self.assertFalse(cfg.control.exists())
            self.assertEqual(m.cargar_progreso(cfg, "2026-06")["7002"]["estado"], "ok")

    def test_sin_cache_reconstruye_desde_publicado_sin_perdida(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            shutil.rmtree(cfg.cache)
            r = correr(cfg)
            self.assertEqual(r["publicados"], [])
            self.assertEqual(auditar(cfg.docs)["errores"], [])

    def test_cache_alterada_se_rechaza_y_se_reconstruye_desde_publicado(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            p = cfg.cache / "progreso/2026-06.jsonl.gz"
            with gzip.open(p, "rt") as f:
                regs = [json.loads(s) for s in f]
            regs[0]["tablas"]["balance"]["PeriodoActual"]["TotalActivo"] = 1
            with gzip.open(p, "wt") as f:
                f.write(json.dumps(regs[0]) + "\n")
            correr(cfg)
            self.assertEqual(auditar(cfg.docs)["errores"], [])

    def test_reintenta_respuestas_de_desafio_sin_falso_hueco(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            get = proveedor()
            n = 0

            def fetch(url):
                nonlocal n
                n += 1
                return b"<html>challenge()</html>" if n == 1 else get(url)

            r = correr(cfg, fetch)
            self.assertEqual(r["publicados"], ["2026-06"])
            self.assertEqual(n, 3)

    def test_roll_back_si_falla_escritura_segunda_tabla(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            ctl = json.loads(cfg.control.read_text())
            estado = m.cargar_estado(cfg, "2026-06", ctl)
            paths = [
                cfg.control,
                cfg.docs / "fi_balance/2026-06.parquet",
                cfg.docs / "fi_resultados/2026-06.parquet",
            ]
            before = {p: p.read_bytes() for p in paths}
            oldctl = copy.deepcopy(ctl)
            for t in estado["7002"]["tablas"].values():
                for c in t.values():
                    for cod in c:
                        c[cod] *= 2
            original = m.pq.write_table

            def write(table, path, **kwargs):
                if "fi_resultados" in str(path):
                    raise OSError("disco simulado")
                return original(table, path, **kwargs)

            with (
                mock.patch.object(m.pq, "write_table", side_effect=write),
                self.assertRaises(OSError),
            ):
                m.publicar_periodo(
                    cfg, "2026-06", estado, ctl, {"7002": {"run": "7002"}}
                )
            for p, b in before.items():
                self.assertEqual(p.read_bytes(), b)
            self.assertEqual(ctl, oldctl)

    def test_no_puede_perder_resultados_con_balance_intacto(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            ctl = json.loads(cfg.control.read_text())
            estado = m.cargar_estado(cfg, "2026-06", ctl)
            before = (cfg.docs / "fi_resultados/2026-06.parquet").read_bytes()
            estado["7002"]["tablas"]["resultados"] = {}
            with self.assertRaises(x.ErrorFuente):
                m.publicar_periodo(
                    cfg, "2026-06", estado, ctl, {"7002": {"run": "7002"}}
                )
            self.assertEqual(
                (cfg.docs / "fi_resultados/2026-06.parquet").read_bytes(), before
            )

    def test_parquet_modificado_aunque_cuadre_no_pasa_el_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            p = cfg.docs / "fi_balance/2026-06.parquet"
            fs = pq.read_table(p).to_pylist()
            for f in fs:
                f["valor_miles_mf"] *= 2
            pq.write_table(pa.Table.from_pylist(fs, schema=m.ESQUEMA), p)
            self.assertTrue(any("SHA-256" in e for e in auditar(cfg.docs)["errores"]))


class PoliticaYCatalogosTest(unittest.TestCase):
    def test_calendario_plazos_y_rechazo_del_cierre_no_disponible(self):
        self.assertEqual(m.ultimo_disponible(date(2026, 10, 1)), "2026-06")
        self.assertEqual(m.ultimo_disponible(date(2026, 4, 1)), "2025-09")
        self.assertEqual(
            m.trimestres("2025-09", "2026-06"),
            ["2025-09", "2025-12", "2026-03", "2026-06"],
        )
        with (
            mock.patch.object(m, "_hoy", return_value=date(2026, 10, 1)),
            self.assertRaises(ValueError),
        ):
            m.correr(desde="2026-09", hasta="2026-09", registro={"x": {}})

    def test_todos_los_buckets_se_revisan_con_tres_corridas_al_mes(self):
        dias = [date(2026, m, d) for m in range(1, 13) for d in (5, 15, 25)]
        for run in ("7002", "9919", "7064"):
            self.assertTrue(
                any(m.toca_refresco(run, "2011-03", d, "2026-06") for d in dias)
            )
        self.assertTrue(
            m.toca_refresco("7002", "2026-06", date(2026, 10, 1), "2026-06")
        )

    def test_completitud_no_omite_fondos_sin_cartera_y_no_acepta_pendientes(self):
        ev = m.evaluar({"7002": {"estado": "ok"}}, {"7002": {}, "9919": {}})
        self.assertFalse(ev["puede_publicar"])
        self.assertEqual(ev["pendientes"], ["9919"])
        self.assertFalse(
            m.evaluar(
                {"7002": {"estado": "ok"}, "9919": {"estado": "rechazado"}},
                {"7002": {}, "9919": {}},
            )["puede_publicar"]
        )

    def test_registro_todo_publico_no_recorta_por_cartera_y_rechaza_duplicados(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = m.Config(raiz=Path(tmp))
            cfg.docs.mkdir(parents=True)
            p = cfg.docs / "fi_registro_fondos_universo.json"
            p.write_text(
                json.dumps(
                    [
                        {"run_fondo": "7002", "tipo_entidad": "FINRE"},
                        {"run_fondo": "9919", "tipo_entidad": "FIRES"},
                    ]
                )
            )
            self.assertEqual(set(m.cargar_registro(cfg)), {"7002", "9919"})
            p.write_text(
                json.dumps([{"run_fondo": "7002", "tipo_entidad": "FINRE"}] * 2)
            )
            with self.assertRaises(ValueError):
                m.cargar_registro(cfg)

    def test_catalogos_js_validos_dos_carpetas_campos_y_chips_sin_dobles_sumas(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            for name in (
                "duckdb_client.js",
                "sidebar.js",
                "data_viewer.js",
                "data_dictionary.js",
                "erd_graph.js",
            ):
                p = cfg.raiz / "docs/js" / name
                subprocess.run(
                    ["node", "--check", str(p)], check=True, capture_output=True
                )
                self.assertIn("fi_balance", p.read_text())
                self.assertIn("fi_resultados", p.read_text())
            sidebar = (cfg.raiz / "docs/js/sidebar.js").read_text()
            self.assertIn("contexto = 'PeriodoActual'", sidebar)
            self.assertIn("contexto = 'TrimestreActual'", sidebar)
            self.assertIn("moneda = 'CLP'", sidebar)
            ds = (cfg.raiz / "docs/js/data_dictionary.js").read_text()
            for c in x.COLUMNAS:
                self.assertIn(c, ds)
            vocab = json.loads((cfg.raiz / "docs/vocabulario.json").read_text())
            self.assertEqual(
                [
                    t["nombre"]
                    for t in vocab["tablas"]
                    if t["id"] in ("fi_balance", "fi_resultados")
                ],
                ["fi.balance", "fi.resultados"],
            )

    def test_todos_los_assets_comparten_una_version_de_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            correr(cfg)
            index = (cfg.raiz / "docs/index.html").read_text()
            versiones = set(
                re.findall(r'(?:src|href)="(?:css|js)/[^"?]+\?v=([^"]+)"', index)
            )
            self.assertEqual(len(versiones), 1)
            self.assertTrue(next(iter(versiones)).startswith("fi-eeff-"))

    def test_no_registra_tablas_inexistentes_y_catalogos_idempotentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_root(Path(tmp))
            self.assertFalse(actualizar_catalogos(cfg.raiz, cfg.docs))
            correr(cfg)
            paths = list((cfg.raiz / "docs/js").glob("*.js")) + [
                cfg.raiz / "data_manifest.json",
                cfg.raiz / "docs/vocabulario.json",
                cfg.raiz / "docs/index.html",
            ]
            before = {p: p.read_bytes() for p in paths}
            self.assertFalse(actualizar_catalogos(cfg.raiz, cfg.docs))
            for p, b in before.items():
                self.assertEqual(p.read_bytes(), b)

    def test_auditoria_detecta_claves_duplicadas_falta_de_cuenta_y_contextos_mezclados(
        self,
    ):
        fs = x.filas(registro())
        self.assertEqual(verificar_tablas(fs)["errores"], [])
        fs["balance"].append(copy.deepcopy(fs["balance"][0]))
        self.assertTrue(verificar_tablas(fs)["errores"])
        fs = x.filas(registro())
        fs["resultados"][0]["moneda"] = "USD"
        self.assertTrue(verificar_tablas(fs)["errores"])
        fs = x.filas(registro())
        fs["balance"].pop()
        self.assertTrue(verificar_tablas(fs)["errores"])

    def test_workflow_no_publica_con_auditoria_fallida(self):
        w = (RAIZ / ".github/workflows/fi_eeff.yml").read_text()
        self.assertIn("steps.auditar.outcome == 'success'", w)
        self.assertNotIn("if: always() && steps.procesar.outputs.publicado", w)


if __name__ == "__main__":
    unittest.main()
