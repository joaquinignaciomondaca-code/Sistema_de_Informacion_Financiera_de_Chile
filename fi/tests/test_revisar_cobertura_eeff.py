"""Cobertura por categoría, vigencia y fechas sin red ni publicación de cifras."""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pyarrow as pa
import pyarrow.parquet as pq

from fi.scripts import eeff_xml as xml
from fi.scripts import revisar_cobertura_eeff as m

FIXTURES = Path(__file__).parent / "fixtures"


def financiero(run="10898", periodo="2026/06", encabezado=True, enlace=False):
    datos = f"<dd>{run}-7</dd>" if encabezado else "<dd></dd>"
    extra = (
        f'<a href="/institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo=FIEF2026846327_20260911_124849_{run}.xml">XML</a>'
        if enlace
        else f"<p>No existe información de la entidad para el periodo {periodo}.</p>"
    )
    return (
        f'<html><h2>Información financiera</h2><dl id="datos_ent"><dt>RUT:</dt>{datos}</dl>{extra}</html>'
    ).encode()


def identificacion(
    run="10898",
    tipo="Rescatable",
    inicio="17/08/2026",
    termino="",
    nombre="FONDO DE INVERSIÓN",
):
    filas = {
        "R.U.N. del Fondo": f"{run}-7",
        "Nombre Fondo Inversión": nombre,
        "Tipo de Fondo de Inversión:": tipo,
        "Vigencia": "Vigente",
        "Estado (indica si fondo está liquidado)": "",
        "Fecha Inicio Operaciones": inicio,
        "Fecha Término Operaciones": termino,
    }
    return (
        "<table>"
        + "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in filas.items())
        + "</table>"
    ).encode()


def lista(fondos):
    cabecera = (
        "<tr><th>R.U.T.</th><th>Entidad</th><th>Administrador</th><th>Estado</th></tr>"
    )
    filas = "".join(
        f"<tr><td>{f['run_fondo']}-7</td><td>{f['nombre_fondo']}</td><td>AGF</td><td>{f['estado_vigencia']}</td></tr>"
        for f in fondos
    )
    return (f"<html><table>{cabecera}{filas}</table></html>").encode()


def universo():
    return [
        {
            "run_fondo": run,
            "nombre_fondo": f"FONDO {run}",
            "tipo_entidad": tipo,
            "estado_vigencia": vig,
            "estado_eeff": "sin_informacion",
        }
        for run, tipo, vig in [
            ("10898", "FIRES", "Vigente"),
            ("10702", "FINRE", "Vigente"),
            ("7064", "FIRES", "No Vigente"),
            ("7001", "FINRE", "No Vigente"),
        ]
    ]


def proveedor(fondos=None, llamadas=None):
    fondos = fondos or universo()
    idx = {f["run_fondo"]: f for f in fondos}

    def get(url):
        if llamadas is not None:
            llamadas.append(url)
        q = parse_qs(urlsplit(url).query)
        if "entidad" in q:
            vig = "Vigente" if q["Estado"][0] == "VI" else "No Vigente"
            return lista(
                [
                    f
                    for f in fondos
                    if f["tipo_entidad"] == q["entidad"][0]
                    and f["estado_vigencia"] == vig
                ]
            )
        run = q["rut"][0]
        f = idx[run]
        if q["pestania"] == ["1"]:
            return identificacion(
                run,
                "No Rescatable" if f["tipo_entidad"] == "FINRE" else "Rescatable",
                inicio="",
            )
        if q["tipoentidad"][0] != f["tipo_entidad"]:
            return b"<html><h4>Sin informaci\xc3\xb3n.</h4></html>"
        return financiero(
            run,
            encabezado=q["vig"][0]
            == ("VI" if f["estado_vigencia"] == "Vigente" else "NV"),
        )

    return get


