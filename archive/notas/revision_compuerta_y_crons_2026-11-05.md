# Compuerta de estabilidad y crons: revisión del 2026-11-05

Revisión posterior al merge del PR #105 (2026-11-05T15:25Z). Tres defectos que quedaron al
descubierto al mirar lo que la compuerta haría **el lunes 9**, no lo que decía hoy.

## 1. La compuerta de estabilidad iba a marcar en rojo dos flujos ya arreglados

**Síntoma.** `web_audit.yml` corre `audit_automatizacion.py --frescura` los lunes a las 14:00
UTC. La corrida del 2026-11-09 habría fallado con dos errores:

```
ifrs_sectores.yml: 9 de sus últimas 10 corridas fallaron (última el 2026-11-04)
fi_eeff.yml:       8 de sus últimas 10 corridas fallaron (última el 2026-11-04)
```

**Causa.** `inestabilidad()` miraba las últimas diez corridas terminadas **sin ventana de
tiempo**. Los dos flujos se arreglaron —`ifrs_sectores` el 5 de noviembre en
`pipelines/ifrs_sectores/actualizar.py` (2445684), `fi_eeff` el 4— y sus corridas posteriores
son verdes, pero los fallos viejos seguían en la muestra. Con un cron de cada tres días, el
historial tarda semanas en depurar solo: `ifrs_sectores` necesitaba unas ocho corridas exitosas
más (~24 días) y `fi_eeff` unas seis (~18). Hasta entonces la compuerta semanal habría
comentado el issue #24 con un diagnóstico sobre código que ya no existía.

**Cambios.**

- `ultimo_arreglo(nombre, rama)` fecha el último commit que tocó el flujo **o cualquiera de los
  scripts que el inventario le asocia**. Se usa `git log` (el mismo estilo que `llegada()`) y no
  el `updated_at` de la API de workflows: ese campo no se mueve con los pushes
  (`ifrs_sectores` seguía en 2026-10-02 después de dos arreglos).
- `inestabilidad()` recorta el historial anterior a ese corte. Si no queda ninguna corrida
  posterior, no reporta: todavía no hay con qué juzgar. Si el flujo vuelve a fallar después del
  arreglo, se reporta igual —el corte no compra un perdón, solo deja de juzgar el código viejo.
- Se conservan los tres umbrales que ya existían: no reportar con menos de cuatro corridas
  terminadas, no reportar cuando `fallidas * 2 <= terminadas`, y descartar `cancelled`/`skipped`.

**Un defecto del propio arreglo, encontrado al probarlo con el historial real.** La primera
versión contaba las corridas descartadas y las imprimía por flujo: trece líneas idénticas en la
salida semanal. La segunda versión descartaba los commits que tocaban más de ocho archivos, con
la idea de ignorar los commits de campaña. Estaba mal por dos motivos: los commits de
regeneración del bot tocan cientos de datos sin arreglar ningún flujo, y el arreglo del alias del
contrato (2026-11-04) tocó 192 archivos siendo un arreglo de verdad. Peor aún, el commit que fijó
`ubuntu-24.04` en 17 workflows contaba como «arreglo» de los 17 y reiniciaba el reloj de
estabilidad de toda la automatización a la vez: la compuerta quedaba ciega justo cuando hay que
mirarla. La medición correcta es **cuántos workflows toca el commit**, no cuántos archivos: por
encima de tres es una campaña sobre la flota y se sigue mirando hacia atrás. `macro.yml` conserva
así su corte del 26 de octubre en vez de saltar al 4 de noviembre.

**Verificación.** En un clon con historial completo (`--filter=blob:none`, 1.215 commits) y
contra la API real:

| Flujo | Corte | Terminadas | Posteriores | Veredicto |
|---|---|---|---|---|
| `ifrs_sectores.yml` | 2026-11-05 | 10 | 1 | silencio (no alcanza el mínimo de 4) |
| `fi_eeff.yml` | 2026-11-04 | 10 | 3 | silencio (no alcanza el mínimo de 4) |
| `contrato_publicado.yml` | 2026-11-04 | 9 | 5 | silencio (1 fallo de 5) |
| `macro.yml` | 2026-10-26 | 10 | 10 | silencio (0 fallos) |

`--frescura` completo: 13 flujos OK por fecha, `91 tablas inventariadas, 0 problemas`, exit 0.

