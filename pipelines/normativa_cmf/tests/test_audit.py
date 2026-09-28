from __future__ import annotations

import copy
import unittest

from pipelines.normativa_cmf.audit import validate_feed


class FeedAuditTests(unittest.TestCase):
    def _feed(self):
        return {
            "schema_version": 1,
            "status": "ok",
            "source_url": "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php",
            "last_checked_at": "2026-09-28T12:00:00Z",
            "run_summary": {
                "listed_records": 1,
                "new_or_changed_records": 1,
                "pdf_checks": 1,
                "gemini_calls": 1,
                "pending_analysis": 0,
                "unassigned_records": 0,
            },
            "events": [{
                "id": "cmf-test",
                "publication_date": "2026-09-14",
                "date_precision": "dia",
                "document_url": "https://www.cmfchile.cl/normativa/ncg_777_2026.pdf",
                "document_sha256": "a" * 64,
                "event_type": "modificacion",
                "summary": "Modifica disposiciones aplicables a fondos mutuos.",
                "summary_evidence": "se aplica a los fondos mutuos",
                "summary_evidence_page": 1,
                "sectors": ["ffmm"],
                "sector_evidence": [{
                    "sector": "ffmm",
                    "quote": "fondos mutuos y sus administradoras",
                    "page": 1,
                }],
                "affected_norms": ["NCG N° 777"],
                "norm_evidence": [{
                    "norm": "NCG N° 777",
                    "quote": "modifica la NCG 777",
                    "page": 2,
                }],
                "effective_date": "",
                "effective_date_precision": "sin_fecha",
                "effective_date_evidence": "",
                "effective_date_page": 0,
                "confidence": "alta",
                "needs_human_review": False,
                "review_flags": [],
                "analysis_status": "complete",
            }],
        }

    def test_validates_complete_evidence_backed_event(self):
        self.assertEqual(validate_feed(self._feed(), require_run=True), [])

    def test_rejects_sector_assignment_without_matching_evidence(self):
        feed = self._feed()
        feed["events"][0]["sector_evidence"] = []
        errors = validate_feed(feed)
        self.assertTrue(any("industria sin una cita" in error for error in errors))

    def test_pending_event_is_allowed_but_cannot_claim_analysis_complete(self):
        feed = self._feed()
        event = feed["events"][0]
        event.update({
            "analysis_status": "pendiente",
            "summary": "",
            "summary_evidence": "",
            "summary_evidence_page": 0,
            "sectors": [],
            "sector_evidence": [],
            "affected_norms": [],
            "norm_evidence": [],
            "needs_human_review": True,
            "review_flags": ["API de análisis no disponible en esta ejecución"],
        })
        feed["run_summary"]["pending_analysis"] = 1
        feed["run_summary"]["unassigned_records"] = 1
        self.assertEqual(validate_feed(feed), [])

    def test_rejects_effective_date_that_conflicts_with_its_quote(self):
        feed = self._feed()
        event = feed["events"][0]
        event.update({
            "effective_date": "2027-01-02",
            "effective_date_precision": "dia",
            "effective_date_evidence": "Entra en vigencia el 1 de enero de 2027.",
            "effective_date_page": 3,
        })
        errors = validate_feed(feed)
        self.assertTrue(any("vigencia incompatible" in error for error in errors))

    def test_rejects_malformed_confidence_without_crashing(self):
        feed = self._feed()
        feed["events"][0]["confidence"] = {"confidence": "alta"}
        errors = validate_feed(feed)
        self.assertTrue(any("confidence no es una categoría válida" in error for error in errors))

    def test_rejects_invalid_evidence_page_types(self):
        feed = copy.deepcopy(self._feed())
        feed["events"][0]["sector_evidence"][0]["page"] = True
        errors = validate_feed(feed)
        self.assertTrue(any("evidencia de industria mal formada" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
