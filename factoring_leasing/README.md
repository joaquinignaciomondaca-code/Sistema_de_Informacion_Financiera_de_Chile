# Factoring y leasing

Industria sola. Dos secciones. Lo que no está en el PDF no se completa.

La entrega de esta vuelta es marzo 2026. El estado financiero sale del PDF de Información Financiera. La API solo valida totales. No escribe cifras en el EEFF.

## Cómo está ordenado

```text
factoring_leasing/
├── README.md                         este archivo
├── eeff_fuentes/                     Markdown transcrito del PDF. Es la fuente.
├── eeff_estado/                      checkpoint y JSONL. Si la corrida se corta, sigue.
└── scripts/
    ├── 03_eeff_desde_pdf.py          lee el Markdown y publica el EEFF
    ├── stream_cmf_eeff_series.py     serie API de totales. Validación, no fuente.
    ├── pipeline_stream_factoring_leasing.py
    ├── audit_factoring_leasing.py    audita maestro, serie API y tablas viejas
    └── 02_extract_factoring_leasing_notas_series.py
                                      no lee el PDF. No correrlo para publicar notas.

pipelines/eeff/                       lector, alias y cuadre. No es otra industria.
docs/outputs/factoring_leasing/       JSON y parquet publicados.
```

El número de nota no es la llave. El diccionario está en `pipelines/eeff/alias.py`. La revisión de títulos está en `pipelines/eeff/REVISION_NOTAS_2026_03.md`. La propuesta de esta vuelta está en `pipelines/eeff/PROPUESTA.md`.

## EEFF

Un documento por sociedad, periodo y tipo. Marzo 2026, diez PDF. Unidad de las líneas: miles de pesos.

| Tabla | Qué es | Filas |
|---|---|---|
| `factoring_leasing_eeff_documentos` | Qué se leyó, si cierra, y el hueco si no cierra | 10 |
| `factoring_leasing_balance_lineas` | Carátula del balance, una fila por cuenta | 223 |
| `factoring_leasing_resultados_lineas` | Estado de resultados, una fila por cuenta | 120 |
| `factoring_leasing_notas_indice` | Listado de títulos. Sin montos | 273 |
| `factoring_leasing_notas_cobertura` | Ocho familias comunes: leída, en el índice, o índice cortado | 80 |
| `factoring_leasing_nota_efectivo` | Nota de efectivo. Solo Security | 4 |
| `factoring_leasing_nota_deudores` | Nota de deudores. Solo Security. Cuadra el neto | 16 |
| `factoring_leasing_validacion_api` | Totales del PDF contra la serie API. No es fuente | 60 |
| `factoring_leasing_nota_esquema_pendiente` | Encabezados vistos sin esquema cerrado. Vacía | 0 |
| `factoring_leasing_nota_lineas` | Bolsa retirada. Vacía a propósito | 0 |

`nota_efectivo`: caja 4.240, fondos mutuos 0, bancos 11.278.871, total 11.283.111. Cuadra con la carátula. `nota_deudores`: neto 648.223.161. Colocación y provisión no se estiman.

Cinco carátulas cierran de punta a punta, balance y resultado: Autofin, Forum, GM Financial, Santander Consumer y ST Capital. Santander no trae una línea única de total pasivos. ST Capital no trae pasivo no corriente. La ecuación cierra igual.

| Sociedad | Balance | Resultados | Notas con montos |
|---|---|---|---|
| Autofin | Completo | Completo | Ninguna. Índice de 29 títulos |
| Forum | Completo | Completo | Ninguna. Índice de 31 títulos |
| GM Financial | Completo | Completo | Ninguna. Índice de 22 títulos |
| Santander Consumer | Completo | Completo | Ninguna. Índice de 39 títulos |
| ST Capital | Completo | Completo | Ninguna. Índice cortado, parte en la nota 5 |
| Security | Totales cierran. Faltan líneas de activo y de pasivo corriente | Completo | Efectivo y deudores. Las otras seis familias están en el índice |
| Penta | Completo | Incompleto entre ganancia bruta y antes de impuestos | Ninguna. Índice de 29 títulos |
| Primus | Completo | El corte cierra. El comparativo no, por 15.308 miles | Ninguna. Índice cortado, parte en la nota 6 |
| Eurocapital | Incompleto | Una línea | Ninguna. Índice cortado, notas 5 a 8 |
| Tanner | Incompleto | Incompleto | Ninguna. Índice de 36 títulos, sin montos |

El hueco, en miles, está en `eeff_documentos.hueco`. No se rellena.

Contra la API de marzo 2026 hay 51 chequeos que calzan y 9 líneas que el PDF no trajo (`SOLO_API`). La serie no dice si el estado es consolidado o individual, así que el calce numérico queda `SIN_TIPO`.

Flujo de efectivo y cambios en el patrimonio no se extrajeron. Están en el PDF. No están en estas tablas.

## De Interés

No es el estado financiero.

