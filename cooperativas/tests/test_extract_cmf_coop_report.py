import unittest

from cooperativas.scripts import extract_cmf_coop_report as x

# Cifras reales CMF julio 2026 (MM$), tomadas de la sonda.
REAL = {
    "activos": {"Coopeuch": [93542, 667248, 28000, 639248, 0, 3207219, 104590, 3102629, 2038901, 192445, 1818017, 28439, 0, 1063728, 127002, 4074312],
                "Capual": [3671, 8981, 8944, 0, 37, 99380, 18, 99362, 99362, 36484, 62878, 0, 0, 0, 4106, 117779]},
    "pasivos": {"Coopeuch": [3250652, 2420487, 235440, 1454358, 730689, 3598, 2813, 785, 617223, 6500, 533, 823660, 719872],
                "Capual": [82427, 77218, 4804, 53611, 18803, 0, 0, 0, 0, 1480, 0, 35352, 30194]},
    "resultados": {"Coopeuch": [220917, 2950, 8434, 8218, -1617, 238902, -66539, -66501, 0, -38, -106385, 65978, 0, 65978, -1804, 64174, 64174, 0, 58314],
                   "Capual": [9481, 252, 156, 582, 390, 10861, -2837, -2783, -54, 0, -5754, 2270, 0, 2270, -22, 2248, 2248, 0, 2284]},
    "margen": {"Coopeuch": [220917, 302598, 284684, 4889, 229246, 50549, 16225, 1689, -81681, -76437, -5244, 2950, 8467, 5637, 985, 1845, -5517],
               "Capual": [9481, 11206, 11206, 3, 11203, 0, 0, 0, -1725, -1644, -81, 252, 252, 252, 0, 0, 0]},
}
HEADERS = {
    "activos": ["Efectivo y depósitos en bancos", "Instrumentos financieros no derivados", "Colocaciones", "Provisiones Constituidas", "Activos Totales"],
    "pasivos": ["Pasivos", "Patrimonio", "Depósitos y Captaciones Totales", "Capital Pagado"],
    "resultados": ["Margen de intereses", "Comisiones Netas", "Gasto en provisiones", "Impuesto", "Castigos del ejercicio"],
    "margen": ["Margen de intereses", "Ingresos por intereses y reajustes", "Gastos por intereses y reajustes", "Comisiones netas"],
}
SHEET_NAMES = {"activos": "Activos Cooperativas", "pasivos": "Pasivos Cooperativas",
               "resultados": "Estado Resultados Coop", "margen": "Margen Interes - Comisiones"}


def sheet(key, data=None, extra_row=None, blank_col=True):
    data = data or REAL[key]
    width = len(next(iter(REAL[key].values())))
    head = [None] * width  # como en la planilla: frases en la primera columna de cada bloque combinado
    for i, h in enumerate(HEADERS[key][:-1]):
        head[i * 2] = h
    head[-1] = HEADERS[key][-1]
    rows = [["Volver"], [None, "(Cifras en millones de pesos)"], [None, "Instituciones (1):", None, *head], []]
    for name, vals in data.items():
        rows.append([None, name, *( [None] if blank_col else [] ), *vals])
    if extra_row:
        rows.append(extra_row)
    total = [sum(v[i] for v in data.values()) for i in range(len(next(iter(data.values()))))]
    rows += [[], [None, "Total Cooperativas", None, *total], [None, "(1) Notas"]]
    return rows


def workbook(**over):
    wb = {"Índice": [["x"]], "Definiciones Usadas": [["y"]]}
    for key, name in SHEET_NAMES.items():
        wb[name] = over.get(key) or sheet(key)
    return wb


class ParseTests(unittest.TestCase):
    def test_real_july_2026_parses_and_validates(self):
        parsed = x.parse_workbook(workbook())
        info = x.validate_period(parsed)
        self.assertEqual(info["cooperativas"], ["CAPUAL", "COOPEUCH"])
        rows = x.to_rows("2026-07", parsed, "u", "s")
        self.assertEqual(len(rows), 2 * (16 + 13 + 19 + 17))
        at = next(r for r in rows if r["cooperativa"] == "COOPEUCH" and r["codigo_concepto"] == "activos_totales")
        self.assertEqual((at["monto_mm_clp"], at["fecha_corte"], at["estado"]), (4074312, "2026-07-31", "balance"))
        ut = next(r for r in rows if r["cooperativa"] == "CAPUAL" and r["codigo_concepto"] == "resultado_ejercicio")
        self.assertEqual((ut["monto_mm_clp"], ut["base_monto"]), (2248, "acumulado del año a la fecha"))

    def test_float_values_from_xls_and_dash(self):
        data = {k: [float(v) for v in vals] for k, vals in REAL["pasivos"].items()}
        rows = sheet("pasivos", data)
        rows[4][6] = "---"  # un '---' se lee como 0 sólo si cuadra
        with self.assertRaises(ValueError):
            x.validate_period(x.parse_workbook(workbook(pasivos=rows)))

    def test_lautaro_rosas_maps_to_coonfia(self):
        self.assertEqual(x.coop_key("Lautaro Rosas (2)"), "lautaro rosas")
        self.assertEqual(x.COOPERATIVAS["lautaro rosas"][1], "COONFIA")


