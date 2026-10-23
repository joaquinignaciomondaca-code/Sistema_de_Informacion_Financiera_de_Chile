# ¿Se pueden publicar estos datos?

> **Estado (2026-10-23).** El contrato vigente es **2.0.0** y se publica en
> `docs/api/v2/`. Esta nota se escribió cuando la ruta era `api/v1/`: las rutas de
> archivo y de URL se actualizaron para que los comandos sigan funcionando, y las
> referencias a «v1» como nombre de la fase se conservan como se escribieron.

**Revisión de condiciones de uso de las fuentes y de la Ley 21.719 sobre los datos ya publicados**

| | |
|---|---|
| **Fecha** | 2026-10-22 |
| **Objeto revisado** | Los 90 objetos de `docs/api/v2/` y las tablas de `docs/outputs/` que los alimentan |
| **Método** | Texto vigente de cada fuente (citado abajo) cruzado con consultas sobre los Parquet publicados, no con una opinión general |
| **Naturaleza** | Análisis operativo de cumplimiento. No sustituye la revisión de un abogado antes del 1 de diciembre de 2026 |

## 1. Veredicto

**Los datos se pueden publicar, con condiciones, y hoy no se cumplen tres de ellas.** No hay prohibición general en CMF ni en el Banco Central; la restricción fuerte que se temía existe, pero recae sobre una base que este repositorio **no** publica.

| Fuente | Objetos | Filas | ¿Se puede publicar? | Condición pendiente |
|---|---|---|---|---|
| CMF | 65 | 19.736.045 | **Sí**, citando la fuente | La cita no está implementada por recurso |
| BCCh | 24 | 41.452 | **Sí**, citando que la información es propiedad del Banco | Ídem, más declarar las adaptaciones |
| SPensiones | 1 | 7 | **Sí** para el listado de AFP | Nada |
| SUSESO | 0 | 0 | No hay datos de esta fuente | La fila del `DATA_LICENSE.md` está mal |

Fuera de eso, el riesgo real no viene de las condiciones de las fuentes sino de la **Ley 21.719**: el repositorio publica datos de personas naturales y no tiene aviso de privacidad, canal de derechos ni registro de tratamiento.

## 2. Fuente por fuente

### 2.1 CMF — sí, con mención de la fuente

**Descargo de Responsabilidades** ([cmfchile.cl/portal/principal/623/w4-article-1833.html](https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html)):

> «La Comisión para el Mercado Financiero autoriza la reproducción total o parcial de la información contenida en este Website, siempre y cuando se mencione la fuente.»

Añade que no garantiza la exactitud de la información y que **la versión impresa es la oficial**.

No hay cláusula de uso exclusivo ni límite a fines de investigación. La condición es una sola y es trivial de cumplir: mencionar la fuente. Lo que **no** está cubierto por esa autorización son los datos de terceros que la CMF publica por obligación de sus fiscalizados —por ejemplo los identificadores CUSIP/FactSet en las carteras—, que este repositorio no redistribuye.

### 2.2 BCCh — sí por la API, con dos condiciones

**Términos y Condiciones de la API BDE** ([si3.bcentral.cl/…/Web_Services/terms_es.htm](https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/terms_es.htm)):

> «Está permitido consultar, reproducir, difundir, publicar o adaptar la información contenida en la BDE, mencionando en todo momento que ella es propiedad del Banco. En el caso de adaptaciones que pudieran ser publicadas o difundidas, deberá señalarse que la información de origen pertenece al Banco o a quien corresponda y que la adaptación es propiedad y responsabilidad exclusiva de quien la realiza.»

Condiciones operativas:

1. **Atribución** («propiedad del Banco Central de Chile») en cada tabla.
2. **Adaptaciones identificadas.** `macro_inflacion_implicita` es un cálculo propio (BCP−BCU) y debe declararse como adaptación, no como dato del Banco.
3. **Máximo 5 series simultáneas por segundo por cuenta.** `macro/scripts/series_bcch.py` usa `ThreadPoolExecutor(max_workers=6)` sin limitador: puede superar el límite. Rebajar a 4 es un cambio de una línea.
4. Los derechos son gratuitos e indefinidos **pero revocables** a discreción del Banco.

