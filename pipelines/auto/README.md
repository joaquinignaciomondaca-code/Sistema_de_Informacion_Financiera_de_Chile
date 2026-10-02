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
| Fondos mutuos · balance y resultados anuales | CMF, XML IFRS de cada fondo (Circular 1997), uno por fondo y año | 4, 14, 24 |
| Fondos mutuos · valor cuota | Derivado de la cartera de aseguradoras (CMF, Circular 1835 B.3); no descarga | 9, 19, 29 | `ffmm/scripts/actualizar_valor_cuota.py` (`valor_cuota.yml`) → `docs/outputs/valor_cuota/ffmm`, `docs/outputs/valor_cuota_control.json` | `ffmm/scripts/actualizar_eeff.py` + `eeff_xml.py` (`ffmm_eeff.yml`) | `docs/outputs/ffmm/ffmm_balance`, `ffmm_resultados`, `ffmm_eeff_control.json` |
| Fondos de inversión | CMF, informes IFRS trimestrales de cartera y pactos de cada fondo | 9, 19, 29 | `fi/scripts/actualizar_carteras.py` (`fi_carteras.yml`) | `docs/outputs/fi/` |
| Listas de entidades: AGF, securitizadoras, corredores, fintech, bancos, cooperativas, sistemas de pago | Registros públicos CMF (consulta.php: RGAGF, RGSEC, COBOL, RGPSF, BANCO, BCCOO, TPOPE, RGCCO, BCSAG, DCVAL) | 10, 20, 28 | `pipelines/entidades/actualizar_listas.py` (`entidades.yml`) | listas `*_maestro` + `docs/outputs/entidades/novedades.json` |
| Lista de patrimonios separados | CMF, inscripciones de títulos de deuda por registro automático (`listado_titulos_deuda.php`) | 10, 20, 28 | ídem | `patrimonios_separados_maestro` |
| Lista de AFP | Superintendencia de Pensiones, valor cuota diario por AFP (RUT desde el Registro de Valores CMF) | 10, 20, 28 | ídem | `afp_maestro_administradoras` |
| Macro | Banco Central (API SIETE) | diario | `macro/scripts/series_bcch.py` → `build_tablas_tematicas.py` → `audit_macro_bcch.py` (`macro.yml`) | `docs/outputs/macro/` (23 tablas temáticas + catálogo de 51 series; `series/` es materia prima interna) |

Entidades nuevas: todas las listas se completan solas. `entidades.yml` agrega y actualiza la
vigencia desde los registros públicos; FI regenera su registro completo en cada corrida; FFMM y
seguros construyen su lista con los fondos / compañías que reportan; el actualizador IFRS agrega
las CCAF y sociedades de factoring/leasing que reportan y avisa (`::notice::`) de las AGF y
securitizadoras que reportan sin estar en la lista. Nunca se da de baja por simple ausencia.

Única tabla fuera de Actions: el balance de patrimonios separados (la CMF solo publica esos
estados como PDF). Es un flujo híbrido: la extracción y curación inicial se consolidan localmente
en una planilla, mientras `securitizadoras/scripts/05_publicar_balance_patrimonios.py` ejecuta
validaciones reproducibles y compila el Parquet (2014-12 a 2025-12).

## Contrato de un publicador (cómo escribe en la rama sin pisar a los demás)

Una docena de workflows escriben en la misma rama y varios arrancan a la vez (un merge a `main` dispara
todos los que miran esos archivos). Para que ninguno quede sin publicar por culpa de otro:

1. **El commit de datos lleva solo lo que ese workflow escribe** (sus Parquet, su `manifest.json`). Nunca
   `data_manifest.json`, `docs/js/*.js`, `docs/index.html` ni el catálogo de descargas: los edita todo el
   mundo. Un publicador que los metía en su commit (factoring/leasing y banca hasta el 2026-10-01) chocaba en
   cuanto otro reescribía esa lista entre medio, y reintentar no servía (el conflicto persiste mientras esa edición
   esté en la rama): «8 intentos por contención» y nada publicado.
2. **Lo compartido se regenera sobre la cabeza vigente**, no se integra: en cada intento (≤ 8) `fetch` →
   `reset --hard FETCH_HEAD` → `cherry-pick` del commit de datos → comando `--solo-…` del propio
   publicador (`--solo-data-manifest`, `--solo-conteos`, `--solo-catalogos`) → `build_download_catalog.py` →
   commit → `push`. Un push rechazado se reintenta igual, con espera aleatoria.
