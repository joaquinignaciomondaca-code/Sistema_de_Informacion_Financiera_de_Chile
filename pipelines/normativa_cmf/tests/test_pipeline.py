from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from pipelines.normativa_cmf import pipeline
from pipelines.normativa_cmf.audit import audit as audit_cmf


LISTING_HTML = """<!doctype html>
<html><body><table class="tabla-resultados"><thead><tr>
<th>Documento</th><th>Número</th><th>Fecha</th><th>Descripción</th>
</tr></thead><tbody>
<tr>
<td><a href="/normativa/ncg_777_2026.pdf">NCG N°777</a></td>
<td>777</td><td>14/09/2026</td>
<td>MODIFICA LA NORMA PARA FONDOS MUTUOS Y ADMINISTRADORAS GENERALES DE FONDOS.</td>
</tr>
<tr>
<td><a href="/normativa/cir_2379_2026.pdf">Circular N°2.379</a></td>
<td>2379</td><td>15/09/2026</td>
<td>IMPARTE INSTRUCCIONES PARA COMPAÑÍAS DE SEGUROS.</td>
</tr>
</tbody></table></body></html>"""


class ParseListingTests(unittest.TestCase):
    def test_parses_documents_and_independent_publication_dates(self):
        items = pipeline.parse_listing(LISTING_HTML)
        self.assertEqual(len(items), 2)
        by_number = {item["document_number"]: item for item in items}
        self.assertEqual(by_number["777"]["document_type"], "NCG")
        self.assertEqual(by_number["777"]["publication_date"], "2026-09-14")
        self.assertEqual(by_number["777"]["document_year"], "2026")
        self.assertEqual(by_number["2379"]["document_type"], "Circular")
        self.assertEqual(by_number["2379"]["title"], "Circular N°2.379")
        self.assertTrue(by_number["777"]["id"].startswith("cmf-"))

    def test_rejects_html_that_has_no_recognizable_document_rows(self):
        with self.assertRaises(pipeline.SourceUnavailable):
            pipeline.parse_listing("<html><body><h1>Maintenance</h1></body></html>")

    def test_recognized_empty_listing_is_not_mistaken_for_a_source_failure(self):
        html = """<table class="tabla-resultados"><thead><tr>
        <th>Documento</th><th>Número</th><th>Fecha de publicación</th><th>Descripción</th>
        </tr></thead><tbody></tbody></table>"""
        self.assertEqual(pipeline.parse_listing(html), [])

    def test_nonempty_listing_with_unrecognized_rows_still_fails_closed(self):
        html = """<table class="tabla-resultados"><thead><tr>
        <th>Documento</th><th>Número</th><th>Fecha de publicación</th><th>Descripción</th>
        </tr></thead><tbody><tr><td>NCG 777</td><td>777</td><td>14/09/2026</td>
        <td>MODIFICA LA NORMA PARA FONDOS MUTUOS Y ADMINISTRADORAS GENERALES DE FONDOS.</td>
        </tr></tbody></table>"""
        with self.assertRaises(pipeline.SourceUnavailable):
            pipeline.parse_listing(html)

    def test_canonical_url_discards_volatile_cmf_timestamp(self):
        one = "https://www.cmfchile.cl/sitio/aplic/serdoc/ver_sgd.php?s567=abc&secuencia=-1&t=123"
        two = "https://www.cmfchile.cl/sitio/aplic/serdoc/ver_sgd.php?t=999&s567=abc&secuencia=-1"
        self.assertEqual(pipeline.canonical_url(one), pipeline.canonical_url(two))

    def test_canonical_url_normalizes_official_root_domain_to_https_www(self):
        self.assertEqual(
            pipeline.canonical_url("http://cmfchile.cl/normativa/ncg_777_2026.pdf"),
            "https://www.cmfchile.cl/normativa/ncg_777_2026.pdf",
        )

    def test_rejects_document_links_outside_official_cmf_domain(self):
        html = """<table><tr>
        <td><a href="https://example.com/ncg_777_2026.pdf">NCG 777</a></td>
        <td>777</td><td>14/09/2026</td>
        <td>MODIFICA LA NORMA PARA FONDOS MUTUOS Y ADMINISTRADORAS GENERALES DE FONDOS.</td>
        </tr></table>"""
        with self.assertRaises(pipeline.SourceUnavailable):
            pipeline.parse_listing(html)

    def test_listing_query_uses_requested_start_date(self):
        params = pipeline.listing_params(datetime(2026, 9, 28, tzinfo=timezone.utc).date())
        self.assertEqual((params["dd"], params["mm"], params["aa"]), ("28", "09", "2026"))
        self.assertEqual(params["tiponorma"], "ALL")