**Contraste que conviene tener presente:** los términos institucionales de `bcentral.cl` prohíben «la venta, distribución, circulación o transmisión» de los contenidos sin autorización previa expresa. No hay contradicción real: el canal que usa este repositorio es la API, y sus términos específicos autorizan publicar. La consecuencia práctica es que la atribución debe decir **«Fuente: Banco Central de Chile, BDE/SIETE»** y no presentarse como una copia del sitio web.

### 2.3 SPensiones — sí para lo que se publica, no para lo que no se publica

Dos documentos distintos, con alcances distintos:

**Descargo de responsabilidades del sitio** ([spensiones.cl/…/w3-article-5885.html](https://www.spensiones.cl/portal/institucional/594/w3-article-5885.html)):

> «La Superintendencia de Pensiones autoriza la utilización o reproducción total o parcial de la información contenida en este sitio, en citas o comentarios indicando su fuente.»

**Manual de la Base de Cartera de los Fondos de Pensiones** (versión mayo 2020, nota al pie 1), citado en [`pensiones/AUTOMATIZACION_BDP.md`](../../pensiones/AUTOMATIZACION_BDP.md):

> «Esta base es de uso exclusivo para fines de investigación. Se solicita no distribuir esta información.»

Esta es la restricción que se buscaba. Aplica **a la base de cartera del BDP**, no al listado de administradoras: restringe el propósito y la distribución, con independencia de que haya o no ánimo de lucro, y publicarla en un repositorio MIT chocaría con la licencia que concede «publish, distribute, sublicense». El repositorio ya la trata como bloqueada y **no la publica**: de SPensiones solo sale `afp_lista_entidades`, con siete filas y cuatro campos de identidad (`id`, RUT, razón social y nombre de fantasía), todas personas jurídicas.

Conclusión: **no hay nada que retirar por esta vía**; lo que corresponde es mantener el bloqueo y no reactivar los generadores de cartera.

### 2.4 SUSESO — la fila del `DATA_LICENSE.md` no corresponde

Las **Condiciones de uso** de [suseso.gob.cl](https://www.suseso.gob.cl/606/w3-article-19630.html) permiten reproducir contenidos con fines compatibles con el sitio y sin uso comercial, sin modificarlos. Es una licencia más restrictiva que la de la CMF, pero irrelevante aquí: **este repositorio no publica datos de SUSESO**. `ccaf_balance` y `ccaf_resultados` (13.549 filas) provienen de los estados financieros IFRS que las CCAF envían a la **CMF** (`estadisticas_ifrs.php`), y la lista de entidades es un catálogo curado con enlaces a ambos reguladores. La fila «SUSESO» del `DATA_LICENSE.md` describe una fuente que no alimenta ningún dato.

## 3. Datos personales: lo que realmente está publicado

La Ley 21.719 protege a **personas naturales**, no a personas jurídicas. De los 90 objetos, 87 contienen solo entidades, instrumentos o series. Estos son los tres que contienen datos de personas, medidos sobre los Parquet publicados:

| Objeto | Filas | Qué contiene | Evaluación |
|---|---|---|---|
| `fintech_rpsf_lista_entidades` | 264 | 226 personas jurídicas, **36 personas naturales** y 2 sin tipo. Las 36 llevan RUT+DV, razón social (nombre de la persona), email, comuna, región y sitio web. **46 correos en dominios personales** (gmail, hotmail, outlook, yahoo). | Publicable en su núcleo registral; el **email no es necesario** para el fin del dataset |
| `corredoras_bolsa_lista_entidades` | 120 | **11 corredores de bolsa inscritos a nombre de persona natural**, con RUT+DV y nombre (p. ej. `BRANCHI BRANCHI PABLO`, `1347879-1`; `ETCHEGARAY GIL TOMAS`, `1571295-3`) | Datos de un registro público obligatorio (Ley 18.045); sin datos de contacto. Publicable |
| `seguros_bienes_raices` | 760.152 | `nombre_del_tasador_1/2`: **317 nombres distintos** (233 en la tasación 1 y 263 en la 2), entre personas naturales y sociedades tasadoras | Nombres de peritos tal como constan en la Circular 1835; sin RUT ni contacto. Publicable |

**Lo que se revisó y no es dato personal publicado:**

- `seguros_renta_fija.nombre_deudor`, `rut_deudor` y `rut_deudor_sindicado`: **vacíos en las 2.321.911 filas**. No hay dato de deudores.
- `seguros_renta_fija.rut_lider` / `nombre_lider` (10.698 filas): 13 bancos, no personas.
- `domicilio_casa_matriz` (AGF, CCAF, sistemas de pago): domicilio de personas jurídicas.
- `nombre_custodio`, `nombre_contraparte_garantia`, `nombre_emisor`: bancos, custodios y aseguradoras.
- `nacionalidad`: país del instrumento, no de una persona.

### 3.1 Base de licitud

El registro RPSF de la CMF y el registro de corredores son **fuentes de acceso público** en el sentido del artículo 2 letra i) de la Ley 21.719 («los registros públicos que disponga la ley»), y ese mismo artículo cierra: «El tratamiento de datos personales provenientes de fuentes de acceso público se someterá a las disposiciones de esta ley». Es decir: ser público habilita el tratamiento, no exime de las obligaciones.

La base invocable es **interés legítimo** (art. 13 d) —reutilizar información de registros públicos con fines de transparencia del mercado financiero—, complementada con los fines **estadísticos y científicos** que el artículo 7 letra v) reconoce como causa para no suprimir datos.

### 3.2 Obligaciones que hoy no se cumplen

| Obligación | Norma | Estado en el repositorio |
|---|---|---|
| Deber de secreto o confidencialidad, que alcanza a los datos obtenidos de fuentes públicas **cuando se organizan, clasifican, combinan o complementan** | art. 14 bis | Es exactamente lo que hace el pipeline (normaliza, cruza y deriva tablas). No hay medida declarada |
| Política de tratamiento publicada, con categorías, finalidades, base de licitud, fuente, plazo de conservación y derechos | art. 14 ter | **No existe** ningún aviso de privacidad en el sitio |
| Canal para ejercer acceso, rectificación, supresión, oposición y portabilidad, con respuesta en 30 días corridos | arts. 4–8 y 14 ter f) | **No existe** |
| Registro de actividades de tratamiento | art. 14 ter y ss. | **No existe** |
| Protección desde el diseño y por defecto (solo lo estrictamente necesario) | art. 14 quáter | **Incumplido**: se publican 46 correos personales que el dataset no necesita |
| Reportar vulneraciones | art. 14 sexies | Sin procedimiento |

