# Publicaciones automáticas (GitHub Actions)

Inventario de todo lo que se actualiza solo. Regla común: cada workflow corre **3 veces al mes**
(salvo macro, que es diario), es **incremental** (lo ya publicado y cerrado no se vuelve a
descargar) y **fail-closed** (un período que no pasa la validación no se publica; se reintenta en
la corrida siguiente). Tras publicar en `main`, el mismo workflow despliega GitHub Pages.

| Sector | Fuente | Días (UTC) | Script | Salida |
| :--- | :--- | :--- | :--- | :--- |
| Bancos | CMF, archivos mensuales B1/B2/R1 | 1, 11, 21 | `bancos/scripts/publish_cmf_bank_period.py` (`bancos_cmf_mensual.yml`) | `docs/outputs/bancos/` |
| AGF, securitizadoras, CCAF (+ altas de las listas de CCAF y factoring/leasing) | CMF, TXT trimestral de estados IFRS de todas las sociedades | 2, 12, 22 | `pipelines/ifrs_sectores/actualizar.py` (`ifrs_sectores.yml`) | `docs/outputs/{agf,securitizadoras,cajas_compensacion}/`, `ccaf_maestro`, `factoring_leasing_maestro`, `docs/outputs/entidades/novedades_ifrs.json` |
| Factoring y leasing | CMF, TXT trimestral de estados IFRS | 3, 13, 23 | `factoring_leasing/scripts/backfill_ifrs.py` + `publish_backfill.py` (`factoring_leasing_backfill.yml`) | `docs/outputs/factoring_leasing/` |
| Corredores de bolsa y agentes de valores | CMF, Excel FECU IFRS trimestral de intermediarios | 6, 16, 26 | `corredoras_bolsa/scripts/actualizar_eeff.py` (`corredoras_eeff.yml`) | `docs/outputs/corredoras_bolsa/` |
| Seguros (vida y generales) | CMF, Circular 1835 (cartera de inversiones, archivo mensual) | 7, 17, 27 | `seguros/scripts/actualizar_carteras.py` (`seguros_carteras.yml`) | `docs/outputs/seguros/` |
| Fondos mutuos | CMF, Circular 1333 (cartera mensual) | 8, 18, 28 | `ffmm/scripts/actualizar_carteras.py` (`ffmm_carteras.yml`) | `docs/outputs/ffmm/` |
| Fondos de inversión | CMF, informes IFRS trimestrales de cartera y pactos de cada fondo | 9, 19, 29 | `fi/scripts/actualizar_carteras.py` (`fi_carteras.yml`) | `docs/outputs/fi/` |
| Listas de entidades: AGF, securitizadoras, corredores, fintech, bancos, cooperativas, sistemas de pago | Registros públicos CMF (consulta.php: RGAGF, RGSEC, COBOL, RGPSF, BANCO, BCCOO, TPOPE, RGCCO, BCSAG, DCVAL) | 10, 20, 28 | `pipelines/entidades/actualizar_listas.py` (`entidades.yml`) | listas `*_maestro` + `docs/outputs/entidades/novedades.json` |
| Lista de patrimonios separados | CMF, inscripciones de títulos de deuda por registro automático (`listado_titulos_deuda.php`) | 10, 20, 28 | ídem | `patrimonios_separados_maestro` |
| Lista de AFP | Superintendencia de Pensiones, valor cuota diario por AFP (RUT desde el Registro de Valores CMF) | 10, 20, 28 | ídem | `afp_maestro_administradoras` |
| Macro | Banco Central (API SIETE) | diario | `macro/scripts/daily_macro.py` + `macro/scripts/series_bcch.py` (`macro.yml`) | `docs/outputs/macro/` (3 tablas mensuales + `series/` y catálogo de 51 series) |

Entidades nuevas: todas las listas se completan solas. `entidades.yml` agrega y actualiza la
vigencia desde los registros públicos; FI regenera su registro completo en cada corrida; FFMM y
seguros construyen su lista con los fondos / compañías que reportan; el actualizador IFRS agrega
las CCAF y sociedades de factoring/leasing que reportan y avisa (`::notice::`) de las AGF y
securitizadoras que reportan sin estar en la lista. Nunca se da de baja por simple ausencia.

Única tabla manual: el balance de patrimonios separados (planilla entregada, 2014-12 a 2025-12;
la CMF solo publica esos estados como PDF).

## Guardián: que ninguna tabla vuelva a quedar como foto fija

`pipelines/auto/inventario.json` declara, para cada tabla de `data_manifest.json`, el workflow que
la actualiza (o el motivo por el que es manual). `scripts/audit_automatizacion.py` lo revisa:

* **en cada push** (`web_audit.yml`, job `automatizacion`): una tabla sin inventario, un workflow
  sin horario o que no ejecuta su script, un script que no nombra el archivo de la tabla, o una
  etiqueta «modo» que no calza, hacen fallar la auditoría;
* **cada lunes** (job `frescura`, rama por defecto): cada workflow debe tener una corrida exitosa
  dentro de su plazo (`max_dias`: 16 para los de 3 veces al mes, 3 para macro). Si no, se abre un
  issue «Automatización: hay tablas que no se están actualizando» (o se comenta el abierto).

Al agregar una tabla: sumarla al inventario con su workflow, o con `{"manual": "motivo"}`.

```bash
python scripts/audit_automatizacion.py                 # revisión estática
GH_TOKEN=... python scripts/audit_automatizacion.py --frescura --repo dueño/repo --rama main
```

Auditoría de la web completa:
```bash
python scripts/audit_navigation.py && python scripts/audit_web_full.py
```

**Sin sondas ni laboratorios (2026-09-28):** en `.github/workflows/` sólo quedan workflows que publican
(o `pages` / `web_audit`). Las sondas bancarias, el laboratorio REPO, el laboratorio XML/XBRL, la sonda
retail y los cotejos de muestra se eliminaron; si hace falta investigar algo, hacerlo en una rama y no
dejar workflows sin publicación en la rama principal.
