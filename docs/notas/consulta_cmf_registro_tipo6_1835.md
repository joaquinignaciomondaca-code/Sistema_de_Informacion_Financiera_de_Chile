# Borrador de consulta técnica a CMF: tipo de registro 6 en B.11/B.14

**Estado:** borrador preparado; no enviado.

**Asunto:** Circular 1835: aclaración de registros tipo 6 en archivos E (B.11) y G (B.14)

Estimados/as,

Estamos validando los archivos mensuales de carteras de inversiones de compañías de seguros publicados por la CMF, conforme al Anexo Técnico de la Circular 1835. En archivos `EaammddG.TXT` (B.11, Flujos de Activos Elegibles) y `GaammddG.TXT` (B.14, Garantías en Instrumentos Derivados) encontramos líneas cuyo primer carácter es el tipo de registro `6`.

El Anexo Técnico que consultamos describe para B.11 y B.14 los registros de identificación (tipo 1), detalle (tipo 2) y totales (tipo 3), pero no especifica un tipo 6. Las líneas observadas tienen el largo fijo completo de sus archivos —178 caracteres para E y 300 para G—, de modo que no parecen truncamientos. El hallazgo se repitió en archivos generales de 2024-12 a 2025-03: cuatro archivos E y seis archivos G.

Como comprobación adicional, el 21-10-2026 descargamos en modo de solo lectura el PDF disponible actualmente en la URL oficial indicada abajo, mediante GitHub Actions (run `39639786869`). El archivo descargado tuvo SHA-256 `16aed30312439a9d33abbe90efd863751e0a0cabc394d84d15640233382a1f71`, 1.659.958 bytes y 210 páginas; el servidor indicó `Last-Modified: Mon, 23 Dec 2024 10:21:14 GMT`. La extracción de B.11 y B.14 no encontró menciones a “registro tipo 6” en ninguna de las dos secciones. Esta verificación no contactó ni envió información a la CMF.

Agradeceríamos confirmar:

1. ¿Es válido el tipo de registro 6 en B.11 y/o B.14? ¿Desde qué período o versión de la especificación rige?
2. ¿Cuál es el layout oficial de ese registro (campos, posiciones, picture, dominios y reglas de cuadratura)?
3. ¿Cómo debe relacionarse con los registros de detalle tipo 2 y totales tipo 3? ¿Debe incorporarse como otro detalle, como control/resumen, o tratarse de otra forma?
4. ¿Existe una versión más reciente del anexo o una instrucción SEIL que documente el cambio?

Mientras no exista una definición oficial, nuestro proceso conserva una alerta y aísla el archivo de compañía afectado, en lugar de interpretar campos desconocidos o publicarlos con semántica supuesta. No incluimos valores de las líneas en esta consulta. Si es necesario, podemos proporcionar identificadores de archivo y una muestra redactada por el canal seguro que ustedes indiquen.

Fuente consultada: [Anexos Técnicos de la Circular 1835](https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf).

Saludos cordiales,

[Nombre / organización]
