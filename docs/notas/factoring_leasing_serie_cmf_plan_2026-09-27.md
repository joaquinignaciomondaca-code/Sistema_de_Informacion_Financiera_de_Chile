# Serie CMF IFRS para Factoring y Leasing — backfill en cuarentena

Solicitado: recuperar **todo el histórico disponible en el índice CMF para todos los RUT del catálogo de Factoring y Leasing**, no quedarse en las dos filas de prueba. La muestra publicada de 2022 sigue visible sin cambiar hasta terminar controles de cobertura y calidad del histórico.

Fuente: [Estados financieros IFRS en TXT](https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php), con archivos `ver_archivo.php?inicio=AAAAMM&termino=AAAAMM`. El índice CMF lista períodos desde 2009; cada enlace anual se divide en trimestres. El formato del TXT es `periodo;rut;nombre;I/C;moneda;cuenta;valor;taxonomia;estado`. Se descargan los trimestres una sola vez (uno por llamada) y se consultan diariamente **solo los nuevos o fallidos** después de terminar el backfill. Se conserva el valor literal y se separan todas las cuentas ESF (balance) de todas las cuentas ER (resultado), incluyendo balances individuales y consolidados **sin sumarlos ni mezclarlos**.

Alcance del universo: **28 RUT del catálogo local**, incluyendo los segmentos mixtos y 2 automotrices presentes en esa carpeta, marcados como tales. No se asume que los 28 reporten en la fuente ni que el catálogo sea un padrón completo o vigente. Un período sin ningún RUT objetivo se marca `sin_rut_catalogo`; una entidad sin estado financiero se identifica en el resumen. El nombre reportado se conserva por período y se distingue del nombre actual del catálogo. La moneda queda tal cual aparece en el TXT: **no se fuerza CLP a otras monedas, no se aplica FX, no se redondea ni se divide por 1.000 sin cotejo**. En la primera ejecución el TXT más reciente incluyó un importe no entero; el extractor ahora conserva el texto original, deja el valor numérico en `null` y lo cuenta como pendiente de interpretación en vez de convertirlo silenciosamente a cero o detener todo el backfill. Se conservan los tipos I/C y taxonomías por separado.

La tarea `.github/workflows/factoring_leasing_backfill.yml` corre en Actions en el branch de trabajo con disparo `push`/`workflow_dispatch`; el `schedule` solo comenzará cuando el workflow esté en `main`. El estado por trimestre y los Parquets están **exclusivamente en `.local-data/factoring_leasing_serie/`** (caché más artifact temporal de 30 días), nunca en `docs/outputs`. Los archivos y resumen se recuperan en el siguiente run de la **misma rama**. Una falla no avanza el cursor ni reemplaza archivos publicados; el período fallido se vuelve a intentar. El resumen incluye progreso, cuentas, RUT cubiertos, ausentes, períodos sin datos y errores.

## Puerta antes de publicar la serie

1. Confirmar que completó todos los períodos listados; revisar errores y vacíos.
2. Resolver nombres/RUT históricos, contextos duplicados, diferentes taxonomías/unidades y cobertura por RUT/período.
3. Cotejar muestras adicionales con fichas CMF (por años y entidades) y determinar qué resultados son acumulados vs trimestrales; validar la escala del TXT según moneda.
4. Producir dos tablas públicas claras y separadas de balance y estado de resultados, con rótulo de cobertura real, auditadas antes de reemplazar las muestras actuales. La mera presencia de un ZIP/XBRL o el cuadre interno **no** constituye aprobación.

**No subir aquí los Parquets masivos**: no están auditados ni tienen autorización para sustituir la web existente. La fuente es un TXT público distinto de los ZIP bancarios del otro enlace; esos ZIP y el PDF de Excel por banco quedan para revisión independiente.
