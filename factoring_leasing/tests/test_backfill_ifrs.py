"""Descarga masiva en cuarentena; pruebas sin red ni escrituras en el sitio."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

SPEC = importlib.util.spec_from_file_location('backfill_ifrs', Path(__file__).resolve().parents[1] / 'scripts/backfill_ifrs.py')
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)
CATALOG = {'96655860': {'rut': '96655860-1', 'segmento': 'Factoring', 'nombre': 'FACTORING SECURITY S.A.'}}


def fixture(period='202206', rut='96655860', name='FACTORING SECURITY S.A.'):
    lines = []
    for kind, state, currency in [('I', 'ESF C/NC', 'CLP'), ('C', 'ESF C/NC', 'USD')]:
        for account, value in [('Total de activos', '435359519000'),
                               ('Total de pasivos', '376903204000'), ('Patrimonio total', '58456315000')]:
            lines.append(f'{period};{rut};{name};{kind};{currency};{account};{value};TAX CI;{state}')
    lines.append(f'{period};{rut};{name};I;CLP;Ganancia (pérdida), antes de impuestos;8148312000;TAX CI;ERFG')
    lines.append('202206;12345678;OTRA;I;CLP;Total de activos;1;TAX CI;ESF C/NC')
    return ('\n'.join(lines) + '\n').encode()


class BackfillTests(unittest.TestCase):
    def test_index_annual_and_quarterly_links(self):
        html = b'''<html><a href="ver_archivo.php?inicio=202203&amp;termino=202212">2022</a>
        <a href="ver_archivo.php?inicio=202603&termino=202603">Marzo 2026</a></html>'''
        self.assertEqual(b.periods_from_index(html), ['202203','202206','202209','202212','202603'])

    def test_index_does_not_accept_error_page(self):
        with self.assertRaises(ValueError):
            b.periods_from_index(b'ACCION NO PERMITIDA')

    def test_all_accounts_preserved_separate_by_statement_and_context(self):
        balance, income, stats = b.parse_period(fixture(), '202206', CATALOG)
        self.assertEqual((len(balance), len(income), stats['entidades']), (6, 1, 1))
        self.assertEqual({r['tipo_balance'] for r in balance}, {'I', 'C'})
        self.assertEqual({r['moneda_archivo'] for r in balance}, {'CLP','USD'})
        self.assertEqual(balance[0]['valor_archivo'], 435359519000)
        self.assertFalse(any(r['cuenta'].startswith('Ganancia') for r in balance))
        self.assertNotIn('resultado', stats)

    def test_previous_entity_name_not_forced_to_current(self):
        balance, _, stats = b.parse_period(fixture(name='NOMBRE HISTORICO S.A.'), '202206', CATALOG)
        self.assertEqual(stats['nombres_distintos_catalogo'], 1)
        self.assertEqual(balance[0]['nombre_reportado'], 'NOMBRE HISTORICO S.A.')
        self.assertFalse(balance[0]['identidad_nombre_coincide_catalogo'])

    def test_missing_target_is_explicit(self):
        balance, income, stats = b.parse_period(fixture(rut='12345678'), '202206', CATALOG)
        self.assertEqual((balance, income, stats['estado']), ([], [], 'sin_rut_catalogo'))

    def test_wrong_period_and_duplicate_kept_not_summed(self):
        with self.assertRaisesRegex(ValueError, 'período'):
            b.parse_period(fixture(period='202209'), '202206', CATALOG)
        duplicate = fixture().splitlines()[0]
        balance, income, stats = b.parse_period(fixture() + duplicate + b'\n', '202206', CATALOG)
        self.assertEqual(stats['cuentas_contexto_repetidas'], 1)
        self.assertEqual((len(balance), len(income)), (7, 1))
        self.assertEqual(balance[-1]['repeticion_contexto'], 2)
        self.assertEqual(balance[-1]['valor_archivo'], 435359519000)

    def test_noninteger_kept_as_text_not_zero(self):
        balance, _, stats = b.parse_period(fixture().replace(b'435359519000', b'NO_APLICA'), '202206', CATALOG)
        self.assertEqual(stats['importes_no_enteros'], 2)  # individual y consolidado
        self.assertIsNone(balance[0]['valor_archivo'])
        self.assertEqual(balance[0]['valor_texto_original'], 'NO_APLICA')
        self.assertFalse(balance[0]['valor_es_entero'])
        with self.assertRaisesRegex(ValueError, 'no es el archivo'):
            b.parse_period(b'<html>error</html>', '202206', CATALOG)

    def test_resume_skips_saved_period_and_keeps_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            index = b'<html><a href="ver_archivo.php?inicio=202203&termino=202206">2022</a></html>'
            seen = []
            def fetch(url):
                seen.append(url)
                return index if url == b.INDEX else fixture(period=url.split('inicio=')[1][:6])
            args = SimpleNamespace(out=out, catalog=Path(tmp) / 'catalog.json', batch=1)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            self.assertEqual(b.run(args, fetch), 0)
            self.assertTrue((out/'periodos/202206/_complete.json').is_file())
            self.assertFalse((out/'periodos/202203/_complete.json').exists())
            self.assertEqual(b.run(args, fetch), 0)
            self.assertTrue((out/'periodos/202203/_complete.json').is_file())
            self.assertEqual(len(seen), 4) # 2 index + 2 unique archive downloads
            self.assertEqual(len(b.pd.read_parquet(out/'periodos/202206/balance.parquet')), 6)
            self.assertEqual(len(b.pd.read_parquet(out/'periodos/202206/resultados.parquet')), 1)
            self.assertEqual(b.run(args, fetch), 0)
            self.assertEqual(len(seen), 5) # only index on completed run

    def test_failure_does_not_mark_period_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = SimpleNamespace(out=out, catalog=Path(tmp)/'catalog.json', batch=2)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            def fetch(url):
                return b'<html><a href="ver_archivo.php?inicio=202206&termino=202206">1</a></html>'
            self.assertEqual(b.run(args, fetch), 1)
            self.assertFalse((out/'periodos/202206/_complete.json').exists())
            self.assertEqual(json.loads((out/'resumen.json').read_text())['estado_global'], 'parcial_con_errores_sin_publicar')

    def test_failed_old_period_does_not_block_new_and_resume_retries_only_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = SimpleNamespace(out=out, catalog=Path(tmp)/'catalog.json', batch=3)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            index = b'<html><a href="ver_archivo.php?inicio=202203&termino=202209">2022</a></html>'
            downloads = []
            def fetch(url):
                if url == b.INDEX:
                    return index
                period = url.split('inicio=')[1][:6]
                downloads.append(period)
                return b'<html>CMF 500</html>' if period == '202203' else fixture(period=period)
            self.assertEqual(b.run(args, fetch), 0)
            self.assertEqual(downloads, ['202209', '202206', '202203'])
            self.assertEqual(json.loads((out/'resumen.json').read_text())['pendientes'], ['202203'])
            downloads.clear()
            self.assertEqual(b.run(args, fetch), 0)
            self.assertEqual(downloads, ['202203'])
            self.assertEqual(json.loads((out/'resumen.json').read_text())['completados_total'], 2)

    def test_annual_fallback_only_selected_quarter(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = SimpleNamespace(out=out, catalog=out/'catalog.json', batch=1)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            index = b'<html><a href="ver_archivo.php?inicio=200903&termino=200912">2009</a></html>'
            requests = []
            def fetch(url):
                requests.append(url)
                if url == b.INDEX:
                    return index
                if url.endswith('inicio=200912&termino=200912'):
                    return fixture(period='200912')
                if url.endswith('inicio=200909&termino=200909'):
                    return fixture(period='200909')
                if url.endswith('inicio=200906&termino=200906'):
                    return fixture(period='200906')
                if url.endswith('inicio=200903&termino=200903'):
                    return b'<html>CMF 500</html>'
                if url.endswith('inicio=200903&termino=200912'):
                    return fixture(period='200903') + fixture(period='200906')
                raise AssertionError(url)
            # Saltar primero 3 períodos para probar respaldo directo.
            catalog_hash = b.hashlib.sha256(args.catalog.read_bytes()).hexdigest()
            for period in ('200912', '200909', '200906'):
                bal, inc, stats = b.parse_period(fixture(period=period), period, CATALOG)
                stats.update(periodo=period, schema=b.SCHEMA_VERSION, sha256_catalogo=catalog_hash,
                             filas_balance=len(bal), filas_resultados=len(inc))
                b.save_period(out, period, bal, inc, stats)
            self.assertEqual(b.run(args, fetch), 0)
            report = json.loads((out/'periodos/200903/_complete.json').read_text())
            self.assertTrue(report['respaldo_anual'])
            self.assertEqual(report['fuente_archivo'].split('inicio=')[1], '200903&termino=200912')
            rows = b.pd.read_parquet(out/'periodos/200903/balance.parquet')
            self.assertEqual(set(rows['periodo']), {'2009-03'})
            self.assertEqual(json.loads((out/'resumen.json').read_text())['completados_total'], 4)

    def test_broken_cache_is_not_treated_as_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = SimpleNamespace(out=out, catalog=Path(tmp)/'catalog.json', batch=1)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            index = b'<html><a href="ver_archivo.php?inicio=202206&termino=202206">2022</a></html>'
            def fetch(url):
                return index if url == b.INDEX else fixture()
            self.assertEqual(b.run(args, fetch), 0)
            self.assertTrue(b.valid_cached(out, '202206', b.hashlib.sha256(args.catalog.read_bytes()).hexdigest()))
            (out/'periodos/202206/resultados.parquet').unlink()
            self.assertFalse(b.valid_cached(out, '202206', b.hashlib.sha256(args.catalog.read_bytes()).hexdigest()))
            self.assertEqual(b.run(args, fetch), 0)
            self.assertTrue((out/'periodos/202206/resultados.parquet').exists())

    def test_catalog_accepts_canonical_and_legacy_rut_formats(self):
        """El maestro publicado usa rut=cuerpo (C) + rut_dv (B); antes usaba rut con DV."""
        esperado = {'96655860': {'rut': '96655860-1', 'segmento': 'Factoring',
                                 'nombre': 'FACTORING SECURITY S.A.'}}
        canonical = {'rut': '96655860', 'rut_dv': '96655860-1', 'rut_completo': '96.655.860-1',
                     'segmento': 'Factoring', 'razon_social': 'FACTORING SECURITY S.A.'}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            path.write_text(json.dumps([canonical]))
            self.assertEqual(b.load_catalog(path), esperado)
            # Formatos anteriores del mismo catálogo: B (cuerpo-DV) y A (con puntos).
            for legacy in ('96655860-1', '96.655.860-1'):
                path.write_text(json.dumps([{'rut': legacy, 'segmento': 'Factoring',
                                             'razon_social': 'FACTORING SECURITY S.A.'}]))
                self.assertEqual(b.load_catalog(path), esperado)
            # Sin DV publicado: se calcula el oficial (módulo 11), no se inventa otro.
            path.write_text(json.dumps([{'rut': '96655860', 'segmento': 'Factoring',
                                         'razon_social': 'FACTORING SECURITY S.A.'}]))
            self.assertEqual(b.load_catalog(path), esperado)

    def test_catalog_rejects_duplicate_inconsistent_or_invalid_rut(self):
        base = {'segmento': 'Factoring', 'razon_social': 'FACTORING SECURITY S.A.'}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            casos = [
                ([{**base, 'rut': '96655860', 'rut_dv': '96655860-1'},
                  {**base, 'rut': '96655860', 'rut_dv': '96655860-1'}], 'duplicado'),
                ([{**base, 'rut': '96655860', 'rut_dv': '76002293-4'}], 'inconsistente'),
                ([{**base, 'rut': 'NO-ES-RUT'}], 'inválido'),
                ([{**base, 'rut': ''}], 'inválido'),
                ([], 'vacío'),
            ]
            for rows, motivo in casos:
                path.write_text(json.dumps(rows))
                with self.assertRaises(ValueError, msg=motivo):
                    b.load_catalog(path)

    def test_run_with_canonical_catalog_labels_rows_as_published(self):
        """La extracción sigue indexando por cuerpo y rotulando con el RUT del catálogo."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = SimpleNamespace(out=out, catalog=Path(tmp) / 'catalog.json', batch=1)
            args.catalog.write_text(json.dumps([{'rut': '96655860', 'rut_dv': '96655860-1',
                                                 'rut_completo': '96.655.860-1',
                                                 'segmento': 'Factoring',
                                                 'razon_social': 'FACTORING SECURITY S.A.'}]))
            index = b'<html><a href="ver_archivo.php?inicio=202206&termino=202206">2022</a></html>'
            self.assertEqual(b.run(args, lambda url: index if url == b.INDEX else fixture()), 0)
            rows = b.pd.read_parquet(out / 'periodos/202206/balance.parquet')
            self.assertEqual(set(rows['rut_cuerpo']), {'96655860'})
            self.assertEqual(set(rows['rut']), {'96655860-1'})
            self.assertEqual(json.loads((out / 'resumen.json').read_text())['rut_catalogo'], 1)

    def test_published_master_catalog_loads(self):
        """Guardia de regresión: el maestro publicado real debe cargar sin red ni parches."""
        self.assertTrue(b.CATALOG.is_file(), f'falta el catálogo publicado: {b.CATALOG}')
        catalog = b.load_catalog()
        self.assertGreaterEqual(len(catalog), 28)
        for body, meta in catalog.items():
            self.assertTrue(body.isdigit())
            self.assertEqual(b.formato(meta['rut']), 'B')
            self.assertEqual(b.cuerpo(meta['rut']), body)
            self.assertTrue(meta['nombre'].strip())
            self.assertTrue(meta['segmento'].strip())

