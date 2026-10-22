# Aviso de privacidad y tratamiento de datos personales

**Responsable:** Joaquín Mondaca, responsable del proyecto Sistema de Información
Financiera de Chile (en adelante, «el proyecto»).
**Canal para ejercer derechos:** [issues del repositorio](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/issues)
—abrir un issue titulado «Derechos Ley 21.719»—.
**Versión:** 1.0 · 22 de octubre de 2026.
**Norma aplicable:** Ley 21.719, que entra en vigencia el 1 de diciembre de 2026.

Este documento cumple el deber de información y transparencia del artículo 14 ter
de la Ley 21.719 y sirve de registro de las actividades de tratamiento. Se aplica
a los datos publicados en el sitio y en la API del proyecto.

## 1. Qué datos personales se publican

El proyecto publica datos de organismos públicos chilenos. La mayoría
corresponde a personas jurídicas, que no son objeto de la ley. Estos son los
tres conjuntos con datos de personas naturales:

| Conjunto | Personas | Datos | Origen |
|---|---|---|---|
| `fintech_rpsf_lista_entidades` | 36 personas naturales (de 264 prestadores) | RUT, nombre o razón social, comuna, región, sitio web, estado de vigencia | Registro de Prestadores de Servicios Financieros de la CMF (Ley 21.521) |
| `corredoras_bolsa_lista_entidades` | 11 corredores inscritos a nombre de persona natural (de 120) | RUT, nombre, estado de vigencia | Registro de corredores de bolsa de la CMF (Ley 18.045) |
| `seguros_bienes_raices` | 317 nombres de tasadores (233 en la tasación 1 y 263 en la tasación 2) | Nombre del tasador 1 y 2, tal como consta en la Circular 1835; la fuente mezcla personas naturales y sociedades tasadoras | Declaración de cartera de las aseguradoras a la CMF |

## 2. Qué datos personales no se publican

- **Correos de contacto.** La columna `email_contacto` de `fintech_rpsf_lista_entidades`
  se retiró el 22 de octubre de 2026. Contenía 253 direcciones, 46 de ellas en
  dominios personales. No es un dato registral y no aporta al fin del conjunto.
- **Deudores y asegurados.** Las columnas `nombre_deudor`, `rut_deudor` y
  `rut_deudor_sindicado` están vacías en las 2.321.911 filas de
  `seguros_renta_fija`: nunca se poblaron desde la fuente.
- **Direcciones y roles de inmuebles.** `seguros_bienes_raices` no publica
  dirección exacta ni rol; publica `comuna`, `ciudad` y un seudónimo estable
  (`property_id`) que permite seguir el mismo bien entre meses.
- **RUT de personas naturales en carteras.** En `fi_cartera_nacional` se suprime
  el RUT del emisor cuando probablemente corresponde a una persona natural y se
  agrega `emisor_tipo` con el criterio aplicado: **202.835 filas y 31.215 RUT
  distintos**, que no reaparecen en ningún otro objeto del catálogo. Contrastado
  contra registros públicos, el criterio alcanza a personas naturales
  identificables, no a entidades.

### 2.1 Una sola columna de identificador

`rut_emisor` no se vacía: se sustituye. Tiene dos contenidos posibles y una
columna que dice cuál es:

| `rut_emisor` | `rut_omitido_por_ley` | Cuándo |
|---|---|---|
| El RUT del emisor (cuerpo, sin dígito verificador) | falso | El emisor es una persona jurídica |
| Un seudónimo estable con prefijo `EMI-` | verdadero | El emisor es una persona natural: su RUT no se publica |
| Vacío | falso | La fuente no informa RUT |

El seudónimo es el mismo para la misma persona en cualquier trimestre y fondo, así
que se puede sumar su exposición, seguir su serie y medir concentración sin
revelar su identidad. Agrupar por emisor, sea del tipo que sea, es una sola línea:
`GROUP BY rut_emisor`.

El prefijo `EMI-` no es decorativo: evita que un seudónimo se confunda con un RUT
al leer la columna, al hacer un `JOIN` o al exportar a CSV.

El seudónimo no es una anonimización: el vínculo con el RUT vive en
una tabla privada que no se publica, y el artículo 2 letra k de la Ley 21.719
reserva la palabra «anonimización» para el procedimiento irreversible. Por eso la
bandera se llama `rut_omitido_por_ley` y no `anonimizado_por_ley`.

