"""Configuración y taxonomía del monitor normativo CMF."""

from __future__ import annotations

CMF_LIST_URL = (
    "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php"
)
CMF_BASE_URL = "https://www.cmfchile.cl"
CMF_SOURCE_LABEL = "CMF · Legislación y normativa"
SCHEMA_VERSION = 1
ANALYSIS_VERSION = "2026-09-28.1"
DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_MAX_AI_CALLS = 10
DEFAULT_MAX_PDF_CHECKS = 120
MAX_PDF_BYTES = 18 * 1024 * 1024
MAX_PDF_PAGES = 50
MAX_TEXT_CHARS = 48_000
MAX_DESCRIPTION_CHARS = 8_000
MAX_SUMMARY_CHARS = 650

# Identificadores enlazados con el árbol de industrias del explorador.
SECTOR_LABELS = {
    "seguros": "Seguros de Vida y Generales",
    "agf": "Administradoras Generales de Fondos (AGF)",
    "ffmm": "Fondos Mutuos (FFMM)",
    "fi": "Fondos de Inversión (FI)",
    "pensiones": "Fondos de Pensiones",
    "bancos": "Banca Comercial",
    "macro": "Macroeconomía y Tasas",
    "factoring_leasing": "Factoring y Leasing",
    "corredoras_bolsa": "Corredoras de Bolsa",
    "securitizadoras": "Sociedades Securitizadoras",
    "patrimonios_separados": "Patrimonios Separados",
    "cooperativas": "Cooperativas de Ahorro y Crédito",
    "cajas_compensacion": "Cajas de Compensación",
    "sistemas_pago": "Sistemas de Pago",
    "fintech": "FinTech y Finanzas Abiertas",
}

# El explorador histórico usa este alias en el nodo AFP corporativo, mientras
# que el catálogo de datos lo denomina "pensiones".
SECTOR_ALIASES = {"afp_corporativo": "pensiones"}

EVENT_TYPES = (
    "consulta_publica",
    "nueva_norma",
    "modificacion",
    "derogacion",
    "circular_instruccion",
    "prorroga_o_aclaracion",
    "otro",
)

EFFECTIVE_DATE_PRECISIONS = ("dia", "mes", "inmediata", "sin_fecha")

DEFAULT_MODEL_FLASH_LITE = "gemini-3.5-flash-lite"
DEFAULT_MODEL_FLASH = "gemini-3.8-flash"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "event_type": {"type": "STRING", "enum": list(EVENT_TYPES)},
        "summary": {"type": "STRING"},
        "summary_evidence": {"type": "STRING"},
        "summary_evidence_page": {"type": "INTEGER"},
        "sectors": {
            "type": "ARRAY",
            "items": {"type": "STRING", "enum": list(SECTOR_LABELS)},
        },
        "sector_evidence": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "sector": {"type": "STRING", "enum": list(SECTOR_LABELS)},
                    "quote": {"type": "STRING"},
                    "page": {"type": "INTEGER"},
                },
                "required": ["sector", "quote", "page"],
            },
        },
        "affected_norms": {"type": "ARRAY", "items": {"type": "STRING"}},
        "norm_evidence": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "norm": {"type": "STRING"},
                    "quote": {"type": "STRING"},
                    "page": {"type": "INTEGER"},
                },
                "required": ["norm", "quote", "page"],
            },
        },
        "effective_date": {"type": "STRING"},
        "effective_date_precision": {
            "type": "STRING",
            "enum": list(EFFECTIVE_DATE_PRECISIONS),
        },
        "effective_date_evidence": {"type": "STRING"},
        "effective_date_page": {"type": "INTEGER"},
        "confidence": {"type": "STRING", "enum": ["alta", "media", "baja"]},
        "needs_human_review": {"type": "BOOLEAN"},
    },
    "required": [
        "event_type",
        "summary",
        "summary_evidence",
        "summary_evidence_page",
        "sectors",
        "sector_evidence",
        "affected_norms",
        "norm_evidence",
        "effective_date",
        "effective_date_precision",
        "effective_date_evidence",
        "effective_date_page",
        "confidence",
        "needs_human_review",
    ],
}