La ley entra en vigencia el **1 de diciembre de 2026**, es decir en 40 días. Hay un proyecto para postergarla al 1 de diciembre de 2027 (boletín 18.623-07), en primer trámite: **no es ley** y no corresponde planificar sobre él.

### 3.3 ¿La supresión protege personas reales?

`fi.cartera_nacional` suprime `rut_emisor` cuando el RUT es menor a 50.000.000 y no figura en el padrón de 3.280 entidades conocidas. Conviene medir si ese criterio alcanza a personas naturales efectivas o solo a un subconjunto estadístico.

- **Volumen suprimido.** Contrastando la versión publicada con la anterior al commit `3b88beb`, desaparecen **202.835 filas y 31.215 RUT distintos**, en 28 fondos. Son el 0,28 % del monto del objeto (795.356 miles de la moneda funcional frente a 288.512.050). Por instrumento: 202.437 filas en «otros títulos de deuda nacional», 208 en mutuos hipotecarios y 186 en «otros títulos».
- **Control de fuga.** Ninguno de esos 31.215 RUT aparece en los **55 objetos publicados que tienen alguna columna de RUT** (cruce sobre todo el catálogo, 0 coincidencias). La supresión es consistente: no queda identificado en otra tabla.
- **Verificación nominal externa.** El registro público de solicitantes de certificados de cumplimiento de obligaciones laborales y previsionales de la Dirección del Trabajo (formulario F30-1, año 2024) publica RUT con el nombre de la persona o empresa solicitante. Al menos uno de los RUT suprimidos aparece ahí como **persona natural identificada con nombres y apellidos**, con el mismo dígito verificador que calcula el propio pipeline. Por minimización no se reproduce aquí el nombre ni el RUT, ni se incorporan a ninguna tabla.
- **Conclusión.** La regla no suprime «probables personas» en abstracto: suprime personas naturales reales, cuya identidad el proyecto puede verificar pero no publica. El criterio se mantiene sin cambios; cualquier modificación es una decisión de publicación que corresponde al responsable del repositorio.

### 3.4 ¿Por qué la Dirección del Trabajo y la CMF publican lo que el proyecto omite?

La asimetría que se percibe —un servicio público publica el RUT con nombre y apellido, el proyecto lo suprime— no está en el permiso, sino en el rol y en la finalidad. Son tres diferencias acumuladas.