**Cambiar de criterio es configuración, no código.** La variable de entorno
`SIF_PUBLICAR_RUT_EMISOR` admite `suprimir` (por omisión, lo descrito aquí) y
`publicar`, que repone el RUT de las personas naturales y deja la bandera en
falso. La compuerta `scripts/auditar_personas_publicadas.py` verifica que la
bandera y el contenido de `rut_emisor` coincidan, y rechaza una publicación que
mezcle los dos modos.

## 3. Base de licitud

Los datos provienen de **fuentes de acceso público** en el sentido del artículo 2
letra i) de la ley: registros que la ley obliga a mantener y que cualquiera puede
consultar. Ese mismo artículo dispone que el tratamiento de datos de fuentes de
acceso público queda sujeto a la ley.

La base de licitud es el **interés legítimo** del artículo 13 letra d): reutilizar
información de registros públicos para dar transparencia al mercado financiero
chileno y permitir análisis estadístico reproducible. El proyecto no persigue
fines comerciales, no vende datos y no elabora perfiles.

Cuando un titular ejerce oposición, el proyecto evalúa la solicitud considerando
que el artículo 7 letra v) exceptúa la supresión cuando el tratamiento es
necesario para fines históricos, estadísticos o científicos de interés público, y
que el artículo 8 letra c) regula la oposición sobre datos de fuente de acceso
público. La respuesta se funda y se entrega por escrito.

## 4. Derechos del titular

Cualquier persona puede solicitar **acceso, rectificación, supresión, oposición y
portabilidad** sobre sus datos, y el **bloqueo temporal** mientras se resuelve una
solicitud de rectificación, supresión u oposición.

Cómo ejercerlos:

1. Abrir un issue en el repositorio con el título «Derechos Ley 21.719».
2. Indicar el derecho que se ejerce y el conjunto de datos afectado. Para acceso
   basta individualizarse; para oposición hay que señalar la causal.
3. El proyecto acusa recibo y responde por el mismo medio dentro de **30 días
   corridos**, prorrogables por una vez por otros 30. El bloqueo temporal se
   responde dentro de **2 días hábiles**.

Si la solicitud se rechaza o no se responde en plazo, el titular puede reclamar
ante la Agencia de Protección de Datos Personales.

## 5. Conservación y actualización

Los datos se publican mientras la fuente los publique. Las particiones
históricas se conservan para que un análisis pueda reproducirse: esa conservación
se ampara en los fines estadísticos y científicos del artículo 7 letra v). Una
rectificación u oposición se aplica a partir de la publicación siguiente y se
documenta en el historial del repositorio, que es público.

## 6. Destinatarios y encargados

No hay cesión ni comunicación de datos a terceros. El sitio se aloja en GitHub
Pages y su espejo en Vercel, que actúan como encargados del alojamiento sin acceso
a una base distinta de la publicada. Los datos publicados son, por definición,
accesibles a cualquiera que consulte el sitio.

## 7. Seguridad

El proyecto no almacena datos personales distintos de los que publica. El
repositorio no contiene credenciales, cada archivo se publica con su `sha256` y su
tamaño, y la integridad se verifica en cada integración continua. Una vulneración
que afecte derechos de titulares se reportará a la Agencia por el medio más
expedito, conforme al artículo 14 sexies.

## 8. Decisiones automatizadas

No se toman decisiones automatizadas ni se elaboran perfiles con datos
personales. Las tablas derivadas son agregaciones, filtros o cruces documentados,
no evaluaciones sobre personas.

## 9. Registro de actividades de tratamiento

| Finalidad | Titulares | Categorías de datos | Base de licitud | Origen | Destinatarios | Plazo |
|---|---|---|---|---|---|---|
| Publicar el registro de prestadores fintech | Personas naturales inscritas en el RPSF | Identificación (RUT, nombre), ubicación (comuna, región), sitio web | Interés legítimo (art. 13 d) | Registro público de la CMF | Público en general | Mientras la fuente lo publique |
| Publicar el registro de corredores de bolsa | Personas naturales inscritas como corredores | Identificación (RUT, nombre) | Interés legítimo (art. 13 d) | Registro público de la CMF | Público en general | Mientras la fuente lo publique |
| Publicar la nómina de tasadores de la cartera de seguros | Tasadores personas naturales | Nombre | Interés legítimo (art. 13 d) | Declaración regulatoria a la CMF (Circular 1835) | Público en general | Mientras la fuente lo publique |
| Reproducir series y estados financieros de entidades | Personas jurídicas (fuera del ámbito de la ley) | — | — | CMF, BCCh, SPensiones | Público en general | Mientras la fuente lo publique |

## 10. Cambios

Cada cambio de este documento sube la versión y queda registrado en el historial
del repositorio. La fecha de la primera versión es el 22 de octubre de 2026.