**Nota sobre el clon superficial.** En el clon de trabajo del agente `git rev-list` devuelve un
solo commit, así que `ultimo_arreglo` fechaba todos los flujos con la fecha del clon y el corte
no medía nada. El job `frescura` de `web_audit.yml` tiene `fetch-depth: 0`, así que en Actions
el historial está completo. Pero la salida con el corte en el futuro no distingue un repo sano
de uno ciego: si el clon no tiene historial, conviene mirar el resumen final
(«N flujo(s) con historial anterior descartado») y desconfiar si dice 13 de 13 el mismo día.

## 2. `*/N` en cron es «cada N días del mes», no «cada N días»

Nueve flujos usaban `*/3` en el campo del día del mes. En cron eso significa los días 1, 4, 7,
…, 31 —no «cada 72 horas»— y además tiene un hueco: los meses de 30 días nunca llegan al 31 y
el salto final es de **dos** días (28→31 sí, 28→30 no, 30→1). Con `*/3` y un mes de 31 días el
patrón es 1,4,7,…,31, y al mes siguiente 1: el 31 salta en los meses de 30 y el intervalo real
oscila entre 2 y 4 días.

**Cambios.** Los nueve pasan a días fijos 1,4,7,…,28, conservando la hora de cada uno y
escalonando el día para no concentrar las nueve corridas el día 1:

| Flujo | Antes | Ahora |
|---|---|---|
| `bancos_cmf_mensual.yml` | `0 13 */3 * *` | `0 13 1 * *` |
| `corredoras_eeff.yml` | `45 13 */3 * *` | `45 13 1 * *` |
| `factoring_leasing_backfill.yml` | `20 12 */3 * *` | `20 12 4 * *` |
| `ffmm_carteras.yml` | `0 14 */3 * *` | `0 14 7 * *` |
| `ffmm_eeff.yml` | `20 14 */3 * *` | `20 14 10 * *` |
| `fi_carteras.yml` | `0 15 */3 * *` | `0 15 13 * *` |
| `fi_eeff.yml` | `35 15 */3 * *` | `35 15 16 * *` |
| `ifrs_sectores.yml` | `30 13 */3 * *` | `30 13 19 * *` |
| `seguros_carteras.yml` | `0 14 */3 * *` | `0 14 22 * *` |

Cada cron lleva ahora, encima, el aviso de por qué no se usa `*/3`. Los nombres de los flujos
que decían «cada 3 días» pasan a «días 1,4,7,…,28» para que el nombre del workflow en Actions no
mienta. El párrafo de la migración a `ubuntu-26.04` sigue diciendo «cada 3 días»: ahí la cifra
describe el retraso típico con que se nota un fallo, y con días fijos sigue siendo del orden de
tres.

**Riesgo asumido.** Si GitHub no ejecuta un día (cola saturada, incidente), la siguiente
oportunidad es la del día fijo siguiente, no «tres días después». Para datos trimestrales o
mensuales no cambia nada: la fuente publica una vez al mes y cualquiera de los intentos la
recoge. Para `contrato_publicado.yml` tampoco aplica: su `*/2` es de **horas**, donde sí
significa «cada 2 horas».

## 3. `ifrs_sondeo.yml` no se disparó el 2026-11-05

**Síntoma.** Cron `40 13 5 * *` (mensual, día 5). A las 16:09 UTC del 5 de noviembre no había
corrida agendada; el flujo está `active`, no hay nada encolado y la última corrida `schedule`
fue la del 2026-10-05, que salió verde.

**Estado.** No reproducido y sin acción de código. El sondeo es de solo lectura y además corre
por `push` cuando cambia él mismo o sus módulos: la última corrida (2026-11-04, `push`) es
exitosa. Los crons de GitHub se retrasan y, con la cola cargada, a veces se saltan una
ejecución; lo mismo pasó con `ifrs_sondeo` en octubre (la corrida del día 5 llegó a las 21:13
UTC). Se dejó anotado aquí para no confundirlo con un fallo del flujo si vuelve a ocurrir. Si se
repite dos meses seguidos, la salida es un `workflow_dispatch` manual o añadir un día de
respaldo (`5,15`), no cambiar el horario.

## Verificación

| Comprobación | Resultado |
|---|---|
| `python -m unittest scripts.test_audit_automatizacion` | 14 pruebas OK (5 nuevas) |
| Las 2 pruebas del corte, con el corte desactivado | fallan; con el corte, pasan |
| `audit_automatizacion.py` (estático) | 91 tablas, 0 problemas |
| `audit_automatizacion.py --frescura` contra `main`, historial completo | 13 flujos OK, 0 problemas, exit 0 |
| `yaml.safe_load` sobre los 20 workflows | 20 válidos |
| Crons de los 9 flujos normalizados | ninguno conserva `*/3` en el día |
