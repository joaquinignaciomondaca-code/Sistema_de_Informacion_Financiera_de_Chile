import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "docs" / "outputs" / "bancos" / "bancos_maestro.json"
# Convención de RUT (pipelines/auto/rut.py): `rut` = cuerpo sin DV, `rut_dv` = con DV.
EXPECTED_RUTS = {
    "009": "97011000",
    "012": "97030000",
    "504": "97032000",
    "507": "97051000",
}
EXPECTED_RUT_DV = {
    "009": "97011000-3",
    "012": "97030000-7",
    "504": "97032000-8",
    "507": "97051000-1",
}


def dv_m11(body: str) -> str:
    weighted_sum = sum(
        int(digit) * multiplier
        for digit, multiplier in zip(reversed(str(body)), [2, 3, 4, 5, 6, 7] * len(str(body)))
    )
    remainder = 11 - weighted_sum % 11
    return "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)


def rut_consistente(rut: str, rut_dv: str) -> bool:
    """`rut` debe ser el cuerpo numérico y `rut_dv` = cuerpo-DV válido."""
    cuerpo = str(rut)
    if not re.fullmatch(r"\d{4,9}", cuerpo):
        return False
    return str(rut_dv) == f"{cuerpo}-{dv_m11(cuerpo)}"


class BankMasterIdentityTests(unittest.TestCase):
    def test_master_unique_codes_and_valid_rut_checksums(self):
        rows = json.loads(MASTER.read_text(encoding="utf-8"))
        codes = [row["codigo_institucion"] for row in rows]
        self.assertGreaterEqual(len(rows), 40)  # la lista crece sola (entidades.yml)
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(rut_consistente(row["rut"], row["rut_dv"]) for row in rows))

    def test_officially_cross_checked_ruts_stay_corrected(self):
        rows = json.loads(MASTER.read_text(encoding="utf-8"))
        by_code = {row["codigo_institucion"]: row for row in rows}
        for code, rut in EXPECTED_RUTS.items():
            with self.subTest(code=code):
                self.assertEqual(by_code[code]["rut"], rut)
                self.assertEqual(by_code[code]["rut_dv"], EXPECTED_RUT_DV[code])


if __name__ == "__main__":
    unittest.main()
