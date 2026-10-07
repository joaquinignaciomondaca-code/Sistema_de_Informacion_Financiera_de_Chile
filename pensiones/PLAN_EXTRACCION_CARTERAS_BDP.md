# Plan de extracción masiva de carteras históricas AFP — portal BDP

**Fecha: 07-10-2026. Propuesta de diseño, no implementación ni publicación.**

## 1. Qué se puede obtener

La base BDP no contiene sólo derivados: contiene posiciones de cartera en múltiples instrumentos, identificadas por fecha, AFP, fondo y nemotécnico/serie. La captura del usuario confirma tres paquetes históricos (1996–2005, 2006–2015 y 2016–a la fecha) y un paquete/documento de descripción. La fecha anunciada de cierre de base es 01/MAY/2026; no se certificó el último corte dentro del paquete actual.

Se inspeccionaron el manual histórico SP de mayo 2020 y un XLSX de enero–mayo de 2021 conservados en un **espejo GitHub de terceros**, no los CSV actuales descargados de SP. El archivo observado tiene 157.421 filas, 18 columnas y 63 códigos distintos. La clasificación propuesta de sus códigos en 14 familias cubre todas las filas una sola vez: no quedan códigos sin asignar ni hay cruces entre familias en esta muestra.

**Esto confirma potencial de extracción instrumental, no 157.421 contratos ni operaciones de compraventa.** Son observaciones mensuales de posición; el mismo instrumento puede aparecer en distintos cortes. Las series de derivados tampoco son IDs universales de contratos.

## 2. Separación propuesta por tablas

Los nombres siguientes son propuestos, no tablas ya disponibles en la web. Separar por familia, no por AFP, año, mercado o moneda; esas aperturas deben ser columnas/filtros y particiones físicas. El significado de cada código se debe versionar contra el diccionario SP vigente en cada fecha.

| Tabla propuesta | Contenido | Códigos observados en la muestra 2021 | Filas observadas |
|---|---|---|---:|
| `afp_cartera_renta_fija` | Bonos públicos/privados, letras hipotecarias, bonos de reconocimiento, convertibles y otros títulos de deuda; subtipo conservado | BTU, BTP, DEB, BRP, BVL, LHF, BCS, BCA, BEF, BSF, BCU, BCP, PRC, EBC, BEE, TBI, BSE, BFI, BHM, TBE, BEC, CERO | 55.876 |
| `afp_cartera_intermediacion_financiera` | Depósitos a plazo y pagarés descontables; ampliar con otros instrumentos del diccionario | DPF, PDC | 1.741 |
| `afp_cartera_acciones` | Acciones nacionales/extranjeras y ADR | ACC, ADR, AEE | 7.467 |
| `afp_cartera_cuotas_fi` | Cuotas de fondos de inversión nacionales/extranjeros | CFIV, CFID, CIEV | 6.053 |
| `afp_cartera_cuotas_ffmm` | Cuotas de fondos mutuos nacionales/extranjeros | CFMV, CFMD, CMEV, CMED | 18.133 |
| `afp_cartera_etf` | Títulos representativos de índices accionarios/renta fija | ETFA, ETFB | 4.824 |
| `afp_cartera_capital_privado` | Vehículos, aportes comprometidos y coinversiones de capital privado | ACPE, VCPE, CCPE, KCPE | 2.242 |
| `afp_cartera_deuda_privada` | Vehículos y aportes comprometidos de deuda privada | ADPE, VDPE | 915 |
| `afp_cartera_creditos_sindicados` | Participaciones en convenios de crédito | CSIN | 75 |
| `afp_cartera_promesas_cuotas_fi` | Promesas de suscripción/pago; no mezclar automáticamente con cuotas adquiridas | PFI | 3.679 |
| `afp_cartera_disponibilidades` | Posiciones de cuentas corrientes de inversión nacional/extranjera | CC2, CC3 | 1.055 |
| `afp_derivados_forwards` | Compra/venta, distintos subyacentes, mercados y modalidades; no sólo monedas | WNMV, WNMC, WNNV, WNNC, WNTC, YENV, WEMV, YEMC, WEMC, YEMV, YENC, WENV | 48.850 |
| `afp_derivados_swaps` | Tasas/monedas, preservando los campos de ambas partes y la modalidad | SNT, YSET, YSEM, SNM | 6.462 |
| `afp_derivados_opciones` | Opciones; en la muestra sólo opciones de suscripción OSAN | OSAN | 49 |
| **Total** | Una asignación de cada fila de origen | **63 códigos** | **157.421** |

No equiparar las modalidades de compromiso con inversión desembolsada o valor contable de un activo. En capital/deuda privados conservar un campo `subtipo_fuente` que distinga vehículo, compromiso y coinversión; ofrecer vistas separadas si se necesita sumar magnitudes homogéneas. No sumar indiscriminadamente todas las familias bajo «activos totales».

### Familias descritas por el manual, sin observaciones en la muestra examinada

