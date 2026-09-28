# Publicaciones automáticas (GitHub Actions)

Inventario de todo lo que se actualiza solo. Regla común: cada workflow corre **3 veces al mes**
(salvo macro, que es diario), es **incremental** (lo ya publicado y cerrado no se vuelve a
descargar) y **fail-closed** (un período que no pasa la validación no se publica; se reintenta en
la corrida siguiente). Tras publicar en `main`, el mismo workflow despliega GitHub Pages.

| Sector | Fuente | Días (UTC) | Script | Salida |
| :--- | :--- | :--- | :--- | :--- |
| Bancos | CMF, archivos mensuales B1/B2/R1 | 1, 11, 21 | `bancos/scripts/publish_cmf_bank_period.py` (`bancos_cmf_mensual.yml`) | `docs/outputs/bancos/` |
| AGF, securitizadoras, CCAF | CMF, TXT trimestral de estados IFRS de todas las sociedades | 2, 12, 22 | `pipelines/ifrs_sectores/actualizar.py` (`ifrs_sectores.yml`) | `docs/outputs/{agf,securitizadoras,cajas_compensacion}/` |
| Factoring y leasing | CMF, TXT trimestral de estados IFRS | 3, 13, 23 | `factoring_leasing/scripts/backfill_ifrs.py` + `publish_backfill.py` (`factoring_leasing_backfill.yml`) | `docs/outputs/factoring_leasing/` |
| Corredores de bolsa y agentes de valores | CMF, Excel FECU IFRS trimestral de intermediarios | 6, 16, 26 | `corredoras_bolsa/scripts/actualizar_eeff.py` (`corredoras_eeff.yml`) | `docs/outputs/corredoras_bolsa/` |
| Seguros (vida y generales) | CMF, Circular 1835 (cartera de inversiones, archivo mensual) | 7, 17, 27 | `seguros/scripts/actualizar_carteras.py` (`seguros_carteras.yml`) | `docs/outputs/seguros/` |
| Fondos mutuos | CMF, Circular 1333 (cartera mensual) | 8, 18, 28 | `ffmm/scripts/actualizar_carteras.py` (`ffmm_carteras.yml`) | `docs/outputs/ffmm/` |
| Fondos de inversión | CMF, informes IFRS trimestrales de cartera y pactos de cada fondo | 9, 19, 29 | `fi/scripts/actualizar_carteras.py` (`fi_carteras.yml`) | `docs/outputs/fi/` |
| Listas de entidades (AGF, securitizadoras, corredores, fintech) | Registros públicos CMF (consulta.php) | 10, 20, 30 | `pipelines/entidades/actualizar_listas.py` (`entidades.yml`) | listas `*_maestro` + `docs/outputs/entidades/novedades.json` |
| Macro | Banco Central (API SIETE) | diario | `macro/scripts/daily_macro.py` (`macro.yml`) | `docs/outputs/macro/` |

Entidades nuevas: además de `entidades.yml`, FI regenera su registro completo en cada corrida;
FFMM y seguros construyen su lista con los fondos / compañías que reportan; los actualizadores
IFRS y de corredores avisan (`::notice::`) de quien reporta sin estar en la lista.

Sin actualización periódica (solo lista de entidades u otra razón): pensiones (lista de AFP),
cooperativas, fintech (solo lista, vía `entidades.yml`), sistemas de pago, patrimonios separados
(balance desde planilla manual, 2014–2025).

Auditoría de la web completa:
```bash
python scripts/audit_navigation.py && python scripts/audit_web_full.py
```