3. **Pruebas antes de publicar.** Un publicador con lógica propia de extracción o de compuertas corre sus pruebas
   unitarias (sin red, con fuentes sintéticas) antes de tocar la fuente: lo que decide qué se publica no llega a la web
   sin haberlas pasado. Hoy las tienen cableadas IFRS, corredores, banca, factoring-leasing, los estados financieros de
   fondos mutuos y normativa; seguros, las carteras de FFMM, FI, entidades y macro no tienen pruebas en su workflow. `web_audit.yml` corre
   además todas las de los extractores de estados financieros en cada push y PR (job `pruebas`).
   Las pruebas no pueden depender del día en que corren: los relojes se inyectan (`_hoy()`/`_ahora()`).
4. **Los disparadores `push` incluyen los módulos compartidos que el script importa**
   (`pipelines/auto/ifrs_txt.py`, `cuadratura.py`, `estable.py`, `rut.py`).

`pipelines/auto/tests/test_contrato_publicadores.py` (job `pruebas` de `web_audit.yml`) hace cumplir los puntos 1 y 2: todo `git add`
que nombre un archivo compartido tiene que ir precedido, en el mismo paso, de `reset --hard FETCH_HEAD` y de un regenerador.

Cierres que la CMF reedita: el TXT IFRS muestra «(actualizado: …)» junto a cada archivo
(`ifrs_txt.actualizaciones_indice`). `ifrs_sectores/actualizar.py` y `factoring_leasing/scripts/backfill_ifrs.py`
vuelven a leer un trimestre ya cerrado si esa fecha es posterior a su última lectura; el informe de
corredores no trae fecha, así que ahí un cierre no se relee.

Fondos mutuos, estados financieros (`ffmm/scripts/actualizar_eeff.py`): no hay descarga masiva, solo una ficha y un XML por
fondo y año, así que el flujo es distinto al del TXT IFRS. Procesa todos los fondos (vigentes y extintos) y todos los cierres de
diciembre desde 2010, y cada fondo y cierre queda en uno de cuatro estados: `ok`, `sin_informacion`, `ilegible` o `pendiente`.
Reglas que lo distinguen de los demás publicadores:

* **Un error transitorio nunca es «sin información».** La CMF sirve a veces una página de desafío JavaScript en lugar de la ficha,
  o un XML a medias: eso se reintenta y deja el cierre `pendiente`. Mientras haya un cierre cerrado pendiente, no se publica
  nada (serie incompleta). Tras 3 corridas sin poder leer un XML, se excluye como `ilegible` y queda listado en el control.
* **Reedición por nombre de archivo.** El nombre del XML lleva la fecha y hora de envío: si cambió, hubo un reenvío autorizado y se
  baja de nuevo (`reediciones` en `ffmm_eeff_control.json`). Cada corrida revisa las fichas de los dos últimos cierres y de 1/36
  del resto, de modo que toda la historia se revisa una vez al año sin pedir las ~8.000 fichas cada vez.
* **El estado se reconstruye de lo publicado.** El progreso (`.local-data/ffmm_eeff`) viaja en la caché de Actions, pero si se pierde
  se rehace desde los Parquet y el control: no hay que volver a bajar la historia.
* **Compuertas:** cuadratura activo − pasivo = activo neto (el activo neto atribuible a los partícipes no se suma al pasivo) con la
  política común de `pipelines/auto/cuadratura.py`, nueve identidades contables por fondo y cierre como avisos, y detención si
  más del 2 % de los XML son ilegibles (cambió el formato).

## Guardián: que ninguna tabla vuelva a quedar como foto fija

`pipelines/auto/inventario.json` declara, para cada tabla de `data_manifest.json`, el workflow que
la actualiza o, cuando todavía no hay workflow programado, si el flujo es híbrido/manual y su
motivo. `scripts/audit_automatizacion.py` lo revisa:

* **en cada push** (`web_audit.yml`, job `automatizacion`): una tabla sin inventario, un workflow
  sin horario o que no ejecuta su script, un script que no nombra el archivo de la tabla, o una
  etiqueta «modo» que no calza, hacen fallar la auditoría;
* **cada lunes** (job `frescura`, rama por defecto): cada workflow debe tener una corrida exitosa
  dentro de su plazo (`max_dias`: 16 para los de 3 veces al mes, 3 para macro). Si no, se abre un
  issue «Automatización: hay tablas que no se están actualizando» (o se comenta el abierto).

Al agregar una tabla: sumarla al inventario con su workflow, o con `{"hibrido": "motivo", "scripts": ["ruta/al/compilador.py"]}` si el procesamiento posterior es reproducible, o con `{"manual": "motivo"}` si todavía no existe ese compilador.

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
