import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "docs" / "outputs" / "bancos" / "bancos_maestro.json"
EXPECTED_RUTS = {
    "009": "97.011.000-3",
    "012": "97.030.000-7",
    "504": "97.032.000-8",
    "507": "97.051.000-1",
}


def valid_rut(value: str) -> bool:
    normalized = re.sub(r"[^0-9Kk]", "", value).upper()
    if len(normalized) < 2:
        return False
    body, check_digit = normalized[:-1], normalized[-1]
    weighted_sum = sum(
        int(digit) * multiplier
        for digit, multiplier in zip(reversed(body), [2, 3, 4, 5, 6, 7] * len(body))
    )
    remainder = 11 - weighted_sum % 11
    expected = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    return check_digit == expected


class BankMasterIdentityTests(unittest.TestCase):
    def test_master_has_40_unique_codes_and_valid_rut_checksums(self):
        rows = json.loads(MASTER.read_text(encoding="utf-8"))
        codes = [row["codigo_institucion"] for row in rows]
        self.assertEqual(len(rows), 40)
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(valid_rut(row["rut"]) for row in rows))

    def test_officially_cross_checked_ruts_stay_corrected(self):
        rows = json.loads(MASTER.read_text(encoding="utf-8"))
        by_code = {row["codigo_institucion"]: row["rut"] for row in rows}
        for code, rut in EXPECTED_RUTS.items():
            with self.subTest(code=code):
                self.assertEqual(by_code[code], rut)


if __name__ == "__main__":
    unittest.main()