class FailClosedTests(unittest.TestCase):
    def test_wrong_column_count(self):
        data = {k: v[:-1] for k, v in REAL["activos"].items()}
        with self.assertRaisesRegex(ValueError, "montos"):
            x.parse_workbook(workbook(activos=sheet("activos", data)))

    def test_missing_header_phrase(self):
        rows = sheet("activos"); rows[2] = [None, "Instituciones", "Otra cosa"]
        with self.assertRaisesRegex(ValueError, "cabecera"):
            x.parse_workbook(workbook(activos=rows))

    def test_broken_subtotal(self):
        data = {k: list(v) for k, v in REAL["activos"].items()}
        data["Coopeuch"][6] += 500  # comerciales ya no suman al total de colocaciones
        with self.assertRaisesRegex(ValueError, "colocaciones"):
            x.validate_period(x.parse_workbook(workbook(activos=sheet("activos", data))))

    def test_assets_must_equal_liabilities_plus_equity(self):
        data = {k: list(v) for k, v in REAL["pasivos"].items()}
        data["Capual"][11] += 100; data["Capual"][12] += 100
        with self.assertRaisesRegex(ValueError, "pasivos \\+ patrimonio"):
            x.validate_period(x.parse_workbook(workbook(pasivos=sheet("pasivos", data))))

    def test_total_row_must_match(self):
        rows = sheet("resultados"); rows[-2][3] += 50
        with self.assertRaisesRegex(ValueError, "Total Cooperativas"):
            x.validate_period(x.parse_workbook(workbook(resultados=rows)))

    def test_unknown_cooperative(self):
        rows = sheet("activos", extra_row=[None, "Cooperativa Nueva", None, *REAL["activos"]["Capual"]])
        with self.assertRaisesRegex(ValueError, "no reconocida"):
            x.parse_workbook(workbook(activos=rows))

    def test_coop_sets_must_match_across_sheets(self):
        rows = sheet("margen", {"Coopeuch": REAL["margen"]["Coopeuch"]})
        with self.assertRaisesRegex(ValueError, "cooperativas"):
            x.validate_period(x.parse_workbook(workbook(margen=rows)))


class DeclaredDifferenceTests(unittest.TestCase):
    def test_small_source_difference_is_declared(self):
        data = {k: list(v) for k, v in REAL["resultados"].items()}
        data["Capual"][11] -= 4; data["Capual"][13] -= 4; data["Capual"][15] -= 4; data["Capual"][16] -= 4
        info = x.validate_period(x.parse_workbook(workbook(resultados=sheet("resultados", data))))
        d = info["diferencias_fuente_declaradas"]
        self.assertEqual([(i["cooperativa"], i["concepto"], i["diferencia_mm_clp"]) for i in d],
                         [("CAPUAL", "resultado_operacional_neto", -4)])


class WorkAreaTests(unittest.TestCase):
    def test_2019_11_work_area_to_the_right_is_ignored(self):
        rows = sheet("activos")
        rows[1] = rows[1] + [None] * 30 + ["VARIACIÓN MENSUAL"]  # cabecera que se extiende a la derecha
        for r in rows[4:]:
            if len(r) > 2 and r[1] in ("Coopeuch", "Capual", "Total Cooperativas"):
                r.extend([None] * 8 + [672, r[1], *r[3:]])
        x.validate_period(x.parse_workbook(workbook(activos=rows)))


class SpacerTests(unittest.TestCase):
    def test_internal_single_blank_spacers_are_allowed(self):
        rows = sheet("resultados")
        for r in rows[4:]:
            if len(r) > 10 and r[1] in ("Coopeuch", "Capual", "Total Cooperativas"):
                r[:] = r[:9] + [None] + r[9:15] + [None] + r[15:]
        x.validate_period(x.parse_workbook(workbook(resultados=rows)))

    def test_2019_11_small_gap_before_work_area(self):
        rows = sheet("pasivos")
        for r in rows[4:]:
            if len(r) > 2 and r[1] in ("Coopeuch", "Capual", "Total Cooperativas"):
                r.extend([None, None, 672, r[1], *r[3:]])
        x.validate_period(x.parse_workbook(workbook(pasivos=rows)))


class DiscoverTests(unittest.TestCase):
    def test_pairs_resource_with_article_label(self):
        page = ('<a href="articles-113058_recurso_1.xlsx?ts=1"></a>'
                '<a href="w4-article-113058.html">Reporte Financiero de Cooperativas de Ahorro y Crédito julio 2026</a>'
                '<a href="articles-44433_recurso_1.xls?ts=2"></a>'
                '<a href="w4-article-44433.html">Reporte Financiero de Cooperativas de Ahorro y Crédito enero 2017</a>')
        got = x.discover(page)
        self.assertEqual(sorted(got), ["2017-01", "2026-07"])
        self.assertTrue(got["2017-01"].endswith("articles-44433_recurso_1.xls?ts=2"))


if __name__ == "__main__":
    unittest.main()