class EvidenceValidationTests(unittest.TestCase):
    def test_only_supported_sector_and_effective_date_are_kept(self):
        pages = [
            {"page": 1, "text": "La presente norma se aplica a los fondos mutuos y sus administradoras."},
            {"page": 3, "text": "La presente circular entra en vigencia el 1 de enero de 2027."},
        ]
        raw = {
            "event_type": "modificacion",
            "summary": "Modifica obligaciones aplicables a fondos mutuos.",
            "summary_evidence": "se aplica a los fondos mutuos y sus administradoras",
            "summary_evidence_page": 1,
            "sectors": ["ffmm", "seguros"],
            "sector_evidence": [
                {"sector": "ffmm", "quote": "los fondos mutuos y sus administradoras", "page": 1},
                {"sector": "seguros", "quote": "compañías de seguros", "page": 1},
            ],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "2027-01-01",
            "effective_date_precision": "dia",
            "effective_date_evidence": "entra en vigencia el 1 de enero de 2027",
            "effective_date_page": 3,
            "confidence": "alta",
            "needs_human_review": False,
        }
        clean = pipeline._validate_analysis(raw, pages, "mock-model", pdf_text_available=True)
        self.assertEqual(clean["sectors"], ["ffmm"])
        self.assertEqual(clean["effective_date"], "2027-01-01")
        self.assertIn("sector_sin_evidencia_verificable", clean["review_flags"])
        self.assertTrue(clean["needs_human_review"])

    def test_effective_date_must_match_the_supported_quote(self):
        pages = [{
            "page": 2,
            "text": "La presente circular entra en vigencia el 1 de enero de 2027 para fondos mutuos.",
        }]
        raw = {
            "event_type": "nueva_norma",
            "summary": "Establece una fecha de vigencia para fondos mutuos.",
            "summary_evidence": "entra en vigencia el 1 de enero de 2027",
            "summary_evidence_page": 2,
            "sectors": ["ffmm"],
            "sector_evidence": [{"sector": "ffmm", "quote": "fondos mutuos", "page": 2}],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "2027-01-02",
            "effective_date_precision": "dia",
            "effective_date_evidence": "entra en vigencia el 1 de enero de 2027",
            "effective_date_page": 2,
            "confidence": "alta",
            "needs_human_review": False,
        }
        clean = pipeline._validate_analysis(raw, pages, "mock-model", pdf_text_available=True)
        self.assertEqual(clean["effective_date"], "")
        self.assertEqual(clean["effective_date_precision"], "sin_fecha")
        self.assertIn("vigencia_sin_evidencia_verificable", clean["review_flags"])
        self.assertTrue(clean["needs_human_review"])

    def test_malformed_confidence_is_downgraded_and_flagged_for_review(self):
        pages = [{"page": 1, "text": "La norma se aplica a los fondos mutuos y sus administradoras."}]
        raw = {
            "event_type": "modificacion",
            "summary": "Actualiza disposiciones para fondos mutuos.",
            "summary_evidence": "se aplica a los fondos mutuos y sus administradoras",
            "summary_evidence_page": 1,
            "sectors": ["ffmm"],
            "sector_evidence": [{"sector": "ffmm", "quote": "fondos mutuos y sus administradoras", "page": 1}],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "",
            "effective_date_precision": "sin_fecha",
            "effective_date_evidence": "",
            "effective_date_page": 0,
            "confidence": {"confidence": "alta"},
            "needs_human_review": False,
        }
        clean = pipeline._validate_analysis(raw, pages, "mock-model", pdf_text_available=True)
        self.assertEqual(clean["confidence"], "baja")
        self.assertIn("confianza_no_validada", clean["review_flags"])
        self.assertTrue(clean["needs_human_review"])

    def test_listing_only_evidence_cannot_publish_pdf_page_or_effective_date(self):
        self.assertFalse(pipeline._quote_is_supported(
            "fondos mutuos y sus administradoras",
            0,
            [{"page": 1, "text": "fondos mutuos y sus administradoras"}],
        ))
        raw = {
            "event_type": "nueva_norma",
            "summary": "La norma se aplica a fondos mutuos.",
            "summary_evidence": "La norma se aplica a fondos mutuos",
            "summary_evidence_page": 0,
            "sectors": ["ffmm"],
            "sector_evidence": [{"sector": "ffmm", "quote": "fondos mutuos y sus administradoras", "page": 0}],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "2027-01-01",
            "effective_date_precision": "dia",
            "effective_date_evidence": "entra en vigencia el 1 de enero de 2027",
            "effective_date_page": 0,
            "confidence": "media",
            "needs_human_review": False,
        }
        listing_description = "La norma se aplica a fondos mutuos y sus administradoras; entra en vigencia el 1 de enero de 2027."
        clean = pipeline._validate_analysis(
            raw,
            [{"page": 0, "text": listing_description}],
            "mock-model",
            pdf_text_available=False,
        )
        self.assertEqual(clean["sectors"], ["ffmm"])
        self.assertEqual(clean["effective_date"], "")
        self.assertEqual(clean["effective_date_precision"], "sin_fecha")
        self.assertIn("vigencia_sin_evidencia_verificable", clean["review_flags"])
        self.assertTrue(clean["needs_human_review"])

    def test_unverifiable_effective_date_is_not_published_as_fact(self):
        raw = {
            "event_type": "nueva_norma",
            "summary": "Nueva norma.",
            "summary_evidence": "Nueva norma publicada para el sector financiero",
            "summary_evidence_page": 1,
            "sectors": ["ffmm"],
            "sector_evidence": [{"sector": "ffmm", "quote": "fondos mutuos", "page": 1}],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "2027-01-01",
            "effective_date_precision": "dia",
            "effective_date_evidence": "fecha inventada",
            "effective_date_page": 1,
            "confidence": "alta",
            "needs_human_review": False,
        }
        clean = pipeline._validate_analysis(raw, [{"page": 1, "text": "fondos mutuos"}], "mock-model", pdf_text_available=True)
        self.assertEqual(clean["effective_date"], "")
        self.assertEqual(clean["effective_date_precision"], "sin_fecha")
        self.assertEqual(clean["analysis_status"], "pendiente")
        self.assertTrue(clean["needs_human_review"])

    def test_failed_flash_escalation_still_consumes_second_call(self):
        pages = [{"page": 1, "text": "La norma se aplica a los fondos mutuos y sus administradoras."}]
        lite = {
            "event_type": "modificacion",
            "summary": "Actualiza disposiciones para fondos mutuos.",
            "summary_evidence": "se aplica a los fondos mutuos",
            "summary_evidence_page": 1,
            "sectors": ["ffmm"],
            "sector_evidence": [{"sector": "ffmm", "quote": "fondos mutuos y sus administradoras", "page": 1}],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "",
            "effective_date_precision": "sin_fecha",
            "effective_date_evidence": "",
            "effective_date_page": 0,
            "confidence": "media",
            "needs_human_review": True,
        }
        with patch("pipelines.normativa_cmf.pipeline._call_gemini", side_effect=[lite, pipeline.GeminiError("HTTP 429")]) as call:
            analysis, calls_used = pipeline.analyze_document(
                {"title": "Circular de prueba", "description_cmf": ""},
                pages,
                api_key="test-key",
                model_flash_lite="mock-lite",
                model_flash="mock-flash",
                max_calls=2,
            )
        self.assertEqual(call.call_count, 2)
        self.assertEqual(calls_used, 2)
        self.assertEqual(analysis["ai_model"], "mock-lite")
        self.assertTrue(analysis["needs_human_review"])