El diccionario histórico incluye futuros nacionales/extranjeros (familias FN/FE), más clases de opciones y swaps; bienes raíces (RAIZ), mutuos hipotecarios (MHE), leasing (CLEA), vehículos de infraestructura/inmobiliarios (VIPE/VRPE) y notas estructuradas (ELN), entre otros. Se pueden preparar rutas como `afp_derivados_futuros`, `afp_cartera_inmobiliaria`, `afp_cartera_mutuos_hipotecarios` y `afp_cartera_estructurados`, **pero no certificar filas, cobertura o fechas sin revisar los originales de los demás años**. No crear salidas vacías fingiendo que se verificó ausencia en toda la historia.

No clasificar exclusivamente por primera letra: instrumentos ordinarios también comparten prefijos con derivados. Usar diccionario explícito por código completo y versión/fecha; un código nuevo debe ir a cuarentena y bloquear la certificación completa del lote.

## 3. Campos comunes y específicos

### Núcleo de toda fila

- `fecha_corte_fuente`: fecha original completa, sin reemplazarla por un fin de mes sintético.
- `periodo`: derivado de la fecha para consultas/particiones.
- `afp_codigo_fuente`, `tipo_fondo_fuente`.
- `tipo_instrumento_fuente`, `nemotecnico_serie_fuente`.
- `nombre_emisor_fuente`, `nacionalidad_emisor_fuente`, `grupo_economico_fuente`.
- `unidad_reajuste_moneda_fuente`.
- `unidades_fuente`, `precio_clp_fuente`, `inversion_clp_fuente`: normalizados sólo después de verificar formato y significado por instrumento; conservar signos, ceros y ausencias.
- `plazo_economico_fuente`: duración, no vencimiento.

Conservar también en staging las **18 columnas originales**, incluyendo sus textos numéricos sin reformatear, aunque no apliquen a cada familia. `nombre_del_emisor` no debe convertirse globalmente en `contraparte`: para acciones/bonos es emisor; para ciertas posiciones de derivados es la entidad que funciona como contraparte.

### Específicos de derivados

- Forwards: `moneda_contrato_forward_fuente`, `moneda_objeto_forward_fuente`, `precio_ejercicio_forward_fuente`.
- Swaps: `tasa_fondo_fuente`, `tasa_contraparte_fuente`, preservando la cadena completa (índice, moneda, tenor, spread, base).
- Opciones/futuros: sólo campos realmente contenidos en el archivo. No completar los campos adicionales de `fi_opciones` mediante supuestos.
- Derivados opcionales documentados: dirección compra/venta, modalidad de garantías/compensación, subyacente y mercado según código; vencimiento a partir de serie sólo cuando el formato normativo vigente lo permite sin ambigüedad. Etiquetarlos como derivados del código/serie, no campos originales.

No asumir unidades USD para todos los forwards ni nocional CLP para todos los swaps. No renombrar `inversion` a nocional; tampoco a MTM neto universal sin revisar el manual actual y los controles económicos de cada familia.

### Identificación y linaje

- `archivo_fuente`, `sha256_archivo_fuente`, `numero_fila_fuente`, `version_esquema`, `version_clasificacion`, `fecha_descarga`.
- `id_registro_fuente`: identificador técnico de **hash del archivo + número de fila**. Para CSV contar registros lógicos, no líneas físicas si hay campos multilineales. No es ID económico de contrato ni permite enlazar automáticamente versiones del mismo archivo.
- Catalogar paquetes/hashes y versiones; un cambio de hash obliga a revisar revisiones, no a concatenar todos los archivos como posiciones nuevas.

La clave fecha + AFP + fondo + tipo + serie no es única: en la muestra hay 5.773 claves repetidas, normalmente con distintas condiciones. Conservar todas las filas y detectar duplicados exactos por separado sin eliminarlos automáticamente.

## 4. Dimensiones útiles

1. `afp_catalogo_administradoras_historicas`: siglas históricas, identidad y vigencia cotejadas. No imponer las siete AFP actuales a los archivos desde 1996; no asignar un RUT por parecido de nombre.
2. `afp_catalogo_tipos_instrumento`: código, descripción fuente, familia de destino, significado de medidas y fechas/versiones de vigencia. Catálogo explícito, auditable.
3. `afp_catalogo_emisores_fuente`: nombres/códigos observados; identidad legal, RUT o LEI sólo si otra fuente permite un enlace verificable.
4. `afp_catalogo_monedas_fuente`: códigos de origen y equivalencias verificadas, sin alterar NO, UF, US$ o códigos históricos silenciosamente.

Estas dimensiones pueden ayudar a cruzar bonos/acciones/fondos con otros sectores del SIF. El BDP no aporta por sí solo un maestro legal completo de emisores ni el detalle de los activos subyacentes de todos los fondos adquiridos.

## 5. Extracción masiva recomendada

### A. Descarga acotada, procesamiento local

