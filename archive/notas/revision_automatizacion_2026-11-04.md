# Revisión de la automatización y de las compuertas (2026-11-04)

Revisión de los fallos que la auditoría de la web y el guardián de automatización estaban
reportando en `main`. Cada punto describe el síntoma observado en GitHub Actions, la causa
y lo que se cambió. Todo se verificó en local con los datos publicados de `main`.

## 1. `main` en rojo sin que nadie tocara el código: contrato derivado mezclado

**Síntoma.** 11 corridas de «Auditoría de la web…» en rojo entre el 1 y el 2 de noviembre,
y de nuevo el 4 de noviembre, siempre en el primer paso:

```
Contrato: manifiesto ETL, API y descargas comparten métricas  → exit 1
MÉTRICAS DESACTUALIZADAS: ejecuta scripts/build_metricas_publicadas.py
```

**Causa.** El catálogo API quedó con 19.814.981 filas y el catálogo de descargas con
19.814.992; `macro_uf` tenía 4.689 filas en `catalog.json` y 4.690 en descargas y en su
Parquet. La serie diaria macro (11 filas nuevas) entró al repositorio mientras la cadena de
`contrato_publicado.yml` ya estaba corriendo: `build_macro_web.py` leyó el estado nuevo y
`build_api.py`/`build_contrato.py` el anterior. El flujo publicó esa mezcla y la compuerta la
descubrió en el push siguiente. Además el README declara esas mismas cifras y el flujo que
las actualiza no lo versionaba, así que cada publicación de datos lo dejaba atrás.

**Cambios.**

- `scripts/refrescar_contrato.py`: la cadena completa vive en un solo sitio
  (`scripts.build_macro_web.CADENA`) y se rehace entera si `HEAD` se mueve durante la corrida.
  Termina con la pasada de `--check` de cada generador, de modo que no se publica un artefacto
  que no coincide con los datos publicados.
- `scripts/build_metricas_publicadas.py`: `sincronizar_readme()` reescribe la tabla sectorial,
  el total y los tres resúmenes narrativos del README desde el catálogo y las descargas.
  Solo sustituye cifras; no toca la prosa.
- `contrato_publicado.yml`: invoca el refresco unificado y versiona `README.md`.

## 2. Fondos de inversión: el cierre llevaba 33 días congelado

**Síntoma.** `fi_eeff.yml` llevaba 10 corridas seguidas en rojo desde el 2026-10-02 y la
serie FI seguía en 2026-06. El guardián de frescura solo lo detectó el 2026-11-02, 33 días
después, porque `fi_eeff.yml` no estaba en su lista.

**Causa.** Eran dos fallos encadenados.

1. La compuerta `MAX_RECHAZADOS = 2 %` mezclaba dos cosas muy distintas: un documento
   defectuoso (en 2025-03, 3 de 859 venían con el balance como bloque XBRL y no como
   cuenta/cifra) y una negativa de acceso de la CMF. Con el umbral contando ambas, cualquier
   negativa empujaba el cierre por encima del 2 % y lo bloqueaba.
2. El bloqueo era definitivo. La anotación del run 41343943402 lo muestra sin ambigüedad:
   `2023-06: 175 de 782 documentos con XML rechazados`, todos con el mismo motivo,
   `CMF rechaza explícitamente la descarga: ACCION NO PERMITIDA 16`. Es el mismo censo que el
   `fi/README.md` declaró no rescatable el 2026-10-01: no se recupera reintentando. Como la
   regla era «un solo documento negado bloquea el cierre», ese cierre **no se podía completar
   nunca**: cada corrida de 3 días bajaba los 782 documentos, volvía a fallar y frenaba los
   cierres nuevos que venían detrás. Diez de las últimas diez corridas en rojo, 33 días sin
   éxito.

**Cambios** (`fi/scripts/actualizar_eeff.py`, `fi/README.md`).

- El umbral del 2 % mira solo los documentos defectuosos; las negativas de acceso ya no lo
  alimentan. Un documento que no pasa las identidades contables o el cotejo se excluye con su
  motivo, como ya hacía `pipelines/auto/cuadratura.py`, y sigue bloqueando por encima del 2 %,
  que es cuando la lectura falla en bloque y no en un caso aislado.
- Una negativa de acceso que **no estaba** en la corrida anterior bloquea el cierre: el
  conjunto todavía cambia y se reintenta, porque la CMF a veces la levanta.
- El **mismo conjunto** de negativas ya no es una carrera: son documentos que la CMF no
  entrega. El cierre se publica como **parcial**, con el piso en
  `fi_eeff_control.json → parciales` (RUN, validados y motivo) y un `::warning` en el run. El
  período deja de reintentarse salvo con `--refrescar-todo`, y una negativa nueva vuelve a
  bloquear hasta que su conjunto también se repita.