class PdfExtractionTests(unittest.TestCase):
    def test_extracts_native_text_with_page_number(self):
        import fitz

        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Normativa aplicable a fondos mutuos y administradoras.")
        pdf_bytes = document.tobytes()
        document.close()

        pages = pipeline.extract_pdf_pages(pdf_bytes)
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["page"], 1)
        self.assertIn("fondos mutuos", pages[0]["text"])


class GeminiInteractionsApiTests(unittest.TestCase):
    def test_uses_interactions_rest_contract_and_standard_json_schema(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "status": "completed",
            "model": "gemini-3.6-flash",
            "steps": [{
                "type": "model_output",
                "content": [{"type": "text", "text": '{"event_type":"otro"}'}],
            }],
        }
        with patch("pipelines.normativa_cmf.pipeline.requests.post", return_value=response) as post:
            result = pipeline._call_gemini("test-key", "gemini-flash-lite-latest", "prompt de prueba")

        self.assertEqual(result, {"event_type": "otro", "_response_model": "gemini-3.6-flash"})
        recorded = pipeline._validate_analysis(
            result,
            [],
            "gemini-flash-lite-latest",
            pdf_text_available=False,
        )
        self.assertEqual(recorded["ai_model"], "gemini-3.6-flash")
        self.assertEqual(recorded["ai_model_requested"], "gemini-flash-lite-latest")
        self.assertEqual(pipeline.GEMINI_INTERACTIONS_URL, "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(post.call_args.args[0], pipeline.GEMINI_INTERACTIONS_URL)
        self.assertEqual(pipeline.GEMINI_API_REVISION, "2026-05-20")
        self.assertEqual(post.call_args.kwargs["headers"]["Api-Revision"], pipeline.GEMINI_API_REVISION)
        self.assertEqual(post.call_args.kwargs["headers"]["x-goog-api-key"], "test-key")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], "gemini-flash-lite-latest")
        self.assertEqual(pipeline.DEFAULT_MODEL_FLASH_LITE, "gemini-flash-lite-latest")
        self.assertEqual(pipeline.DEFAULT_MODEL_FLASH, "gemini-flash-latest")
        self.assertEqual(payload["input"], "prompt de prueba")
        self.assertIs(payload["store"], False)
        self.assertEqual(payload["generation_config"], {"max_output_tokens": 2400})
        self.assertEqual(payload["response_format"]["type"], "text")
        self.assertEqual(payload["response_format"]["mime_type"], "application/json")
        self.assertEqual(payload["response_format"]["schema"], pipeline.ANALYSIS_SCHEMA)
        self.assertEqual(pipeline.ANALYSIS_SCHEMA["type"], "object")
        self.assertEqual(pipeline.ANALYSIS_SCHEMA["properties"]["event_type"]["type"], "string")
        self.assertNotIn("contents", payload)
        self.assertNotIn("generationConfig", payload)

    def test_parses_outputs_text_shape_as_well_as_current_steps_shape(self):
        cases = [
            {
                "status": "completed",
                "outputs": [{"type": "text", "text": '{"event_type":"otro"}'}],
            },
            {
                "status": "completed",
                "steps": [{
                    "type": "thought",
                    "content": [{"type": "text", "text": "no se publica como salida"}],
                }, {
                    "type": "model_output",
                    "content": [
                        {"type": "text", "text": '{"event_type":"ot'},
                        {"type": "text", "text": 'ro"}'},
                    ],
                }],
            },
        ]
        for body in cases:
            with self.subTest(shape="steps" if "steps" in body else "outputs"):
                response = Mock(status_code=200)
                response.json.return_value = body
                with patch("pipelines.normativa_cmf.pipeline.requests.post", return_value=response):
                    result = pipeline._call_gemini("test-key", "gemini-3.8-flash", "prompt")
                    self.assertEqual(result["event_type"], "otro")

    def test_incomplete_interaction_is_not_accepted_as_a_classification(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "status": "incomplete",
            "steps": [{
                "type": "model_output",
                "content": [{"type": "text", "text": '{"event_type":"otro"}'}],
            }],
        }
        with patch("pipelines.normativa_cmf.pipeline.requests.post", return_value=response):
            with self.assertRaisesRegex(pipeline.GeminiError, "incomplete"):
                pipeline._call_gemini("test-key", "gemini-3.5-flash-lite", "prompt")

    def test_http_diagnostic_is_redacted_and_pending_error_stays_generic(self):
        secret = "test-secret-that-must-not-be-logged"
        response = Mock(status_code=403)
        response.json.return_value = {
            "error": {
                "status": "PERMISSION_DENIED",
                "message": f"API key: {secret} is not authorized for this method",
            },
        }
        with (
            patch("pipelines.normativa_cmf.pipeline.requests.post", return_value=response),
            patch("pipelines.normativa_cmf.pipeline.LOGGER.warning") as warning,
        ):
            with self.assertRaises(pipeline.GeminiError) as raised:
                pipeline._call_gemini(secret, "gemini-3.5-flash-lite", "prompt")

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(str(raised.exception), "HTTP 403")
        self.assertNotIn(secret, warning.call_args.args[1])
        self.assertIn("PERMISSION_DENIED", warning.call_args.args[1])
        self.assertIn("[redacted]", warning.call_args.args[1])