class LecturaCoberturaTest(unittest.TestCase):
    def test_no_rescatable_no_se_confunde_con_rescatable(self):
        self.assertEqual(m.tipo_de("No Rescatable"), "FINRE")
        self.assertEqual(m.tipo_de("Rescatable"), "FIRES")
        self.assertEqual(m.tipo_de(" NO   RESCATABLE "), "FINRE")
        self.assertIsNone(m.tipo_de("Fondo mutuo"))

    def test_identificacion_preserva_tipo_y_fecha_de_inicio_posterior(self):
        i = m.leer_identificacion(identificacion(), "10898")
        self.assertEqual(i["tipo_declarado"], "FIRES")
        self.assertEqual(i["fecha_inicio_operaciones"], "2026-08-17")
        self.assertEqual(m.motivo_temporal(i, "2026-06"), "inicio_posterior_al_cierre")

    def test_inicio_vacio_no_se_inventa_ni_se_afirma_sin_operaciones(self):
        i = m.leer_identificacion(
            identificacion("10702", "No Rescatable", inicio=""), "10702"
        )
        self.assertEqual(i["tipo_declarado"], "FINRE")
        self.assertIsNone(i["fecha_inicio_operaciones"])
        self.assertEqual(m.motivo_temporal(i, "2026-06"), "fecha_inicio_no_informada")

    def test_fechas_invalidas_no_parecen_vacias(self):
        with self.assertRaises(xml.ErrorTransitorio):
            m.leer_identificacion(identificacion(inicio="31/02/2026"), "10898")

    def test_identificacion_de_otro_run_no_se_acepta(self):
        with self.assertRaises(xml.ErrorTransitorio):
            m.leer_identificacion(identificacion(), "10702")

    def test_sartor_en_liquidacion_no_se_omite_por_ser_vigente(self):
        i = m.leer_identificacion(
            identificacion(inicio="01/01/2020", nombre="SARTOR EN LIQUIDACIÓN"), "10898"
        )
        self.assertEqual(
            m.motivo_temporal(i, "2026-06"), "en_liquidacion_sin_eeff_del_cierre"
        )

    def test_termino_anterior_se_distingue_de_inicio_posterior(self):
        i = m.leer_identificacion(
            identificacion(inicio="01/01/2020", termino="30/12/2025"), "10898"
        )
        self.assertEqual(m.motivo_temporal(i, "2026-06"), "termino_anterior_al_cierre")

    def test_inicio_antes_del_cierre_sin_termino_requiere_revision(self):
        i = m.leer_identificacion(identificacion(inicio="30/06/2026"), "10898")
        self.assertEqual(
            m.motivo_temporal(i, "2026-06"), "inicio_anterior_al_cierre_sin_eeff"
        )

    def test_ambos_tipos_fi_tienen_el_mismo_formato_de_fief(self):
        for nombre in ["7002_2026-06", "9919_2026-06", "7064_2021-12"]:
            run, p = nombre.split("_")
            with self.subTest(nombre=nombre):
                r = m.clasificar_sondeo(
                    (FIXTURES / (nombre + ".html")).read_bytes(), run, p
                )
                self.assertEqual(r["estado"], "xml")
                self.assertTrue(r["archivo"].endswith(f"_{run}.xml"))

    def test_ausencia_identificada_debe_ser_del_cierre(self):
        self.assertEqual(
            m.clasificar_sondeo(financiero(), "10898", "2026-06")["estado"],
            "sin_informacion",
        )
        with self.assertRaises(xml.ErrorTransitorio):
            m.clasificar_sondeo(financiero(periodo="2025/06"), "10898", "2026-06")

    def test_no_vigente_pedido_como_vi_no_es_ausencia_identificada(self):
        self.assertEqual(
            m.clasificar_sondeo(financiero(encabezado=False), "10898", "2026-06")[
                "estado"
            ],
            "sin_identificacion",
        )

    def test_sin_ficha_de_tipo_alternativo_no_es_sin_informacion(self):
        r = m.clasificar_sondeo(b"<h4>Sin informaci\xc3\xb3n.</h4>", "10898", "2026-06")
        self.assertEqual(r["estado"], "sin_ficha")

    def test_ficha_financiera_de_otro_run_es_pendiente(self):
        with self.assertRaises(xml.ErrorTransitorio):
            m.clasificar_sondeo(financiero("10702"), "10898", "2026-06")

    def test_challenge_json_y_corte_no_son_ausencia(self):
        for raw in [
            b'{"error":"fallo"}',
            b"<script>challenge()</script>",
            b"<html><h2>Informacion financiera</h2>",
        ]:
            with self.subTest(raw=raw), self.assertRaises(xml.ErrorTransitorio):
                m.clasificar_sondeo(raw, "10898", "2026-06")

    def test_no_vigentes_tambien_forman_parte_del_registro(self):
        fs = [
            f
            for f in universo()
            if f["tipo_entidad"] == "FIRES" and f["estado_vigencia"] == "No Vigente"
        ]
        self.assertEqual(m.leer_lista(lista(fs), "FIRES", "NV")[0]["run_fondo"], "7064")

    def test_lista_vigencia_erronea_o_duplicada_se_rechaza(self):
        f = universo()[0]
        for raw in [lista([f, f]), lista([f])]:
            with self.subTest(raw=raw), self.assertRaises(xml.ErrorTransitorio):
                m.leer_lista(raw, "FIRES", "NV")

    def test_lista_vacia_o_ilegible_no_es_padron_vacio(self):
        for raw in [lista([]), b"<html>challenge</html>"]:
            with self.subTest(raw=raw), self.assertRaises(xml.ErrorTransitorio):
                m.leer_lista(raw, "FIRES", "VI")

    def test_cambios_de_tipo_y_altas_no_se_silencian(self):
        viejo = universo()
        nuevo = copy.deepcopy(viejo)
        nuevo[0]["tipo_entidad"] = "FINRE"
        nuevo.append({**nuevo[0], "run_fondo": "10930"})
        r = m.cotejar_registro(viejo, nuevo)
        self.assertEqual(r["cambios_tipo"][0]["run"], "10898")
        self.assertEqual(r["altas_fuera_del_padron_local"][0]["run_fondo"], "10930")

    def test_un_run_en_dos_tipos_no_se_colapsa_ni_se_elige_un_tipo(self):
        fs = universo()
        r = m.cotejar_registro(fs, [*fs, {**fs[0], "tipo_entidad": "FINRE"}])
        self.assertEqual(r["fondos_cmf"], 4)
        self.assertEqual(r["filas_listas_cmf"], 5)
        self.assertEqual(r["tipos_ambiguos"], ["10898"])
        self.assertEqual(r["cambios_tipo"], [])

    def test_duplicado_de_vigencia_no_duplica_fondos_ni_inventa_vigencia(self):
        fs = universo()
        r = m.cotejar_registro(fs, [*fs, {**fs[0], "estado_vigencia": "No Vigente"}])
        self.assertEqual(r["fondos_cmf"], 4)
        self.assertEqual(r["registros_ambiguos"][0]["run"], "10898")
        self.assertEqual(r["tipos_ambiguos"], [])
        self.assertEqual(r["cambios_vigencia"], [])


