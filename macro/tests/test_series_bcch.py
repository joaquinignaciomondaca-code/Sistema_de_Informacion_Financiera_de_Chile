"""Pruebas sin red del catálogo amplio de series BCCh (formato largo, incremental)."""
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from macro.scripts import series_bcch as sb


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        salida = raiz / "docs" / "outputs" / "macro"
        salida.mkdir(parents=True)
        (raiz / "data_manifest.json").write_text(json.dumps({"tables": [{"id": "x", "registros_reales": 5}]}))
        self.p = [patch.object(sb, "RAIZ", raiz), patch.object(sb, "SALIDA", salida),
                  patch.object(sb, "CARPETA", salida / "series"),
                  patch.object(sb, "CATALOGO_PQ", salida / "macro_series_catalogo.parquet"),
                  patch.dict("os.environ", {"BCCH_EMAIL": "u", "BCCH_PASSWORD": "p"})]
        for x in self.p:
            x.start()
        self.raiz = raiz
        self.llamadas = []

    def tearDown(self):
        for x in self.p:
            x.stop()
        self.tmp.cleanup()

    def api(self, datos, errores=()):
        def falsa(serie_id, desde, hasta, usuario, clave):
            self.llamadas.append((serie_id, desde))
            if serie_id in errores:
                raise sb.ErrorApi("BCCh código -5: serie no existe")
            return f"Título {serie_id}", [(f, v) for f, v in datos.get(serie_id, []) if f >= desde]
        return patch.object(sb, "consultar", side_effect=falsa)


class Pruebas(Base):
    def test_catalogo_bien_formado(self):
        self.assertGreaterEqual(len(sb.CATALOGO), 50)
        for c in sb.CATALOGO:
            self.assertIn(c["frecuencia"], sb.FRECUENCIA, c)
            self.assertTrue(c["serie_id"][0] in "FG", c)

    def test_backfill_incremental_y_sin_borrar(self):
        hoy = date.today()
        d = [((hoy - timedelta(days=i)).isoformat(), 900.0 + i) for i in range(40, 0, -1)]
        datos = {"F073.TCO.PRE.Z.D": d, "F019.PPB.PRE.44.D": [("2015-03-02", 1200.5)]}
        with self.api(datos, errores={"F019.PPB.PRE.45.D"}):
            self.assertEqual(sb.main(["--claves", "usd_clp", "oro", "plata"]), 0)
        self.assertTrue(all(desde == sb.DESDE for _, desde in self.llamadas))
        df = sb.cargar()
        self.assertEqual(len(df), 41)
        cat = pd.read_parquet(sb.CATALOGO_PQ).set_index("clave")
        self.assertEqual(cat.loc["plata", "estado"][:6], "error:")
        self.assertEqual(cat.loc["oro", "titulo_bcch"], "Título F019.PPB.PRE.44.D")
        self.assertEqual(cat.loc["usd_clp", "observaciones"], 40)
        man = json.loads((self.raiz / "data_manifest.json").read_text())
        self.assertIn("macro_series", {t["id"] for t in man["tables"]})
        self.assertEqual(man["total_records"], 5 + 41 + len(sb.CATALOGO))
        # Segunda corrida: consulta solo la ventana; la API "olvida" un día viejo y revisa uno.
        self.llamadas.clear()
        d2 = [(f, v) for f, v in d[-15:] if f != d[-12][0]]
        d2[-1] = (d2[-1][0], 1.0)
        with self.api({"F073.TCO.PRE.Z.D": d2}):
            self.assertEqual(sb.main(["--claves", "usd_clp"]), 0)
        self.assertEqual(self.llamadas[0][1], (date.fromisoformat(d[-1][0]) - timedelta(days=10)).isoformat())
        df = sb.cargar()
        usd = df[df.clave == "usd_clp"].set_index("fecha")["valor"]
        self.assertEqual(len(usd), 40)                 # nada se borró
        self.assertEqual(usd[d[-1][0]], 1.0)           # la revisión se aplicó

    def test_todas_fallan_no_escribe(self):
        with self.api({}, errores={c["serie_id"] for c in sb.CATALOGO}):
            self.assertEqual(sb.main(["--claves", "usd_clp", "oro"]), 1)
        self.assertFalse(sb.CATALOGO_PQ.exists())

    def test_descarta_futuro(self):
        futuro = (date.today() + timedelta(days=3)).isoformat()
        with self.api({"F073.UFF.PRE.Z.D": [("2020-01-01", 28000.0), (futuro, 1.0)]}):
            sb.main(["--claves", "uf"])
        self.assertEqual(sb.cargar()["fecha"].tolist(), ["2020-01-01"])


if __name__ == "__main__":
    unittest.main()