class AnalysisRoutingTests(unittest.TestCase):
    def test_escalates_ambiguous_flash_lite_result_to_flash(self):
        pages = [{
            "page": 1,
            "text": "La norma se aplica a los fondos mutuos y sus administradoras.",
        }]
        common = {
            "event_type": "modificacion",
            "summary": "Actualiza disposiciones para fondos mutuos.",
            "summary_evidence": "se aplica a los fondos mutuos",
            "summary_evidence_page": 1,
            "sectors": ["ffmm"],
            "sector_evidence": [{
                "sector": "ffmm",
                "quote": "fondos mutuos y sus administradoras",
                "page": 1,
            }],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "",
            "effective_date_precision": "sin_fecha",
            "effective_date_evidence": "",
            "effective_date_page": 0,
        }
        lite = {**common, "confidence": "media", "needs_human_review": True}
        flash = {**common, "confidence": "alta", "needs_human_review": False}
        with patch("pipelines.normativa_cmf.pipeline._call_gemini", side_effect=[lite, flash]) as call:
            analysis, calls_used = pipeline.analyze_document(
                {"title": "Circular de prueba", "description_cmf": ""},
                pages,
                api_key="test-key",
                model_flash_lite="mock-lite",
                model_flash="mock-flash",
                max_calls=2,
            )
        self.assertEqual(calls_used, 2)
        self.assertEqual([call.args[1] for call in call.call_args_list], ["mock-lite", "mock-flash"])
        self.assertEqual(analysis["ai_model"], "mock-flash")
        self.assertFalse(analysis["needs_human_review"])