| Tabla | Qué es | Filas |
|---|---|---|
| `factoring_leasing_maestro` | 28 sociedades. 22 vigentes, 6 históricas | 28 |
| `factoring_leasing_balance_resumen` | Totales de la API, 2014-03 a 2026-03, 24 RUT | 878 |

Cuatro del maestro no aparecen en la serie: Bandesarrollo, BCI Factoring, BICE Factoring y Scotia Azul. Diez sociedades de marzo 2026 tienen fila API y no tienen PDF en esta entrega, entre ellas Factotal, Incofin y Progreso.

## Fuera de la entrega

Siguen en disco y no se cargan en el monitor:

- `factoring_leasing_nota_efectivo_detalle` (2.975)
- `factoring_leasing_cartera_morosidad_detalle` (17.406)

`02_extract_factoring_leasing_notas_series.py` las arma repartiendo totales de la API con porcentajes fijos. No son notas. No correr ese script para publicar un EEFF. `audit_factoring_leasing.py` las revisa porque existen; esa auditoría no cubre el PDF.

## Pendiente

1. **Extraer más notas.** Hoy solo hay montos en efectivo y deudores de Security. Eso no cierra el trabajo. Cada nota es una tabla con su propia estructura. La llave es el nombre, no el número: el mismo préstamo es la nota 13 en 2013 y otra nota 13 en 2026. No se inventan columnas. Si el Markdown trae la tabla antes de cerrar el esquema, queda en `nota_esquema_pendiente`, sin montos. No se copia la API ni el HTML.

   El orden, cuando haya PDF:

   - Primero Security, marzo 2026, las que ya están en el índice y no tienen tabla: pasivos financieros, cuentas por pagar, relacionadas, impuestos, patrimonio, y propiedades, planta y equipo. De ahí salen las columnas. Si una no tiene forma estable, no se masifica.
   - Después, las otras nueve de marzo 2026, la misma nota por nombre.
   - No parar en esas ocho. El índice trae más (ingresos y costos, intangibles, segmentos, contingencias, medio ambiente, y otras). Activo a valor razonable apareció en otros EEFF y no está en Security ni en GM Financial de este corte: no se declara ausente por no estar en un año. Se extrae la que el PDF trae, en su tabla, cuando el título es el mismo entre sociedades. Si el título no es el mismo, se guarda la línea de la carátula y la nota no entra como tabla común.
   - Ingresos no es tabla común todavía: Security los junta con costos, Autofin les mete la administración, Tanner los llama composición de resultados.

2. **Completar las carátulas y los resultados cortados**, desde el PDF, no a ojo. Security (líneas que faltan dentro de los subtotales), Penta (resultado), Primus (comparativo), Tanner y Eurocapital. Un índice cortado no niega la nota.

3. **Flujo de efectivo y cambios en el patrimonio.** La norma los pide y el PDF los trae. No entraron en esta vuelta. Cada uno, su tabla. No mezclarlos con el balance.

4. **Otros periodos y las sociedades sin PDF de marzo.** Security 2013 y 2018 entran con el mismo diccionario de nombres, no con los números de 2026. El resto, después de que las notas de marzo tengan forma.

   El OCR de Security individual diciembre 2013 (56 páginas, Actions `36230125769`) ya se leyó. Ocho páginas quedaron en timeout (5, 17, 18, 24, 27, 31, 40 y 51): ahí faltan los cuerpos de relacionadas (nota 6) y de pasivos financieros corrientes (nota 13). Lo que sí se leyó confirma el diccionario, no un juego nuevo de notas. Efectivo es caja más bancos y cierra en 6.705.444. Deudores es el puente bruto menos provisión y cierra en 198.940.321. Intangibles y propiedades cierran en el neto (83.222 y 299.888). Cuentas por pagar cierra en 6.048.480. No hay activo a valor razonable. Capital y ganancias acumuladas no tienen nota. El préstamo corriente es la nota 13 en 2013 y otra nota en 2026: se sigue por el nombre.

5. **La descarga.** El camino ya está: ficha CMF, pestaña Información Financiera, buscador de periodo, enlace `Estados financieros (PDF)`. Desde esta red el TLS a CMF se corta. No se simula el masivo. No se borra un Markdown si la descarga falla.

## Cómo correr

```bash
python factoring_leasing/scripts/03_eeff_desde_pdf.py
python factoring_leasing/scripts/03_eeff_desde_pdf.py --periodo 2026-03
python factoring_leasing/scripts/03_eeff_desde_pdf.py --rut 96655860-1
python pipelines/eeff/test_alias.py
python pipelines/eeff/test_parse_md.py
python pipelines/eeff/test_correr.py
```

No parte de cero. Si el Markdown no cambió y `PARSER_VERSION` es la misma, imprime `skip`. `--forzar` relee. `--olvidar-ausentes` saca del estado un documento cuyo Markdown ya no está. `--descargar` solo baja el PDF si el Markdown no existe.

El JSON se publica siempre. El parquet, solo si está instalado `pyarrow`. Sin eso el parquet viejo no se toca.