| Dimensión | Dirección del Trabajo | CMF | Este proyecto |
|---|---|---|---|
| Mandato | El registro existe porque el art. 183-C del Código del Trabajo obliga a mantenerlo público | Publica los informes IFRS porque es la supervisora y los fondos deben remitirlos | Ninguno: hace un tratamiento nuevo de datos ajenos |
| Qué asocia al RUT | «Solicitó un certificado laboral»: acto administrativo, sin contenido financiero | El RUT del emisor, sin nombre, en una página HTML por fondo y trimestre | RUT + instrumento + monto + fondo + trimestre: un perfil financiero indexado |
| Deber que carga | Responde por su registro | Responde por su registro | Responde por su propio tratamiento (art. 14 bis de la Ley 21.719, que alcanza a los datos resultantes de organizar o combinar fuentes públicas) |

**Qué permite la ley vigente.** El artículo 4 de la Ley 19.628 exige ley o consentimiento, pero su inciso quinto exime de autorización el tratamiento de datos provenientes de fuentes accesibles al público «cuando sean de carácter económico, financiero, bancario o comercial». Eso cubre, en principio, la cartera de un fondo publicada por la CMF. En consecuencia: **publicar no sería hoy una infracción automática, y suprimir tampoco es una obligación legal**; es una decisión de prudencia.

**Qué cambia el 1 de diciembre de 2026.** La Ley 21.719 sustituye esa lógica de exenciones por un régimen de principios: base de licitud (art. 13), finalidad, minimización (art. 14 quáter), transparencia (art. 14 ter) y seguridad. La base invocable pasaría a ser el interés legítimo, que exige ponderación y un aviso publicado. El régimen sancionatorio (arts. 34 bis a 35) fija hasta 5.000 UTM para infracciones leves, 10.000 para las graves —entre ellas tratar sin base de licitud— y 20.000 para las gravísimas.

**Señal legislativa.** El Congreso ha presentado varios proyectos para restringir la publicación de datos de deudas de carácter económico o financiero (boletines 13897-03, 13695-03, 12924-03, 11841-03 y 11716-07). Ninguno es ley, pero la dirección es hacia restringir, no hacia ampliar.

**Conclusión.** Publicar los RUT de personas naturales que actúan en el mercado por su rol —corredores de bolsa, tasadores, representantes de fintech— es defendible: el registro público existe precisamente para informar al mercado sobre ellas. Publicar los de contrapartes de pagarés y mutuos hipotecarios es lo discutible, y tampoco aporta al análisis: `emisor_tipo` conserva el conteo y el monto de esas filas.

## 4. Los cinco defectos concretos

1. **La atribución no está implementada en el contrato.** `catalog.json` no tiene campo de fuente en ninguno de los 90 objetos (`fuente`, `url_fuente` o `norma`), y `datapackage.json` declara una licencia genérica. La condición de la CMF y del BCCh es «mencionar la fuente»: hoy solo se cumple en texto de la web, no en el dato que consume una API o un agente.
2. **Las adaptaciones no se declaran.** `macro_inflacion_implicita` es cálculo propio sobre series del BCCh y no lleva la nota de adaptación que exigen los términos.
3. **Falta minimización.** Los 46 correos personales de `fintech_rpsf_lista_entidades` no aportan al fin del dataset y son el dato con mayor riesgo reputacional y legal del repositorio.
4. **No hay aviso de privacidad ni canal de derechos**, ni en el sitio ni en el repositorio.
5. **`DATA_LICENSE.md` describe fuentes que no se usan** (SUSESO) y objetos retirados (valor cuota de los fondos), y mantiene las cuatro fuentes en `pendiente` cuando dos ya están verificadas.

Un sexto punto, menor pero de cumplimiento: el límite de 5 series por segundo del BCCh frente a `max_workers=6`.

## 5. Ruta ejecutada el 2026-10-22

