"""Regresiones de cobertura para la cuadratura de balances de securitizadoras."""
from __future__ import annotations

import unittest

import pandas as pd

from securitizadoras.scripts.audit_securitizadoras import resumir_cuadre_balance


CLAVES = {
    "periodo": "2009-12",
    "rut": "96847360",
    "tipo_balance": "individual",
    "estado_financiero": "ESF C/NC",
    "repeticion": 1,
}


def fila(cuenta: str, valor: int, **cambios) -> dict:
    return {**CLAVES, "cuenta": cuenta, "valor": valor, **cambios}


class ResumenCuadreBalanceTests(unittest.TestCase):
    def test_cubre_glosas_actuales_y_legacy_sin_perder_balances(self):
        datos = [
            fila("Total de activos", 100),
            fila("Total de patrimonio y pasivos", 100),
            fila("Activos, Total", 250, periodo="2010-03", rut="96847361"),
            fila(
                "Patrimonio Neto y Pasivos, Total",
                250,
                periodo="2010-03",
                rut="96847361",
            ),
        ]

        resumen = resumir_cuadre_balance(pd.DataFrame(datos))

        self.assertEqual(len(resumen), 2)
        self.assertTrue(resumen["verificable"].all())
        self.assertEqual(resumen["diferencia"].tolist(), [0, 0])

    def test_un_balance_sin_total_se_conserva_como_no_verificable(self):
        resumen = resumir_cuadre_balance(
            pd.DataFrame([fila("Total de activos", 100)])
        )

        self.assertEqual(len(resumen), 1)
        self.assertFalse(bool(resumen.iloc[0]["verificable"]))

    def test_aliases_que_se_contradicen_no_se_silencian(self):
        datos = [
            fila("Total de activos", 100),
            fila("Activos, Total", 101),
            fila("Total de patrimonio y pasivos", 100),
        ]

        resumen = resumir_cuadre_balance(pd.DataFrame(datos))

        self.assertTrue(bool(resumen.iloc[0]["conflicto"]))
        self.assertFalse(bool(resumen.iloc[0]["verificable"]))


if __name__ == "__main__":
    unittest.main()