class RevisionRedTest(unittest.TestCase):
    def test_revisa_cada_ausente_en_los_dos_tipos_y_ambas_vigencias(self):
        llamadas = []
        informe = {"periodo": "2026-06", "fondos": universo()}
        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(informe, Path(tmp), fetcher=proveedor(llamadas=llamadas))[
                "revision_cmf"
            ]
        self.assertTrue(r["revision_completa"])
        self.assertEqual(r["fondos_contrastados"], 4)
        self.assertEqual(r["enlace_en_otro_tipo"], [])
        q = [parse_qs(urlsplit(u).query) for u in llamadas]
        for run in ["10898", "10702", "7001", "7064"]:
            fichas = [
                p for p in q if p.get("rut") == [run] and p.get("pestania") == ["29"]
            ]
            self.assertEqual({p["tipoentidad"][0] for p in fichas}, {"FIRES", "FINRE"})
            self.assertEqual(len(fichas), 4 if run in ("7001", "7064") else 2)

    def test_error_red_no_se_cuenta_como_ausencia_ni_revision_completa(self):
        def get(url):
            if "rut=10898&" in url:
                raise OSError("CMF caída")
            return proveedor()(url)

        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(
                {"periodo": "2026-06", "fondos": universo()}, Path(tmp), fetcher=get
            )["revision_cmf"]
        self.assertFalse(r["revision_completa"])
        self.assertIn("10898", r["fondos_pendientes"])

    def test_tipo_alternativo_con_enlace_queda_como_hallazgo_no_publica(self):
        def get(url):
            q = parse_qs(urlsplit(url).query)
            if (
                q.get("rut") == ["10898"]
                and q.get("tipoentidad") == ["FINRE"]
                and q.get("pestania") == ["29"]
            ):
                return financiero(enlace=True)
            return proveedor()(url)

        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(
                {"periodo": "2026-06", "fondos": universo()}, Path(tmp), fetcher=get
            )["revision_cmf"]
            self.assertFalse(any(Path(tmp).rglob("*.parquet")))
        self.assertEqual(r["enlace_en_otro_tipo"], ["10898"])

    def test_rechazos_de_descarga_no_se_reconsultan_con_tipo_alternativo(self):
        fs = universo()
        fs[0]["estado_eeff"] = "rechazado"
        llamadas = []
        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(
                {"periodo": "2026-06", "fondos": fs},
                Path(tmp),
                fetcher=proveedor(llamadas=llamadas),
            )["revision_cmf"]
        self.assertEqual(r["fondos_contrastados"], 3)
        self.assertFalse(any("rut=10898&" in u for u in llamadas))
        self.assertFalse(any("ifrs_xml_verarchivo.php" in u for u in llamadas))

    def test_inicio_vacio_no_sustituye_falta_del_estado(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(
                {"periodo": "2026-06", "fondos": universo()},
                Path(tmp),
                fetcher=proveedor(),
            )["revision_cmf"]
        self.assertEqual(
            r["situacion_faltantes_vigentes"], {"fecha_inicio_no_informada": 2}
        )

    def test_fallo_auxiliar_vi_no_oculta_ausencia_identificada_nv(self):
        def get(url):
            if "rut=7001&" in url and "&vig=VI&" in url:
                raise OSError("ficha vacía al pedir no vigente con VI")
            return proveedor()(url)

        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(
                {"periodo": "2026-06", "fondos": universo()}, Path(tmp), fetcher=get
            )["revision_cmf"]
        self.assertTrue(r["revision_completa"])
        self.assertEqual(r["fondos_pendientes"], [])
        self.assertEqual(len(r["consultas_auxiliares_pendientes"]), 2)

    def test_fallo_en_vigencia_correcta_no_pasa_como_revision_completa(self):
        def get(url):
            if "rut=7001&" in url and "&vig=NV&" in url:
                raise OSError("ficha requerida incompleta")
            return proveedor()(url)

        with tempfile.TemporaryDirectory() as tmp:
            r = m.revisar_red(
                {"periodo": "2026-06", "fondos": universo()}, Path(tmp), fetcher=get
            )["revision_cmf"]
        self.assertFalse(r["revision_completa"])
        self.assertIn("7001", r["fondos_pendientes"])


class FuentesCacheTest(unittest.TestCase):
    def test_solo_reusa_bytes_verificados_y_conserva_fecha_original(self):
        url = "https://www.cmfchile.cl/ficha_prueba"
        raw = financiero()
        anterior = {
            "url": url,
            "estado": "sin_informacion",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "revisado_utc": "2026-10-01T22:00:00+00:00",
        }

        def no_red(u):
            raise AssertionError("no debe volver a descargar una fuente verificada")

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "fuentes").mkdir()
            (
                p / "fuentes" / (hashlib.sha256(url.encode()).hexdigest() + ".html")
            ).write_bytes(raw)
            f = m.Fuentes(
                p,
                time.monotonic() + 60,
                no_red,
                {"revision_cmf": {"listas": [anterior]}},
            )
            r = f.consultar(url, lambda b: m.clasificar_sondeo(b, "10898", "2026-06"))
        self.assertTrue(r["cache_sha256_verificado"])
        self.assertEqual(r["revisado_utc"], anterior["revisado_utc"])

    def test_cache_corrupta_no_se_acepta_y_se_vuelve_a_consultar(self):
        url = "https://www.cmfchile.cl/ficha_prueba"
        raw = financiero()
        llamadas = []
        anterior = {
            "url": url,
            "estado": "sin_informacion",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "revisado_utc": "2026-10-01T22:00:00+00:00",
        }

        def get(u):
            llamadas.append(u)
            return raw

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "fuentes").mkdir()
            (
                p / "fuentes" / (hashlib.sha256(url.encode()).hexdigest() + ".html")
            ).write_bytes(b"corrupto")
            f = m.Fuentes(
                p, time.monotonic() + 60, get, {"revision_cmf": {"listas": [anterior]}}
            )
            r = f.consultar(url, lambda b: m.clasificar_sondeo(b, "10898", "2026-06"))
        self.assertEqual(llamadas, [url])
        self.assertEqual(r["estado"], "sin_informacion")
        self.assertNotIn("cache_sha256_verificado", r)


