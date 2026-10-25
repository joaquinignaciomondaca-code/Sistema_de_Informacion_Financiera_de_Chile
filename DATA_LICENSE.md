# Licencia de los datos

Este repositorio mezcla dos cosas que **no** comparten licencia: el código que
los produce y los datos que publica. La licencia MIT del repositorio cubre el
código, los scripts y la documentación; **no** cubre los datos de terceros que
se redistribuyen aquí.

## Código

MIT. Ver [`LICENSE`](LICENSE).

## Datos

Los datos proceden de organismos públicos chilenos. El proyecto descarga y
normaliza fuentes directas, y también mantiene algunos catálogos editoriales con
procedencia mixta. Las citas de fuente y las condiciones verificadas se derivan
de [`pipelines/api/fuentes.py`](pipelines/api/fuentes.py) y se publican en el
catálogo y el Data Package; eso no convierte la licencia MIT del código en una
licencia de los datos.

Para las **tres fuentes operativas directas** aquí documentadas (CMF, BCCh y
SPensiones), los documentos citados permiten la reutilización bajo las
condiciones indicadas en la tabla. Esto no resuelve automáticamente las
condiciones de fuentes históricas/editoriales que hayan contribuido a un
conjunto.

| Fuente | Objetos | Qué publica aquí | Documento vigente | Condición | Estado |
|---|---|---|---|---|---|
| **CMF** — Comisión para el Mercado Financiero | 65 objetos atribuidos | Bancos, seguros (Circular 1835), fondos mutuos y de inversión, AGF, corredoras, securitizadoras, CCAF, factoring y leasing, patrimonios separados, cooperativas, fintech y sistemas de pago. En `ccaf_maestro`, la entrada directa actual de CMF solo detecta altas; la procedencia del universo inicial también incluye SUSESO (ver abajo). | [Descargo de Responsabilidades](https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html): «autoriza la reproducción total o parcial de la información contenida en este Website, siempre y cuando se mencione la fuente» | Mencionar la fuente para información de CMF | `verificada` para la fuente CMF; no resuelve el insumo histórico SUSESO de `ccaf_maestro` |
| **BCCh** — Banco Central de Chile | 24 | Series macro: dólar, cobre, tasas, curvas de bonos, deuda pública, expectativas de inflación | [Términos y Condiciones de la API BDE](https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/terms_es.htm): «Está permitido consultar, reproducir, difundir, publicar o adaptar la información contenida en la BDE, mencionando en todo momento que ella es propiedad del Banco» | Citar que la información es propiedad del Banco; declarar las adaptaciones; máximo 5 series por segundo | `verificada` |
| **SPensiones** — Superintendencia de Pensiones | 1 | Listado de administradoras de fondos de pensiones (7 filas de identidad) | [Descargo de responsabilidades](https://www.spensiones.cl/portal/institucional/594/w3-article-5885.html): «autoriza la utilización o reproducción total o parcial de la información contenida en este sitio, en citas o comentarios indicando su fuente» | Mencionar la fuente | `verificada` |

### Alcance de la autorización de la CMF

El descargo de la CMF autoriza la «reproducción total o parcial» de la
información de su sitio citando la fuente; no limita el volumen, el formato ni
el número de descargas. Sobre esa base se republican archivos regulatorios
completos —la cartera mensual de seguros de la Circular 1835, por ejemplo— en
Parquet, CSV y Excel. Esta es la lectura del proyecto y no constituye una
opinión jurídica: si la fuente cambiara sus términos o exigiera una autorización
previa para la redistribución masiva, el objeto afectado se retiraría o se
restringiría su descarga.

### Lo que no se publica, y por qué

- **Base de Cartera de los Fondos de Pensiones (SPensiones).** Su manual declara:
  «Esta base es de uso exclusivo para fines de investigación. Se solicita no
  distribuir esta información». Restringe el propósito y la distribución, con
  independencia de que haya o no ánimo de lucro, y choca con la licencia MIT del
  repositorio. El proyecto mantiene el bloqueo en
  [`pensiones/config/publicacion_bdp.json`](pensiones/config/publicacion_bdp.json)
  y no publica esa base ni derivados masivos.
- **SUSESO (procedencia histórica/editorial de `ccaf_maestro`).** `ccaf_balance`
  y `ccaf_resultados` se extraen de estados IFRS enviados a la **CMF**, y el
  pipeline actual no consume memorias ni estados financieros PDF de SUSESO. Sin
  embargo, la lista inicial de `ccaf_maestro` está documentada como construida
  también a partir de una lista de SUSESO. En esta revisión no se localizó ni
  verificó un documento de condiciones de reutilización aplicable a ese insumo
  histórico; por tanto, no se afirma que las condiciones de SUSESO sean
  inaplicables. El catálogo marca su estado como `pendiente_verificacion` dentro
  de `procedencia.condiciones_reutilizacion`. Esta cuestión queda abierta y
  separada de la autorización CMF para los datos CMF y las altas detectadas en
  el TXT IFRS.
- **Identificadores de terceros** (CUSIP/FactSet) de los índices de cartera que
  publica la CMF.

### Adaptaciones

`macro_inflacion_implicita` es un cálculo propio sobre las curvas del Banco
Central (diferencia entre el bono en pesos y el bono en UF del mismo plazo). Los
términos del Banco exigen declarar la adaptación: el objeto se publica con
`adaptacion: true` y la nota de que la adaptación es propiedad y responsabilidad
de este proyecto.

## Datos personales

El proyecto publica datos de personas naturales en tres conjuntos: 36 personas
naturales del registro fintech, 11 corredores inscritos a nombre de persona y 317
nombres de tasadores (233 en la primera tasación y 263 en la segunda; la fuente
mezcla personas naturales y sociedades tasadoras y no permite separarlas con
certeza). El tratamiento, la base de licitud, los derechos del titular y el
registro de actividades están en [`PRIVACIDAD.md`](PRIVACIDAD.md). Las reglas
técnicas de minimización viven en
[`pipelines/auto/privacidad.py`](pipelines/auto/privacidad.py).

## Datos derivados

Las proyecciones y tablas `_relevantes` que genera este repositorio (por ejemplo
`seguros_renta_fija_relevante`) son obra derivada de las anteriores: heredan su
condición y no añaden ninguna licencia nueva.

## Cómo citar

Cada conjunto publicado declara su cita en [`docs/api/v2/catalog.json`](docs/api/v2/catalog.json)
(`atribucion`), en [`docs/api/v2/datapackage.json`](docs/api/v2/datapackage.json)
(`sources[].sif_cita`) y en el catálogo de descargas del sitio. La forma general:

> Fuente: [organismo]. Datos obtenidos de [URL del documento de condiciones],
> consultados el [fecha]. Publicado por el Sistema de Información Financiera de
> Chile, `data_release` [valor].