- [x] **5.1 · Atribución por recurso.** Añadir `fuente`, `fuente_url` y `atribucion` a los 90 objetos de `catalog.json`, `datapackage.json` y `schema/*.json`, y mostrarlos en la web. Regenerar el contrato.
- [x] **5.2 · Adaptaciones.** Marcar `macro_inflacion_implicita` (y cualquier otro cálculo) con `es_adaptacion: true` y la nota de propiedad del Banco.
- [x] **5.3 · Minimización.** Retirar `email_contacto` de `fintech_rpsf_lista_entidades`; decidir si se conserva con máscara. Requiere regenerar catálogo, esquema, particiones y resultados.
- [x] **5.4 · Aviso de privacidad y derechos.** Página propia en el sitio (política, base de licitud, fuente, plazo, canal ARCOP) y archivo `PRIVACIDAD.md` enlazado desde la Guía. Sin esto, la publicación de las 36 personas naturales y los 11 corredores queda sin el deber de transparencia del art. 14 ter.
- [x] **5.5 · `DATA_LICENSE.md` corregido.** CMF y BCCh en `verificada` con la cita textual y la URL; SPensiones en `verificada` solo para el listado de AFP, con el bloqueo del BDP documentado; SUSESO retirada de la tabla y anotada como enlace, no como fuente de datos.
- [x] **5.6 · Límite del BCCh.** `max_workers=4` en `macro/scripts/series_bcch.py`.
- [x] **5.7 · Registro de tratamiento.** Documento interno con finalidades, base de licitud, categorías, destinatarios y plazo, para poder acreditarlo ante la Agencia.

Los pasos 5.1 y 5.2 cierran la condición de las fuentes; 5.3, 5.4 y 5.7 cierran el
riesgo de la Ley 21.719; 5.5 y 5.6 son correcciones de exactitud.

**Qué cambió, en concreto:**

| Paso | Implementación |
|---|---|
| 5.1 | `pipelines/api/fuentes.py` define fuente, cita, URL del documento y estado; `build_contrato.py` los publica en `catalog.json` y en cada `schema/*.json`; `build_api.py` en `sources[].sif_cita` y `sif.atribucion`; `build_download_catalog.py` en el catálogo de descargas, y la web los muestra en cada tarjeta y en la Guía |
| 5.2 | `macro_inflacion_implicita` se publica con `adaptacion: true` y `nota_adaptacion` |
| 5.3 | `privacidad.retirar_contacto()` y el publicador de fintech dejan de escribir `email_contacto`; `enmascarar_identificadores.py --apply` la retiró de lo publicado (253 direcciones). Quedan 0 referencias en el contrato |
| 5.4 | `PRIVACIDAD.md` y `docs/privacidad.html`, enlazados desde Información, la Guía y la nota de uso |
| 5.5 | `DATA_LICENSE.md` reescrito: CMF, BCCh y SPensiones en `verificada` con cita textual y URL; SUSESO retirada como fuente |
| 5.6 | `series_bcch.py` con `max_workers=4` y el motivo escrito en el código |
| 5.7 | Registro de actividades de tratamiento en el apartado 9 de `PRIVACIDAD.md` y en la página del sitio |

## 6. Lo que no se publica y no debe publicarse

- **Cartera de los Fondos de Pensiones (BDP).** Uso exclusivo para investigación y prohibición de distribuir según el manual histórico; sin verificación de la versión vigente ni autorización de la SP. El repositorio mantiene el bloqueo en `pensiones/config/publicacion_bdp.json`.
- **Identificadores de terceros** (CUSIP/FactSet) presentes en los índices de cartera que publica la CMF.
- **Cualquier dato de deudores o asegurados individuales**, aunque aparezca en un archivo regulatorio: no es necesario para el fin del proyecto y agrava el art. 14 bis.

## 7. Fuentes consultadas

| Documento | URL | Fecha de consulta |
|---|---|---|
| CMF, Descargo de Responsabilidades | https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html | 2026-10-22 |
| BCCh, Términos y Condiciones API BDE | https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/terms_es.htm | 2026-10-22 |
| BCCh, Términos de uso institucionales | https://www.bcentral.cl/en/terms-of-use | 2026-10-22 |
| SPensiones, Descargo de responsabilidades | https://www.spensiones.cl/portal/institucional/594/w3-article-5885.html | 2026-10-22 |
| SPensiones, manual BDP (cita en el repositorio) | `pensiones/AUTOMATIZACION_BDP.md` | 2026-10-22 |
| SUSESO, Condiciones de uso | https://www.suseso.gob.cl/606/w3-article-19630.html | 2026-10-22 |
| Ley 21.719 (LeyChile, vigencia 2026-12-01) | https://www.bcn.cl/leychile/navegar?idNorma=1209272 | 2026-10-22 |