class PersistenceTests(unittest.TestCase):
    def _event(self):
        return pipeline.parse_listing(LISTING_HTML)[0]

    @patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None)
    @patch("pipelines.normativa_cmf.pipeline.fetch_listing")
    @patch("pipelines.normativa_cmf.pipeline.fetch_pdf")
    @patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages")
    @patch("pipelines.normativa_cmf.pipeline.analyze_document")
    def test_run_persists_feed_without_secret_and_deduplicates_next_run(
        self, analyze, extract, fetch_pdf, fetch_listing, _sleep
    ):
        item = self._event()
        item["publication_date"] = "2026-06-14"
        item["source_fingerprint"] = "fixture-older-than-pdf-recheck-window"
        fetch_listing.return_value = [item]
        fetch_pdf.return_value = {
            "not_modified": False,
            "content": b"%PDF-test",
            "etag": "\"v1\"",
            "last_modified": None,
            "final_url": item["document_url"],
            "error": None,
        }
        extract.return_value = [{"page": 1, "text": "texto regulatorio"}]
        analyze.return_value = (
            {
                "event_type": "modificacion",
                "summary": "Resumen de prueba con evidencia.",
                "summary_evidence": "texto regulatorio",
                "summary_evidence_page": 1,
                "sectors": ["ffmm"],
                "sector_evidence": [{"sector": "ffmm", "quote": "texto regulatorio", "page": 1}],
                "affected_norms": [],
                "norm_evidence": [],
                "effective_date": "",
                "effective_date_precision": "sin_fecha",
                "effective_date_evidence": "",
                "effective_date_page": 0,
                "confidence": "media",
                "needs_human_review": False,
                "review_flags": [],
                "ai_model": "mock-lite",
                "analysis_version": pipeline.ANALYSIS_VERSION,
                "analysis_status": "complete",
                "analyzed_at": "2026-09-28T00:00:00Z",
            },
            1,
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            feed_path = Path(tmp) / "feed.json"
            first_time = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
            feed = pipeline.run_pipeline(
                lookback_days=365,
                pdf_recheck_days=45,
                api_key="do-not-store-this-key",
                state_path=state_path,
                feed_path=feed_path,
                now=first_time,
            )
            audit_cmf(feed_path, state_path, require_run=True)
            self.assertEqual(len(feed["events"]), 1)
            self.assertEqual(feed["events"][0]["sectors"], ["ffmm"])
            self.assertEqual(feed["run_summary"]["gemini_calls"], 1)
            self.assertEqual(feed["last_detected_at"], "2026-09-28T12:00:00Z")
            self.assertNotIn("do-not-store-this-key", feed_path.read_text(encoding="utf-8"))
            self.assertNotIn("do-not-store-this-key", state_path.read_text(encoding="utf-8"))

            # La segunda ejecución, al día siguiente, conserva el registro y
            # no repite análisis de un documento histórico ya validado.
            second_time = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
            feed2 = pipeline.run_pipeline(
                lookback_days=365,
                pdf_recheck_days=45,
                api_key="do-not-store-this-key",
                state_path=state_path,
                feed_path=feed_path,
                now=second_time,
            )
            audit_cmf(feed_path, state_path, require_run=True)
            self.assertEqual(len(feed2["events"]), 1)
            self.assertEqual(feed2["run_summary"]["gemini_calls"], 0)
            self.assertEqual(feed2["last_detected_at"], "2026-09-28T12:00:00Z")
            self.assertEqual(analyze.call_count, 1)
            self.assertEqual(fetch_pdf.call_count, 1)

    def test_empty_model_variables_fall_back_to_supported_model_names(self):
        item = self._event()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            feed_path = Path(tmp) / "feed.json"
            with (
                patch.dict("os.environ", {"GEMINI_MODEL_FLASH_LITE": "", "GEMINI_MODEL_FLASH": ""}),
                patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[item]),
                patch("pipelines.normativa_cmf.pipeline.fetch_pdf", return_value={
                    "not_modified": False,
                    "content": b"%PDF-test",
                    "etag": None,
                    "last_modified": None,
                    "final_url": item["document_url"],
                    "error": None,
                }),
                patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages", return_value=[{"page": 1, "text": "texto regulatorio"}]),
                patch("pipelines.normativa_cmf.pipeline.analyze_document", return_value=({}, 1)) as analyze,
                patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
            ):
                pipeline.run_pipeline(
                    api_key="test-key",
                    state_path=state_path,
                    feed_path=feed_path,
                    now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc),
                )

        self.assertEqual(analyze.call_args.kwargs["model_flash_lite"], pipeline.DEFAULT_MODEL_FLASH_LITE)
        self.assertEqual(analyze.call_args.kwargs["model_flash"], pipeline.DEFAULT_MODEL_FLASH)

    def test_changed_document_stays_pending_when_api_or_call_budget_is_unavailable(self):
        scenarios = [
            ("", 10, "API de análisis no disponible en esta ejecución"),
            ("test-key", 0, "Límite de llamadas de análisis alcanzado en esta ejecución"),
        ]
        for api_key, max_ai_calls, expected_flag in scenarios:
            with self.subTest(expected_flag=expected_flag), tempfile.TemporaryDirectory() as tmp:
                item = self._event()
                previous = {
                    **item,
                    "source_fingerprint": "previous-source-version",
                    "analysis_status": "complete",
                    "analysis_version": "previous-analysis-version",
                    "summary": "Resumen previo conservado mientras se revisa el cambio.",
                    "summary_evidence": "cita anterior del documento",
                    "summary_evidence_page": 1,
                    "sectors": ["ffmm"],
                    "sector_evidence": [{"sector": "ffmm", "quote": "cita anterior del documento", "page": 1}],
                    "review_flags": [
                        "Límite de descargas PDF alcanzado en esta ejecución",
                        "HTTP 403",
                    ],
                    "needs_human_review": False,
                }
                state_path = Path(tmp) / "state.json"
                feed_path = Path(tmp) / "feed.json"
                state_path.write_text(json.dumps({"schema_version": 1, "items": {item["id"]: {}}}), encoding="utf-8")
                feed_path.write_text(json.dumps({"schema_version": 1, "events": [previous]}), encoding="utf-8")

                with (
                    patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[item]),
                    patch("pipelines.normativa_cmf.pipeline.fetch_pdf", return_value={
                        "not_modified": False,
                        "content": b"%PDF-updated",
                        "etag": None,
                        "last_modified": None,
                        "final_url": item["document_url"],
                        "error": None,
                    }),
                    patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages", return_value=[{"page": 1, "text": "texto nuevo del documento"}]),
                    patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
                ):
                    feed = pipeline.run_pipeline(
                        api_key=api_key,
                        max_ai_calls=max_ai_calls,
                        state_path=state_path,
                        feed_path=feed_path,
                        now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc),
                    )

                event = next(row for row in feed["events"] if row["id"] == item["id"])
                self.assertEqual(event["analysis_status"], "pendiente")
                self.assertEqual(event["summary"], previous["summary"])
                self.assertTrue(event["needs_human_review"])
                self.assertIn(expected_flag, event["review_flags"])
                self.assertNotIn("Límite de descargas PDF alcanzado en esta ejecución", event["review_flags"])
                self.assertNotIn("HTTP 403", event["review_flags"])
                self.assertEqual(feed["run_summary"]["pending_analysis"], 1)

    def test_failed_gemini_call_consumes_the_budget_before_processing_next_document(self):
        items = pipeline.parse_listing(LISTING_HTML)
        items[0]["id"] = "cmf-first-pending"
        items[1]["id"] = "cmf-second-pending"
        for index, item in enumerate(items):
            item["source_fingerprint"] = f"fixture-{index}"
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            feed_path = Path(tmp) / "feed.json"
            with (
                patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=items),
                patch("pipelines.normativa_cmf.pipeline.fetch_pdf", side_effect=lambda url, **kwargs: {
                    "not_modified": False,
                    "content": b"%PDF-test",
                    "etag": None,
                    "last_modified": None,
                    "final_url": url,
                    "error": None,
                }),
                patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages", return_value=[{"page": 1, "text": "texto documental suficiente para analizar"}]),
                patch("pipelines.normativa_cmf.pipeline._call_gemini", side_effect=pipeline.GeminiError("HTTP 403", status_code=403)) as gemini_call,
                patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
            ):
                feed = pipeline.run_pipeline(
                    api_key="test-key",
                    max_ai_calls=10,
                    max_pdf_checks=2,
                    state_path=state_path,
                    feed_path=feed_path,
                    now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc),
                )
            gemini_call.assert_called_once()
            self.assertEqual(feed["run_summary"]["gemini_calls"], 1)
            self.assertEqual(feed["run_summary"]["pending_analysis"], 2)
            events = {event["id"]: event for event in feed["events"]}
            self.assertTrue(all(event["analysis_status"] == "pendiente" for event in events.values()))
            self.assertTrue(any("HTTP 403" in event["review_flags"] for event in events.values()))
            self.assertTrue(any(
                "API de análisis suspendida tras HTTP 403 en esta ejecución" in event["review_flags"]
                for event in events.values()
            ))
            audit_cmf(feed_path, state_path, require_run=True)

    def test_pending_old_analysis_redownloads_pdf_when_api_returns(self):
        item = self._event()
        item["publication_date"] = "2025-12-14"  # Fuera de la ventana corta de re-chequeo PDF.
        item["source_fingerprint"] = "fixture-old-publication"
        analysis = {
            "event_type": "modificacion",
            "summary": "Actualiza disposiciones para fondos mutuos.",
            "summary_evidence": "fondos mutuos y sus administradoras",
            "summary_evidence_page": 1,
            "sectors": ["ffmm"],
            "sector_evidence": [{"sector": "ffmm", "quote": "fondos mutuos y sus administradoras", "page": 1}],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "",
            "effective_date_precision": "sin_fecha",
            "effective_date_evidence": "",
            "effective_date_page": 0,
            "confidence": "alta",
            "needs_human_review": False,
            "review_flags": [],
            "ai_model": "mock-lite",
            "analysis_version": pipeline.ANALYSIS_VERSION,
            "analysis_status": "complete",
            "analyzed_at": "2026-09-29T12:00:00Z",
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            feed_path = Path(tmp) / "feed.json"
            pdf_result = {
                "not_modified": False,
                "content": b"%PDF-stable-document",
                "etag": "\"v1\"",
                "last_modified": None,
                "final_url": item["document_url"],
                "error": None,
            }
            with (
                patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[item]),
                patch("pipelines.normativa_cmf.pipeline.fetch_pdf", return_value=pdf_result) as first_pdf,
                patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages", return_value=[{
                    "page": 1,
                    "text": "La norma se aplica a fondos mutuos y sus administradoras.",
                }]),
                patch("pipelines.normativa_cmf.pipeline.analyze_document") as first_analysis,
                patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
            ):
                first_feed = pipeline.run_pipeline(
                    api_key="",
                    state_path=state_path,
                    feed_path=feed_path,
                    now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc),
                )
                first_pdf.assert_called_once()
                first_analysis.assert_not_called()
                first_event = next(row for row in first_feed["events"] if row["id"] == item["id"])
                self.assertEqual(first_event["analysis_status"], "pendiente")

            with (
                patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[item]),
                patch("pipelines.normativa_cmf.pipeline.fetch_pdf", return_value=pdf_result) as retry_pdf,
                patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages", return_value=[{
                    "page": 1,
                    "text": "La norma se aplica a fondos mutuos y sus administradoras.",
                }]),
                patch("pipelines.normativa_cmf.pipeline.analyze_document", return_value=(analysis, 1)) as retry_analysis,
                patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
            ):
                second_feed = pipeline.run_pipeline(
                    api_key="test-key",
                    state_path=state_path,
                    feed_path=feed_path,
                    now=datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
                )
                self.assertIsNone(retry_pdf.call_args.kwargs["previous"], "al reintentar análisis se vuelve a bajar el PDF completo")
                retry_analysis.assert_called_once()

            audit_cmf(feed_path, state_path, require_run=True)
            second_event = next(row for row in second_feed["events"] if row["id"] == item["id"])
            self.assertEqual(second_event["analysis_status"], "complete")
            self.assertEqual(second_event["sectors"], ["ffmm"])

    def test_pdf_download_budget_keeps_new_items_pending_and_resumes_them(self):
        item = self._event()
        analysis = {
            "event_type": "otro",
            "summary": "Resumen regulatorio respaldado por el documento.",
            "summary_evidence": "texto regulatorio suficiente",
            "summary_evidence_page": 1,
            "sectors": [],
            "sector_evidence": [],
            "affected_norms": [],
            "norm_evidence": [],
            "effective_date": "",
            "effective_date_precision": "sin_fecha",
            "effective_date_evidence": "",
            "effective_date_page": 0,
            "confidence": "media",
            "needs_human_review": True,
            "review_flags": ["sin_industria_asignada"],
            "ai_model": "mock-lite",
            "analysis_version": pipeline.ANALYSIS_VERSION,
            "analysis_status": "complete",
            "analyzed_at": "2026-09-29T12:00:00Z",
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            feed_path = Path(tmp) / "feed.json"
            with (
                patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[item]),
                patch("pipelines.normativa_cmf.pipeline.fetch_pdf") as deferred_pdf,
                patch("pipelines.normativa_cmf.pipeline.analyze_document") as deferred_analysis,
                patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
            ):
                first_feed = pipeline.run_pipeline(
                    api_key="test-key",
                    max_pdf_checks=0,
                    state_path=state_path,
                    feed_path=feed_path,
                    now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc),
                )
                deferred_pdf.assert_not_called()
                deferred_analysis.assert_not_called()
            first_event = next(row for row in first_feed["events"] if row["id"] == item["id"])
            self.assertEqual(first_event["pdf_status"], "pendiente_limite")
            self.assertEqual(first_event["analysis_status"], "pendiente")

            with (
                patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[item]),
                patch("pipelines.normativa_cmf.pipeline.fetch_pdf", return_value={
                    "not_modified": False,
                    "content": b"%PDF-resumed",
                    "etag": None,
                    "last_modified": None,
                    "final_url": item["document_url"],
                    "error": None,
                }) as resumed_pdf,
                patch("pipelines.normativa_cmf.pipeline.extract_pdf_pages", return_value=[{"page": 1, "text": "texto regulatorio suficiente"}]),
                patch("pipelines.normativa_cmf.pipeline.analyze_document", return_value=(analysis, 1)),
                patch("pipelines.normativa_cmf.pipeline.time.sleep", return_value=None),
            ):
                second_feed = pipeline.run_pipeline(
                    api_key="test-key",
                    max_pdf_checks=1,
                    state_path=state_path,
                    feed_path=feed_path,
                    now=datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
                )
                self.assertIsNone(resumed_pdf.call_args.kwargs["previous"])
            second_event = next(row for row in second_feed["events"] if row["id"] == item["id"])
            self.assertEqual(second_event["analysis_status"], "complete")
            self.assertEqual(second_event["pdf_status"], "texto_extraible")

    @patch("pipelines.normativa_cmf.pipeline.fetch_listing", return_value=[])
    def test_valid_empty_listing_is_a_successful_check_not_a_source_failure(self, fetch_listing):
        with tempfile.TemporaryDirectory() as tmp:
            feed_path = Path(tmp) / "feed.json"
            state_path = Path(tmp) / "state.json"
            feed = pipeline.run_pipeline(
                api_key="",
                state_path=state_path,
                feed_path=feed_path,
                now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc),
            )
            audit_cmf(feed_path, state_path, require_run=True)
            self.assertEqual(feed["status"], "ok")
            self.assertEqual(feed["events"], [])
            self.assertEqual(feed["run_summary"]["listed_records"], 0)
            fetch_listing.assert_called_once()

    @patch("pipelines.normativa_cmf.pipeline.fetch_listing", side_effect=pipeline.SourceUnavailable("fallo de origen"))
    def test_source_failure_does_not_publish_a_false_empty_feed(self, fetch_listing):
        with tempfile.TemporaryDirectory() as tmp:
            feed_path = Path(tmp) / "feed.json"
            state_path = Path(tmp) / "state.json"
            with self.assertRaises(pipeline.SourceUnavailable):
                pipeline.run_pipeline(state_path=state_path, feed_path=feed_path)
            self.assertFalse(feed_path.exists())
            self.assertFalse(state_path.exists())


if __name__ == "__main__":
    unittest.main()