- El diagnóstico agrupa los rechazos por motivo y elige un ejemplo por motivo: antes
  `784 × «faltan cuentas»` desbordaba la anotación de Actions y el motivo real no se veía.
- `--max-periodos` ya no puede dejar fuera un cierre publicado que quedó en reintento.

Verificado sobre el perfil real de `2023-06` (607 validados, 175 negados): la primera corrida
bloquea, la segunda publica el cierre parcial con los 175 RUN declarados, y una negativa
adicional lo vuelve a bloquear.

## 3. IFRS de AGF, securitizadoras y CCAF: 6 corridas en rojo por un archivo a medio cargar

**Síntoma.**

```
202609: el archivo trae solo 14 sociedades      → ::warning
… y la corrida terminaba con exit 1
```

**Causa.** La guarda de 50 sociedades se aplicaba igual a un trimestre histórico incompleto
(201003, 4 sociedades, que ya se toleraba) y a un trimestre abierto que la CMF todavía está
cargando. Ese archivo tampoco debía registrarse: habría dejado el trimestre «cerrado» con una
foto parcial.

**Cambios** (`pipelines/ifrs_sectores/actualizar.py`).

- `MIN_SOCIEDADES_RECIENTE = 100`: un trimestre que aún no cierra con menos sociedades lanza
  `ErrorIncompleto`, no se registra y se reintenta; no pinta la corrida de rojo.
- Los históricos incompletos siguen igual: aviso, sin publicar y sin fallar.

## 4. El guardián de automatización no veía lo que fallaba

**Síntoma.** Con `fi_eeff.yml` 33 días en rojo, `ifrs_sectores.yml` 6 de 10 corridas fallidas
y `contrato_publicado.yml` 4 de 6, el guardián semanal solo reportaba «1 problema» (una falta
de `pyarrow` en el issue del 2026-10-05).

**Cambios** (`scripts/audit_automatizacion.py`, con pruebas en `scripts/test_audit_automatizacion.py`).

- `FLUJOS_DE_ESCRITURA`: los publicadores que escriben en la rama sin producir tablas del
  manifiesto (`fi_eeff.yml`, `contrato_publicado.yml`) entran a la revisión de frescura.
- `inestabilidad()`: un flujo que falla más de la mitad de sus últimas corridas terminadas
  falla el guardián aunque su última corrida exitosa esté dentro del plazo. Las corridas
  canceladas no cuentan como fallas.
- `web_audit.yml` cierra solo el issue de frescura cuando ya no hay flujos atrasados; antes
  quedaba abierto para siempre y tapaba los fallos reales.

## 5. `servidor`: el fallo del PR del 2026-11-03

El job `servidor` del run 41576443042 salió con **exit code 4**, que es cómo pytest señala un
error de uso, no un test fallido: la colección no llegó a empezar porque falló un import de
`servidor/tests/conftest.py`. El mismo commit pasó el job 12 minutos después
(run 41578328169, 101 pruebas), sin que cambiara una línea de Python, así que fue una
resolución de dependencias transitoria al instalar `servidor/requirements-dev.txt`
(`fastapi`, `duckdb`, `httpx2`), no un defecto del código. Reproducido en local sobre este
commit: las 101 pruebas pasan.

Para que un fallo así se explique solo, `web_audit.yml` ahora publica la cola de pytest como
anotación cuando el paso falla.

## 6. `main` quedó roto y el bot no podía arreglarlo

La revisión siguió a los runs del PR, y en `main` aparecieron dos fallos del propio
`contrato_publicado.yml` (41704975978 del 2026-11-03 19:37 y 41748802368 del 2026-11-04 00:42)
con la misma causa: la cadena vieja mezcló dos estados (macro publicó 11 filas diarias a las
17:39) y dejó el catálogo API con 19.814.981 filas frente a 19.814.992 en descargas y en el
manifiesto ETL. Con ese desfase, `build_metricas_publicadas.py --check` de `web_audit` sale
en rojo, y el flujo de contrato no podía regenerarlo porque corre la misma cadena que produce
la mezcla: se quedó reintentando hasta agotar los 8 intentos. En local, sobre `main` prístino,
`refrescar_contrato.py` converge en 266 s y deja todas las compuertas en 0; los artefactos de
ese refresco van en este mismo commit, así que `main` vuelve a quedar consistente al fusionar.

## 7. Dos fallos del propio arreglo, detectados en los checks del PR

El primer push de esta revisión dejó dos jobs en rojo, y ninguno venía de la rama:

- **`automatizacion`**: `test_refrescar_contrato.py` importaba `CADENA` desde
  `build_macro_web`, que importa pandas. El job solo instala pyarrow, así que fallaba con
  `ModuleNotFoundError` y lo que se veía era «Pruebas del propio guardián» en rojo con
  «0 problemas» en la línea anterior. La cadena se movió a `scripts/cadena_contrato.py`, sin
  dependencias; `build_macro_web` la reexporta para no romper llamadores. Reproducido con un
  venv que solo tiene pyarrow.