class FuentesOficialesRegistroTest(unittest.TestCase):
    def test_cuatro_listas_originales_conservan_hash_y_no_duplican_9251(self):
        carpeta = FIXTURES / "cobertura"
        fuentes = json.loads((carpeta / "muestras.json").read_text())
        filas = []
        for nombre, r in fuentes.items():
            raw = gzip.decompress((carpeta / (nombre + ".html.gz")).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), r["sha256"])
            self.assertEqual(len(raw), r["bytes"])
            if nombre.startswith("registro_"):
                filas.extend(m.leer_lista(raw, r["tipo_entidad"], r["vigencia"]))
        informe = m.cotejar_registro([], filas)
        self.assertEqual(informe["filas_listas_cmf"], 1683)
        self.assertEqual(informe["fondos_cmf"], 1682)
        self.assertEqual([x["run"] for x in informe["registros_ambiguos"]], ["9251"])
        self.assertEqual(informe["tipos_ambiguos"], [])


class CoberturaLocalTest(unittest.TestCase):
    def preparar(self, d):
        fs = universo()
        fs[0]["estado_eeff"] = "ok"
        (d / "fi_registro_fondos_universo.json").write_text(json.dumps(fs))
        regs = {
            f["run_fondo"]: {
                "estado": f["estado_eeff"],
                "tipo_entidad": f["tipo_entidad"],
            }
            for f in fs
        }
        (d / "fi_eeff_control.json").write_text(
            json.dumps({"periodos": {"2026-06": {"registros": regs}}})
        )
        for tabla in ("balance", "resultados"):
            p = d / f"fi_{tabla}"
            p.mkdir()
            pq.write_table(
                pa.Table.from_pylist(
                    [
                        {
                            "run_fondo": "10898",
                            "tipo_entidad": "FIRES",
                            "contexto": "PeriodoActual",
                        }
                    ]
                ),
                p / "2026-06.parquet",
            )

    def test_censo_se_desglosa_por_tipo_y_vigencia_no_se_filtran_historicos(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.preparar(d)
            r = m.cobertura_local(d, "2026-06")
        self.assertEqual(sum(x["censados"] for x in r["resumen_local"]), 4)
        self.assertEqual(sum(x["ok"] for x in r["resumen_local"]), 1)
        self.assertEqual(len(r["fondos"]), 4)
        self.assertFalse(r["cierre_historico_completo"])

    def test_resultados_sin_fondo_presente_en_balance_no_pasan_el_cruce(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.preparar(d)
            tabla = pa.Table.from_pylist(
                [
                    {
                        "run_fondo": "10702",
                        "tipo_entidad": "FINRE",
                        "contexto": "PeriodoActual",
                    }
                ]
            )
            pq.write_table(tabla, d / "fi_resultados/2026-06.parquet")
            with self.assertRaisesRegex(ValueError, "resultados: fondos"):
                m.cobertura_local(d, "2026-06")

    def test_control_y_padron_con_tipos_discrepantes_no_pasan(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.preparar(d)
            p = d / "fi_eeff_control.json"
            c = json.loads(p.read_text())
            c["periodos"]["2026-06"]["registros"]["10702"]["tipo_entidad"] = "FIRES"
            p.write_text(json.dumps(c))
            with self.assertRaisesRegex(ValueError, "tipo no reconocido o distinto"):
                m.cobertura_local(d, "2026-06")

    def test_informe_local_no_afirma_comprobacion_de_red_no_hecha(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.preparar(d)
            texto = m.markdown(m.cobertura_local(d, "2026-06"))
        self.assertIn("Todavía no hay un contraste", texto)
        self.assertIn("no histórica", texto)


if __name__ == "__main__":
    unittest.main()
