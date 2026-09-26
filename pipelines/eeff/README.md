# EEFF desde el PDF de Información Financiera

El buscador de periodos ya estaba codificado y no se usaba.

En `factoring_leasing/scripts/02_extract_factoring_leasing_notas_series.py`,
`fetch_cmf_pdf_stream` hace exactamente lo que se hace a mano en la CMF:

1. Abrir la ficha, pestaña Información Financiera (`pestania=3`).
2. Enviar el formulario de periodo: `mm`, `aa`, `tipo` (C o I), `tipo_norma=IFRS`.
3. Seguir el enlace cuyo texto es `Estados financieros (PDF)`
   (`safec_ifrs_verarchivo.php`).
4. Si no hay consolidado, repetir en individual.

`extract_all()` de ese script no llama a esa función. Reparte el total de
efectivo y de cartera con porcentajes fijos. Eso no es una nota. Esas tablas
siguen en el monitor bajo De Interés, marcadas para no usarlas como EEFF.

## Cómo corre, y cómo sigue si se corta

No parte de cero. El estado vive en `factoring_leasing/eeff_estado/`:

- `checkpoint.json`: un documento por RUT, periodo y tipo. Si el hash del
  Markdown no cambió y la versión del parser es la misma, no se relee.
- `tablas/<tabla>/<periodo>.jsonl`: las filas. Actualizar un documento
  reescribe solo su periodo, no el historial de otro corte.
- La escritura es atómica. El checkpoint se guarda después de cada sociedad,
  no al final. Si una falla, se anota y se sigue. Las filas buenas anteriores
  de ese documento no se borran.
- Un lock evita que dos corridas pisen los JSONL. Si el proceso murió, el
  lock de un pid muerto no bloquea la reanudación.

`PARSER_VERSION` está en `pipelines/eeff/alias.py`. Sube cuando cambia el
diccionario o el lector. Eso obliga a releer una vez. Después vuelve a saltar.

La API no escribe cifras en el estado. `nota_lineas` quedó vacía: ninguna
nota vive en una bolsa.

## La llave

El número de nota no identifica. El diccionario está en
`pipelines/eeff/alias.py`. «Préstamos que devengan intereses» es otros
pasivos financieros. «Movimientos de patrimonio» y «capital y reservas» son
patrimonio. «Activos a valor razonable con cambios en patrimonio» no es la
nota de patrimonio. «Política de provisiones de deudores» no es la nota de
deudores.

Ocho tablas comunes. Solo dos tienen columnas leídas, las de Security
marzo 2026:

- `nota_efectivo`: concepto, saldo del corte, saldo comparativo. El total
  11.283.111 cuadra con la carátula.
- `nota_deudores`: producto, colocación, provisión, neto. El que cuadra es
  el neto, 648.223.161.

Pasivos financieros, cuentas por pagar, relacionadas, impuestos, patrimonio
y propiedades, planta y equipo están en el índice. `notas_cobertura` las
marca `en_indice_sin_tabla`. No se inventan columnas. Si un Markdown futuro
trae la tabla antes de cerrar el esquema, queda en
`nota_esquema_pendiente` con los encabezados vistos, sin montos inventados.

Un índice cortado no niega una nota. Eurocapital, en el archivo de marzo,
solo tiene las notas 5 a 8: esas seis quedan `indice_incompleto`, no
ausentes.

Ingresos se guarda en la carátula. La nota no entra como tabla común: el
título no es el mismo entre sociedades.

## Qué hay de marzo 2026

Diez PDF, transcritos en `factoring_leasing/eeff_fuentes/`. No se reemplazan
con el HTML.

Carátula que cuadra (activos = pasivos + patrimonio): Forum, Santander
Consumer, Autofin, Primus, ST Capital, GM Financial, Security y Penta.

Parciales, a propósito:

- Tanner: la carátula leída no trae efectivo ni deudores. El índice sí.
- Eurocapital: efectivo, deudores corrientes, total de activos y patrimonio.
  Sin pasivos en el recorte.

Penta no trae el gasto de administración: el corte de página partió la cifra
y no se completa a mano.

## Validación

La serie `factoring_leasing_balance_resumen` no trae tipo consolidado o
individual. Un cuadre numérico queda `SIN_TIPO`, no `OK`: no se finge que
el tipo coincidió. `numeros=cuadra` dice que las cifras calzan, con
tolerancia de 1 millón. En este corte no hay `DIFIERE`. `SOLO_API` es una
línea que el PDF no publicó (Autofin no separa el pasivo corriente; Tanner
y Eurocapital están incompletos; ST Capital no trae pasivo no corriente).
La API no rellena.

## Cómo correrlo

```bash
python factoring_leasing/scripts/03_eeff_desde_pdf.py
python factoring_leasing/scripts/03_eeff_desde_pdf.py --periodo 2026-03
python factoring_leasing/scripts/03_eeff_desde_pdf.py --rut 96655860-1
python pipelines/eeff/test_alias.py
python pipelines/eeff/test_parse_md.py
python pipelines/eeff/test_correr.py
```

La segunda corrida, si nadie tocó los Markdown, imprime `skip` en los diez.

`--forzar` relee aunque el hash coincida. `--olvidar-ausentes` saca del
estado un documento cuyo Markdown ya no está. Sin esa bandera, borrar un
archivo no borra sus filas.

`--descargar` solo baja el PDF si el Markdown no existe. No reintenta el
TLS desde una red que no llega a CMF, y no borra una fuente ya guardada
cuando la descarga falla. Desde esta red no se vuelve a correr.

El JSON se publica siempre. El parquet, solo si está instalado `pyarrow`.
Sin eso el script avisa y no deja el JSON a medias; el parquet viejo no se
toca. Para que el monitor no lea un parquet atrasado:

```bash
pip install pyarrow
```

El monitor separa Factoring en EEFF y De Interés. EEFF es el PDF.
De Interés es el maestro, la serie API y las tablas de porcentajes.
