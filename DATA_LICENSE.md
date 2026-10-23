# Licencia de los datos

Este repositorio mezcla dos cosas que **no** comparten licencia: el código que
los produce y los datos que publica. La licencia MIT del repositorio cubre el
código, los scripts y la documentación; **no** cubre los datos de terceros que
se redistribuyen aquí.

## Código

MIT. Ver [`LICENSE`](../LICENSE).

## Datos

Los datos son de organismos públicos chilenos. Este proyecto los descarga, los
normaliza y los republica en Parquet **sin alterar sus valores**, citando la
fuente en cada recurso: el catálogo, el descriptor Data Package y el catálogo de
descargas declaran la misma cita, que sale de una sola definición
([`pipelines/api/fuentes.py`](../pipelines/api/fuentes.py)).

**Las tres fuentes autorizan la republicación con una condición: citarlas.** No
exigen autorización escrita ni limitan el uso a fines de investigación.

| Fuente | Objetos | Qué publica aquí | Documento vigente | Condición | Estado |
|---|---|---|---|---|---|
| **CMF** — Comisión para el Mercado Financiero | 65 | Bancos, seguros (Circular 1835), fondos mutuos y de inversión, AGF, corredoras, securitizadoras, CCAF, factoring y leasing, patrimonios separados, cooperativas, fintech, sistemas de pago | [Descargo de Responsabilidades](https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html): «autoriza la reproducción total o parcial de la información contenida en este Website, siempre y cuando se mencione la fuente» | Mencionar la fuente | `verificada` |
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
  [`pensiones/config/publicacion_bdp.json`](../pensiones/config/publicacion_bdp.json)
  y no publica esa base ni derivados masivos.
- **SUSESO.** No es fuente de ningún objeto publicado. `ccaf_balance` y
  `ccaf_resultados` salen de los estados financieros IFRS que las CCAF envían a
  la **CMF**; la lista de entidades es un catálogo curado con enlaces a ambos
  reguladores. Sus condiciones de uso no aplican a lo publicado.
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
registro de actividades están en [`PRIVACIDAD.md`](../PRIVACIDAD.md). Las reglas
técnicas de minimización viven en
[`pipelines/auto/privacidad.py`](../pipelines/auto/privacidad.py).

## Datos derivados

Las proyecciones y tablas `_relevantes` que genera este repositorio (por ejemplo
`seguros_renta_fija_relevante`) son obra derivada de las anteriores: heredan su
condición y no añaden ninguna licencia nueva.

## Cómo citar

Cada conjunto publicado declara su cita en `api/v2/catalog.json`
(`atribucion`), en `api/v2/datapackage.json` (`sources[].sif_cita`) y en el
catálogo de descargas del sitio. La forma general:

> Fuente: [organismo]. Datos obtenidos de [URL del documento de condiciones],
> consultados el [fecha]. Publicado por el Sistema de Información Financiera de
> Chile, `data_release` [valor].