1. Obtener documentación vigente y los tres paquetes usando el flujo normal del portal, conservando fecha, opción, nombre del archivo y SHA-256. La captura anuncia unos **428,9 MB sumando los tres paquetes**; no se conoce aún el tamaño descomprimido ni el total de filas.
2. Descargar una vez la historia, no hacer miles de consultas mensuales a los listados agregados. El mecanismo exacto del formulario/botón no se ha inspeccionado desde este entorno; no programar POST, tokens ni destinos inventados. No eludir CAPTCHA/WAF.
3. Guardar originales en `.local-data/pensiones/bdp/` o almacenamiento externo, fuera de `docs/` y Git.
4. Inventariar los miembros de cada ZIP y comprobar qué años/meses contienen; detectar solapamientos y versiones repetidas. Procesar cada CSV anual por lotes/chunks, sin cargar toda la historia en memoria. No ejecutar archivos o código incluido en paquetes; validar rutas y tamaños antes de extraerlos.

### B. Una extracción canónica, múltiples tablas

5. Crear una tabla canónica privada de staging con las 18 columnas originales + normalización + linaje. De ella se obtienen tablas temáticas mediante reglas disjuntas y versionadas.
6. Particionar físicamente por familia y año (`familia/anio=AAAA/part-....parquet`); cada tabla SQL mantiene toda la historia de su familia. AFP/fondo permanecen como columnas.
7. Retener `otros_no_clasificados` en cuarentena; producir informe de códigos y bloquear certificación de extracción completa si contiene filas. No descartarlas ni forzarlas a renta fija.
8. Mantener `afp_cartera_completa` sólo como vista UNION ALL opcional de las familias, no como una segunda fuente a sumar junto con ellas. Los compromisos y otras medidas heterogéneas conservan su naturaleza; una vista unificada no vuelve sumables todas sus filas.

### C. Validación

9. Detectar separador, codificación, encabezados y formato decimal de cada archivo/version; números con `Decimal`, no heurísticas globales de divisores. El XLSX del espejo muestra indicios de pérdida de decimales: **no es apto como fuente numérica del backfill**.
10. Verificar conservación de filas: total canónico = suma de familias + cuarentena; asignación única de familia, signos y ausencias intactos.
11. Auditar cobertura fecha × AFP × fondo × código, sin asumir presencia de A–E antes de la existencia de multifondos; las ausencias no son ceros.
12. Cotejar posiciones/celdas y agregados con SP aplicando unidades y perímetros de cada medida. No cuadrar nocionales con patrimonio ni sumar precio/compromisos/valorización como una sola medida.
13. Identificar revisiones mediante manifiesto; reingestar particiones afectadas de forma idempotente, preservando fuentes originales para auditoría. Nueva descarga del paquete reciente sólo cuando exista revisión o nueva publicación, no un backfill completo diario.

### D. Publicación separada

14. **Sólo si las condiciones vigentes permiten redistribución** y después de auditoría, compilar Parquet/JSON públicos y registrar tablas, diccionario, manifiesto y pruebas en el SIF. No reactivar los generadores sintéticos anteriores.

El manual histórico dice: «Esta base es de uso exclusivo para fines de investigación. Se solicita no distribuir esta información». Es una condición que se debe verificar en el manual vigente, y en caso necesario consultar/autorización SP; cambiar formato a Parquet no resuelve la condición. La extracción local de investigación y la publicación de la base en un sitio web son decisiones distintas.

## 6. Qué NO se obtiene directamente de este archivo

- Transacciones diarias, flujos de compras/ventas o precios efectivamente pagados, por observar cambios de stock mensual.
- ID universal de contrato, ID de pata, fecha de inicio y vencimiento independientes en todas las filas.
- RUT/LEI universal de emisor o contraparte.
- Curvas/tasas de mercado, flujos futuros de cada cupón, garantías o márgenes por contrato y pagos efectivos completos.
- Look-through de posiciones internas de los fondos mutuos/FI/vehículos adquiridos.
- Un nocional y un MTM neto comparables para todos los tipos de instrumento sin trabajo semántico adicional.
- Datos de personas afiliadas, salarios, comisiones AFP, afiliados o estados financieros completos: el portal tiene otras bases y la SP otras fuentes, pero no están contenidos en estos 18 campos de cartera.

## 7. Evidencia y estado

- Portal BDP: https://www.spensiones.cl/apps/bdp/index.php (catálogo demostrado por captura del usuario; botón no accionado desde el entorno).
- Manual y archivo 2021 en espejo GitHub: https://github.com/Sud-Austral/Descargas/tree/699e896c470420577989c350adff5546c11127fc/Carteras%20hist%C3%B3ricas%20de%20Inversi%C3%B3n%20de%20los%20Fondos%20de%20Pensiones.
- Manual SP mayo 2020, 18 campos y glosario: leído íntegramente en espejo; condiciones vigentes pendientes.
- Inventario: `scratch/bdp-research/inspection_2021.json`, `checks_2021.json`, `families_2021.json` (ignorados por Git). Los conteos describen únicamente enero–mayo de 2021 del espejo.
- Informe ampliado: [FUENTES_DERIVADOS_2026-10-07.md](FUENTES_DERIVADOS_2026-10-07.md).

**No se implementó un extractor, no se publicaron Parquet y no se certificó cobertura histórica completa.** El siguiente insumo necesario es documentación vigente y al menos un CSV original de SP; después se puede validar un piloto de lectura/clasificación y escalar a los tres paquetes.
