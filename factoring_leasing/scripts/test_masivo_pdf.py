"""La cola del masivo y el salto de lo ya leído. No baja PDFs."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "masivo", ROOT / "factoring_leasing" / "scripts" / "07_masivo_pdf.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_solo_entran_factoring_y_leasing():
    sociedades = mod.sociedades([
        {"rut": "1-1", "razon_social": "Factor", "es_factoring": 1, "es_leasing_financiero": 0, "es_leasing_habitacional": 0},
        {"rut": "2-2", "razon_social": "Leasing", "es_factoring": 0, "es_leasing_financiero": 1, "es_leasing_habitacional": 0},
        {"rut": "3-3", "razon_social": "Auto", "es_factoring": 0, "es_leasing_financiero": 0, "es_leasing_habitacional": 0},
    ])
    assert [row["rut"] for row in sociedades] == ["1-1", "2-2"]


def test_lo_mas_nuevo_va_primero_y_marzo_entra_aunque_no_este_en_la_serie():
    sociedades = [{"rut": "1-9", "razon_social": "Uno"}]
    serie = [
        {"rut": "1-9", "periodo": "2024-12"},
        {"rut": "1-9", "periodo": "2025-12"},
        {"rut": "9-9", "periodo": "2026-03"},
    ]
    documentos = mod.cola(sociedades, serie)
    assert [doc["periodo"] for doc in documentos] == ["2026-03", "2025-12", "2024-12"]
    assert documentos[0]["fila_api"] is None


def test_lo_ya_leido_no_se_repite_y_un_error_si():
    assert mod.debe_saltar({"version": mod.VERSION, "estado": "leido", "error": ""})
    assert mod.debe_saltar({"version": mod.VERSION, "estado": "marcado", "error": "", "notas_sin_leer": 2})
    assert not mod.debe_saltar({"version": mod.VERSION, "estado": "marcado", "error": "sin PDF"})
    assert not mod.debe_saltar({"version": mod.VERSION - 1, "estado": "leido", "error": ""})
    assert not mod.debe_saltar(None)


if __name__ == "__main__":
    for nombre in list(globals()):
        if nombre.startswith("test_"):
            globals()[nombre]()
    print("ok")