class _Reloj(datetime):
    """`datetime` con un `now()` controlado: la prueba decide cuándo «se descargó» cada cosa."""
    ahora = datetime(2027, 3, 1, 12, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls.ahora


class ReedicionCmfTests(unittest.TestCase):
    """La CMF reedita cierres viejos; la caché por trimestre no debe dejarlos viejos para siempre."""

    @staticmethod
    def _indice(actualizado=''):
        fecha = f'(actualizado: {actualizado})' if actualizado else ''
        return (f'<html><p><a href="ver_archivo.php?inicio=202206&termino=202206">2022</a></p>'
                f'<p>{fecha}</p></html>').encode()

    def setUp(self):
        self.real_datetime = b.datetime
        b.datetime = _Reloj
        _Reloj.ahora = datetime(2027, 3, 1, 12, 0, tzinfo=timezone.utc)   # cada prueba parte igual
        self.addCleanup(setattr, b, 'datetime', self.real_datetime)

    def _entorno(self, tmp):
        out = Path(tmp)
        args = SimpleNamespace(out=out, catalog=out / 'catalog.json', batch=5)
        args.catalog.write_text(json.dumps([{'rut': '96655860-1', 'segmento': 'Factoring',
                                             'razon_social': 'FACTORING SECURITY S.A.'}]))
        estado = {'indice': self._indice(), 'fallar': False}
        descargas = []

        def fetch(url):
            if url == b.INDEX:
                return estado['indice']
            descargas.append(url)
            return b'<html>CMF 500</html>' if estado['fallar'] else fixture(period='202206')
        return out, args, estado, descargas, fetch

    def test_el_trimestre_solo_se_baja_otra_vez_si_la_cmf_lo_reedito_despues_de_la_descarga(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, args, estado, descargas, fetch = self._entorno(tmp)
            _Reloj.ahora = datetime(2027, 3, 1, 12, 0, tzinfo=timezone.utc)
            self.assertEqual(b.run(args, fetch), 0)
            self.assertEqual(len(descargas), 1)

            # Sin fecha en el índice, o con una anterior a la descarga: se reutiliza la caché.
            b.run(args, fetch)
            estado['indice'] = self._indice('15/02/2027 10:00')
            b.run(args, fetch)
            self.assertEqual(len(descargas), 1)
            self.assertEqual(json.loads((out / 'resumen.json').read_text())['periodos_reeditados_cmf'], [])

            # La CMF reedita el 02/03 a las 10:00 (13:00 UTC), después de la descarga guardada.
            _Reloj.ahora = datetime(2027, 3, 2, 15, 0, tzinfo=timezone.utc)
            estado['indice'] = self._indice('02/03/2027 10:00')
            self.assertEqual(b.run(args, fetch), 0)
            self.assertEqual(len(descargas), 2)
            self.assertEqual(json.loads((out / 'resumen.json').read_text())['periodos_reeditados_cmf'], ['202206'])
            meta = json.loads((out / 'periodos/202206/_complete.json').read_text())
            self.assertEqual(meta['fecha_descarga_utc'], '2027-03-02T15:00:00+00:00')

            # Ya refrescado: la corrida siguiente no lo baja de nuevo.
            b.run(args, fetch)
            self.assertEqual(len(descargas), 2)
            self.assertEqual(json.loads((out / 'resumen.json').read_text())['periodos_reeditados_cmf'], [])

    def test_una_reedicion_que_no_se_pudo_bajar_deja_la_serie_incompleta_sin_perder_lo_guardado(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, args, estado, descargas, fetch = self._entorno(tmp)
            self.assertEqual(b.run(args, fetch), 0)
            antes = len(b.pd.read_parquet(out / 'periodos/202206/balance.parquet'))
            _Reloj.ahora = datetime(2027, 3, 2, 15, 0, tzinfo=timezone.utc)
            estado['indice'] = self._indice('02/03/2027 10:00')
            estado['fallar'] = True
            b.run(args, fetch)
            resumen = json.loads((out / 'resumen.json').read_text())
            # Fail-closed: con un cierre vencido y sin refrescar, no se declara completa la serie.
            self.assertEqual(resumen['pendientes'], ['202206'])
            self.assertEqual(resumen['estado_global'], 'parcial_con_errores_sin_publicar')
            # Y la copia anterior sigue ahí para el reintento.
            self.assertEqual(len(b.pd.read_parquet(out / 'periodos/202206/balance.parquet')), antes)

    def test_valid_cached_ignora_fechas_si_no_hay_fecha_de_descarga(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, args, estado, descargas, fetch = self._entorno(tmp)
            b.run(args, fetch)
            marcador = out / 'periodos/202206/_complete.json'
            meta = json.loads(marcador.read_text())
            meta.pop('fecha_descarga_utc')
            marcador.write_text(json.dumps(meta))
            digest = meta['sha256_catalogo']
            reedicion = datetime(2099, 1, 1, tzinfo=timezone.utc)
            self.assertTrue(b.valid_cached(out, '202206', digest, reedicion))


if __name__ == '__main__':
    unittest.main()