- **`audit`**: al agregar esta nota, `archive/notas/README.md` quedó atrás
  (`INDICE-NOTAS: no coincide con las notas`). Regenerado con `build_indice_notas.py`.

Los dos son el mismo tipo de error: una compuerta que solo se descubre cuando corre en el
entorno de CI. Por eso el arreglo se verificó con un venv que replica las dependencias del job
(68 pruebas OK), no con el entorno completo de desarrollo.

Con esos dos corregidos, los checks del PR 103 quedaron todos en verde: `audit`,
`automatizacion`, `pruebas`, `servidor`, `r_ejemplos`, `api_anything` y `actualizar-feed`.
`frescura` aparece en `skipping` porque solo corre programada o por `workflow_dispatch` sobre
la rama por defecto; su verificación en esta revisión se hizo a mano contra `main`.

## 8. `ifrs_sectores` siguió en rojo después del merge

La primera corrida programada en `main` (41789244162) volvió a fallar, y la causa no era la
que se había corregido: era otra puerta del mismo flujo.

**Síntoma.** `exit 1` en 50 s, con solo dos anotaciones y ambas de tipo «defecto»:
`202609: el archivo trae solo 22 sociedades` y `201003: ... archivo histórico incompleto`.
Ninguna debía pintar la corrida de rojo, y la prueba que lo comprobaba pasaba.

**Causa.** El `exit 1` no venía de esos dos. `202606` está **publicado y todavía abierto**
(cierra ~150 días después de junio), así que se relee en cada corrida. Cuando la CMF reenvía el
archivo con cifras que no pasan la cuadratura —o con menos sociedades—, la compuerta conserva
lo ya publicado, que es lo correcto, pero lo anotaba en `errores`. La indulgencia existente
(`defectos`) solo cubría los cierres que el **índice** anuncia como reeditados; para un
trimestre abierto la CMF sube cifras sin anunciarlo, así que caía del lado equivocado. Como en
esa corrida no había nada nuevo que publicar (`hechos == 0`), el resultado era `exit 1`. El
mismo caso explica las corridas en rojo desde el 2026-10-22, la última verde de la serie.

**Arreglo.** La condición deja de mirar solo el anuncio del índice y pasa a mirar los hechos:
un período que ya está publicado y sigue abierto se está **releyendo**, no descubriendo. Si su
relectura no pasa las compuertas, es un aviso sobre la fuente (defecto), no una falla de la
corrida. Lo que nunca se publicó sigue en rojo: esa prueba ya existía y sigue pasando.

**Verificación.** La prueba nueva reproduce el fallo real (`exit 1`) y pasa con el arreglo;
desactivando el arreglo vuelve a fallar, así que prueba lo que dice probar.

**Esperado en `fi_eeff`.** La corrida del merge falló, y es el comportamiento diseñado: la
primera vez que ve el conjunto de negativas lo bloquea para reintentar. Las anotaciones lo
muestran funcionando (`2023-06: 607 validados, 175 rechazados` y `2025-03: 856 validados, 3
rechazados`), y el piso queda guardado en la caché del flujo. La corrida siguiente —con el
mismo conjunto— publica el cierre parcial. `2025-03` arrastra además 1 envío pendiente
crónico («la ficha no enlaza FIEF»), que no bloquea la publicación pero tampoco se puede
completar: por eso su cierre parcial queda con ese fondo fuera del censo conocido.

## Verificación

| Comprobación | Resultado |
|---|---|
| `fi/tests` (incluye el cierre parcial) | 128 pruebas OK |
| `pipelines.ifrs_sectores` + `pipelines.auto` + `pipelines.entidades` + extractores | 311 pruebas OK |
| `factoring_leasing/tests` | 60 pruebas OK |
| `scripts.*` (guardián, métricas y refresco), con solo pyarrow | 19 pruebas OK |
| Job `automatizacion` completo, con solo pyarrow | 68 pruebas OK |
| `audit_automatizacion.py` (estático) | 91 tablas, 0 problemas |
| `audit_automatizacion.py --frescura` contra `main` | detecta los 3 flujos inestables |
| `auditar_eeff_ifrs.py` (datos reales de `main`) | cuadratura completa, 0 descuadres |
| `refrescar_contrato.py` sobre `main` | converge y deja todas las compuertas en 0 |
| `audit_cifras.js` | 14 respaldos al día |
| `build_metricas_publicadas.py --check` tras el refresco | MÉTRICAS OK (90 objetos, 19.814.992 filas) |
| `servidor/tests` | 101 pruebas OK |
