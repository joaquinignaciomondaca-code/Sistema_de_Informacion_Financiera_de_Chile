# Revisión parcial de identidades del maestro bancario

**Fecha:** 2026-09-27

**Alcance:** revisión rápida de consistencia y cotejo oficial de cuatro RUT; no equivale a validar el maestro completo.

## Resultado

- 40 filas y 40 códigos institucionales distintos.
- Los 40 RUT pasan el dígito verificador; esto solo comprueba formato, no identidad.
- Se detectaron cuatro RUT incorrectos al contrastar código/nombre con antecedentes CMF y se corrigieron tanto en `bancos/scripts/pipeline_stream_bancos.py` como en `docs/outputs/bancos/bancos_maestro.json`:

| Código | Identidad | RUT corregido |
| --- | --- | --- |
| 009 | Banco Internacional | 97.011.000-3 |
| 012 | Banco del Estado de Chile | 97.030.000-7 |
| 504 | Banco Bilbao Vizcaya Argentaria, Chile (BBVA) | 97.032.000-8 |
| 507 | Banco del Desarrollo | 97.051.000-1 |

Fuentes oficiales consultadas:

- CMF, Banco Internacional: <https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97011000&grupo=0&tipoentidad=BANCO&vig=VI&control=svs&pestania=38>
- CMF, Banco del Estado de Chile: <https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97030000&grupo=0&tipoentidad=BANCO&row=AAAwy2ACTAAABzgAAl&vig=VI&control=svs&pestania=110>
- CMF, BBVA Chile: <https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97032000&grupo=0&tipoentidad=BANCO&vig=VI&control=svs&pestania=38>
- CMF, antecedentes que identifican el RUT 97.051.000-1 con Banco del Desarrollo: <https://www.cmfchile.cl/portal/principal/623/articles-103770_recurso_1.pdf>

## Pendiente al 2026-09-27 (resuelto el 2026-10-23)

Esta revisión no cotejó los RUT, razón social, tipo, estado ni vigencia de las otras 36 filas de forma individual, ni revisó exhaustivamente los datos históricos y agregados. Por eso el maestro quedó marcado **pendiente de validación** hasta completar el cotejo de los 40 registros contra las nóminas y cronologías oficiales CMF.

## Cotejo completo — 2026-10-23

Se cotejaron las **41 filas** del maestro contra el registro BANCO de la CMF
(`consulta.php?mercado=B&entidad=BANCO`), en sus dos listas: vigentes y no
vigentes. La copia fechada del registro queda en
`docs/outputs/bancos/registro_cmf_banco.json` (36 entidades) y el resultado fila
a fila en `docs/outputs/bancos/identidades_cmf.json`.

| Resultado | Filas | Qué son |
|---|---|---|
| `cotejado` | 30 | El RUT aparece en el registro con la misma razón social. |
| `agregado_sectorial` | 7 | 900, 950, 960, 970, 980, 998 y 999: totales del sistema, no bancos, sin RUT propio. |
| `declarado` | 4 | 027 y las filiales 816, 916 y 927: excepciones documentadas en el script. |
| `no_en_registro` | **0** | — |

**Los nueve RUT que la CMF no reconocía** siguen un patrón que no es de la CMF
(`59048000-2`, `59060000-8`, `59070000-2`, `59015000-2`…). Se reemplazaron por
los del registro oficial, sin tocar el nombre del maestro (que es el que
identifica la entidad en los archivos históricos):

| Código | Antes | Ahora | Nombre en el registro CMF |
|---|---|---|---|
| 017 | 59015000-2 | **97003000-K** | BANCO DO BRASIL S.A. |
| 043 | 59048000-2 | **59002030-3** | BANCO DE LA NACION ARGENTINA |
| 045 | 59060000-8 | **59002220-9** | THE BANK OF TOKYO-MITSUBISHI UFJ, LTD |
| 046 | 97054000-8 | **97919000-K** | BANCO SUDAMERICANO (ANTES THE ROYAL BANK OF SCOTLAND (CHILE)) |
| 052 | 97058000-K | **96929050-2** | DEUTSCHE BANK CHILE |
| 054 | 97060000-0 | **97949000-3** | RABOBANK CHILE (EX HNS BANCO) |
| 056 | 97066000-3 | **97952000-K** | BANCO PENTA |
| 057 | 97068000-4 | **99565970-0** | BANCO PARIS |
| 058 | 59070000-2 | **59141000-8** | DNB NOR BANK ASA |

Además se unificó el formato: `rut_dv` va sin puntos y equivale a `rut` más el
dígito verificador en las 41 filas (9 quedaron con puntos al aplicar la
corrección y se normalizaron). El parámetro `rut` de las particiones no cambió:
`bancos/scripts/completar_entidades.py` no tuvo nada que reescribir.

**Reproducibilidad.** `bancos/scripts/validar_identidades.py --check` y
`bancos/scripts/corregir_identidades.py --check` corren sin red sobre los
archivos publicados y son compuerta de CI. El maestro **deja de estar pendiente
de validación**; la advertencia que se mantiene es la de los agregados `9xx`,
que no son bancos y no se suman con ellos.
