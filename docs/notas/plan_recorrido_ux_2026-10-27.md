# Recorrido de datos: plan operativo y primera revisión interna

Fecha: 2026-10-27. Estado: entregas 1 y 2 implementadas; entrega 3 avanzada, cierre pendiente.

## Estado actual resumido

Este bloque es el estado vigente. Las secciones posteriores conservan la evidencia histórica de cada entrega y pueden mencionar pendientes que ya se atendieron después.

| Entrega | Implementación | Qué falta para cerrar |
|---|---|---|
| 1 · Diagnóstico y reglas | Completada; defectos e hipótesis separados, reglas de selección/filtros/borrador documentadas | Sin implementación pendiente de esta entrega |
| 2 · Entrada y contexto | Implementada: explorar sector, contexto con metadatos existentes, columnas y acceso separado al Mapa | Feedback sobre claridad de una tarea completa; no se afirma validación por visitantes nuevos |
| 3 · Consolidación | Avanzada: selección no interruptiva, protección SQL, exportaciones/partes, rangos, carga recuperable, foco y regresiones | Revisión final visual y de tareas; descarga real fuera de vista previa pendiente; discrepancia heredada de métricas abierta |

No se asigna porcentaje de esfuerzo restante: las tres entregas no tienen igual tamaño y el cierre depende de la evidencia, no del número de commits. No quedan aprobadas ampliación de fichas, analítica ni una nueva política de URLs.

### Tareas y evidencia vigente

| Tarea | Cubierto | Pendiente / límite |
|---|---|---|
| T1 · Encontrar conjunto | Entrada por sector y acceso a contexto/columnas probados en DOM; responsable llegó a lista de fondos mutuos | Feedback sobre elección y claridad, sin interpretar ese intento como prueba de visitante nuevo |
| T2a · Excel pequeño | Generación/reapertura automática de XLSX sintético; alcance y carga probados | Responsable no recibió archivo en vista previa; aceptado provisionalmente, causa y descarga real no confirmadas |
| T2b · Gran volumen | CSV 250.001 y XLSX 150.001 en partes ZIP, todos los IDs y totales comprobados automáticamente | Prueba XLSX no supera el límite de una hoja: verifica la partición preventiva. Falta ejercicio real de gran volumen en navegador/Excel; no se afirma probado todo el catálogo |
| T3 · Contexto y continuidad | Metadatos compartidos, columnas exactas, selección entre pestañas, regreso sin sobrescribir filtros | Revisión de utilidad/explicación financiera por responsable |
| T4 · Ausencia y repeticiones | Anuncio sin datos cerrable y observación de fidelidad a fuente implementados | Feedback de comprensión; no inferir ausencia de reporte ni cero |
| T5 · Borrador SQL | Protección de acciones programáticas, cancelar/aceptar, sugerencias/favoritas y navegación DOM | No es prueba visual ni de todos los navegadores |
| T6 · Filtros y regreso | Recorrido DOM Descargas → Diccionario → SQL → Descargas → Diccionario conserva búsqueda, sector, grupo, años, resultados y borrador | La búsqueda manual del Diccionario abandona la ficha exacta local, pero conserva contexto global: comportamiento intencional |

Última batería DOM: **172/173**, único fallo de métricas heredadas; móvil **15/15**. La discrepancia de métricas requiere conciliación separada, no regeneración ciega de datos. PR #86 permanece abierto como borrador; no se declara CI completamente verde.

## Acuerdo de trabajo

No hay participantes externos disponibles. El responsable del producto dará feedback sobre tareas completas. Las perspectivas sin experiencia/intermedia/experta son criterios de inspección, no usuarios entrevistados. La revisión interna puede detectar problemas funcionales, semánticos y de utilidad; no representa la experiencia de un visitante nuevo.

La [investigación bibliográfica](investigacion_ux_2026-10-27.md) es referencia, no una secuencia obligatoria de fases. No se requiere reclutar participantes ni instalar analítica para avanzar. No se crean tres modos por nivel ni un rediseño global en esta entrega.

## Tres entregas

1. **Diagnóstico y reglas.** Revisar entradas/fichas existentes, ejecutar comprobaciones internas, separar fallos de hipótesis y definir continuidad. Es esta entrega.
2. **Entrada y ficha, juntas.** Proponer un recorrido pequeño para encontrar un conjunto y decidir si sirve; reutilizar contrato y renderers existentes. Revisar con el responsable antes de extenderlo.
3. **Consolidación.** Continuidad completa, grandes descargas, estados, móvil, teclado y regresiones. Los defectos críticos encontrados antes se corrigen sin esperar a esta entrega.

Ciclo: evidencia disponible → propuesta acotada → implementación → tarea del responsable sin instrucciones de navegación → feedback → ajuste. Los resultados se registran por versión. No se presentan como validación de usabilidad poblacional.

## Inventario comprobado de fichas y entradas

| Pieza | Estado real | Fuente / integración |
|---|---|---|
| `/datos/ccaf_lista_entidades/` | Única ficha estática piloto encontrada; HTML sin JS, `noindex,follow`, sin canonical | `build_ficha_piloto.py` deriva de catálogo API v2, Data Package, manifiesto ETL, esquema y particiones; valida archivo/hash |
| Ocho fichas candidatas | Previsualizaciones en memoria, no ocho rutas publicadas | `ficha_renderer.py` y `test_fichas_candidatas.py`; CCAF conserva renderer especializado por procedencia |
| Ficha → aplicación | Enlace de regreso y consulta compartible `#sql=…` | No equivale a una URL general de conjunto seleccionable en cualquier pestaña |
| Portada → sector | `portada.js`, `accion`: Explorar abre Mapa y enfoca sector | Comportamiento actual, no se cambió en esta entrega |
| Aplicación → conjunto | Contexto compartido en memoria | No hay todavía un contrato general de URL por tabla/pestaña en este módulo |
| Contrato publicado | Catálogo, esquemas, particiones, Data Package | Mantener IDs y procedencia; no inventar metadatos de unidad ausentes |

**Decisión de diseño:** no construir una segunda ficha editorial independiente. La siguiente propuesta reutilizará identidad y metadatos del contrato; conservará CCAF y su procedencia especial. No generar todas las rutas, cambiar canonical/sitemap ni prometer indexación como efecto lateral. La ficha piloto no se presenta como una política definitiva de URLs aprobada.

No se modificó la checklist anterior del rediseño ni se cerraron sus decisiones pendientes por esta inspección.

## Reglas de continuidad

| Acción | Regla |
|---|---|
| Seleccionar otra tabla | Actualiza referencia visible; cada pestaña sigue la selección nueva una vez |
| Navegar sin nueva selección | No reaplica filtros ni búsqueda sobre cambios manuales |
| Selección implícita y SQL con texto | No cambia borrador ni pide confirmación |
| Acción `setQueryInput` explícita y SQL diferente | Pide confirmación antes de reemplazar; cancelar conserva texto |
| Misma consulta o editor vacío | No pide confirmación innecesaria |
| Quitar selección | Quita contexto global y selección exacta del Diccionario; limpia búsqueda de Descargas solo si coincide con el ID seleccionado, no una búsqueda manual independiente |
| Seleccionar desde la izquierda | Abre Visor, conforme al acuerdo previo |

Alcance del resguardo SQL: llamadas a `setQueryInput` (incluye abrir SQL desde Descargas). Chips, favoritos y otras escrituras directas del editor aún deben inventariarse antes de afirmar protección universal.

## Recorrido interno, no prueba de comprensión

| ID / grupo | Tarea | Comprobación y estado |
|---|---|---|
| T1 · descubrimiento | Encontrar datos que identifiquen aseguradoras | Inspección confirma entrada por sector y filtro; falta feedback sin instrucciones sobre qué tabla elegir |
| T2a · uso | Descargar conjunto pequeño completo para Excel | Usar conjunto que quepa en hoja; pendiente descargar y abrir archivo real |
| T2b · volumen | Obtener conjunto mayor que el límite de una hoja | Verificar conjunto total, partes/ZIP o alternativa; pendiente. Completo no significa que quepa en una hoja |
| T3 · comprensión/continuidad | Consultar definición y fuente, regresar al mismo conjunto | Contexto y Diccionario exacto cubiertos por prueba hermética; explicación financiera pendiente del responsable |
| T4 · interpretación | Explicar ausencia publicada y repeticiones | Avisos implementados; no implica ausencia de reporte ni importes cero. Falta feedback sobre comprensión |
| T5 · regresión | Conservar borrador y controlar reemplazo explícito | `test_sql_draft.js`: preservación, cancelación, confirmación, mismo SQL y editor vacío pasan |
| T6 · regresión | Cambiar filtros manuales y volver | `test_table_context.js`: no reaplica revisión ya seguida; DOM comprueba selección en Descargas. Comportamiento completo requiere ampliar cobertura |

No confundir éxito de la consulta con interpretación correcta; no confundir inicio de descarga con archivo completo ni tamaño legible con cobertura íntegra.

## Resultado técnico de esta entrega

- Se instaló jsdom solo en `/tmp`, sin dependencia nueva del proyecto.
- `audit_movil_dom.js`: 15/15.
- `audit_interfaz_dom.js`: 157/158. Se actualizaron comprobaciones de controles retirados y textos equivalentes; se añadió aserción de selección en Descargas. Se conserva el fallo de conciliación de métricas, no se oculta.
- `test_table_context.js` y `test_sql_draft.js`: pasan.
- `build_ficha_piloto.py --check` y `test_ficha_piloto_http.py`: pasan. HTTP local bajo raíz y prefijo Pages simulados, seis enlaces internos 200 en cada caso; no prueba hosting público.
- `build_metricas_publicadas.py --check`: falla por diferencias entre API, catálogo de descargas y README. El alcance principal tiene 19.677.277 filas/485.772.410 bytes en Descargas frente a 19.677.266/485.772.322 en métricas. El guardián también informa diferencias de objetos macro y fintech.
- Catálogo de descargas y métricas son idénticos a los del commit base de esta rama (`git diff 50e9a74… -- docs/js/download_catalog.js docs/metricas_publicadas.json` vacío). No se regeneraron ni corrigieron cifras sin reconciliar responsables/constructores. Es un problema heredado que impide declarar la batería completamente verde.
- Capturas Chromium siguen bloqueadas por `libnspr4.so`; jsdom no mide disposición real ni lectura financiera.

## Qué cambia y qué no

En esta entrega se protege el reemplazo SQL mediante `setQueryInput`, se tolera ausencia de `scrollIntoView` en entornos sin layout y se actualizan pruebas/documentación. No se cambia aún la portada, el destino de Explorar, las fichas, los datos, los metadatos de contrato ni la política de URLs.

## Siguiente decisión revisable

Preparar entrada por intención y ficha de conjunto como una sola propuesta, aprovechando el renderer y la ficha piloto. Comparar catálogo y Mapa según tarea; no dar por ganador al catálogo. Mantener acceso directo avanzado y observaciones que afecten interpretación. Analítica queda como evaluación separada de privacidad/beneficio, sin instalar servicios ni registrar consultas.


## Segunda entrega: entrada y contexto de conjunto (versión revisable)

### Cambios

- `Explorar` desde cualquiera de los siete sectores de portada abre el catálogo existente en Descargas con ese sector, sin búsqueda residual de la selección anterior ni recorte de años arrastrado. No se crea una octava pestaña ni un catálogo paralelo.
- `Entender relaciones entre tablas` y `Ver relaciones` ofrecen entrada explícita al Mapa. No se elimina el diagrama ni se afirma superioridad empírica del catálogo.
- Cada tarjeta destaca `detalle` del catálogo y conserva el nombre técnico. La descripción, fuente, filas y cobertura siguen visibles.
- El apartado `Entender este conjunto antes de usarlo` reutiliza cobertura/fuente del catálogo de Descargas y frecuencia/fecha del Diccionario cuando existen. No deduce unidad de observación a partir de frecuencias o conteos ni inventa moneda/unidad ausente.
- `Entender las columnas` selecciona el conjunto y abre su Diccionario exacto. Una acción explícita puede volver a seguir la misma selección; navegar entre pestañas por sí solo no reaplica búsquedas ya atendidas.
- Solo CCAF enlaza a su ficha piloto con URL propia, identificada como piloto. No se generan rutas para las ocho previsualizaciones ni se modifica canonical, sitemap o indexación.

### Prueba interna para el responsable

1. Desde Información, buscar conjuntos de fondos mutuos con Explorar.
2. Abrir el contexto de un conjunto y comprobar si basta para decidir si sirve.
3. Consultar sus columnas y volver al catálogo o al Visor.
4. Usar Ver relaciones por separado y evaluar si los dos destinos resultan claros.
5. Repetir tras tener otra tabla seleccionada: el acceso explícito a explorar sector debe mostrar ese sector, no resultados vacíos por la tabla anterior.

Feedback pendiente: nombres de acciones, utilidad del contexto, densidad visual y conveniencia de conservar Descargas como nombre del catálogo. No se ha probado con usuarios externos.

### Verificaciones de la segunda entrega

- DOM general 161/162: se añaden regresiones de catálogo por sector sin búsqueda residual, acción Mapa, enlace único a ficha piloto y salto a Diccionario exacto.
- Se conserva el único fallo de conciliación de métricas heredado descrito anteriormente.
- `test_table_context.js` amplía cobertura de seguir de nuevo la selección por acción explícita.
- Auditorías estáticas de interfaz/móvil y regresiones SQL pasan. Revisión visual real y archivos descargados siguen pendientes.


## Consolidación iniciada: selección ligera en el Mapa

Feedback del responsable: el esquema automático al pulsar una caja cubre demasiadas relaciones y presenta nombres de columnas recortados (captura compartida). Esto es evidencia de un problema concreto de presentación, no una medición con usuarios nuevos.

- Un clic en nodo solo selecciona; no abre diálogo, no mueve foco al terminal y no inicia consulta del Visor/DuckDB. El contexto se aplica al abrir las pestañas correspondientes.
- `Ver esquema seleccionado` es acción explícita; permanece deshabilitada sin selección válida. La tabla seleccionada conserva borde destacado aunque el puntero salga.
- El detalle solicitado tiene nombres largos ajustados a líneas, lista desplazable interna y acciones/cierre fuera del área desplazable. Se retira la animación y se usa un borde neutro; Escape y devolución de foco permanecen.
- El esquema se cierra al abandonar Mapa. No se cambian los datos ni se ocultan campos.
- Al abrir Visor con contexto no se inicializa primero una tabla anterior: la selección del mapa se carga bajo demanda, incluso si coincide con la vista predeterminada aún no consultada. Regresión hermética añadida.
- Quitar selección ya no borra una búsqueda manual diferente en Descargas; limpia únicamente la búsqueda que coincide con el contexto anterior. Regresión hermética añadida.

Verificación: DOM general 164/165 (mismo fallo heredado de métricas); DOM móvil 15/15; contexto, borrador SQL y auditorías estáticas pasan. El DOM verifica clic sin diálogo/cambio de foco/muestra y apertura explícita, no el encuadre visual real. Pendientes de consolidación: comprobar archivos completos/partes, revisar todas las escrituras directas SQL, capturas y feedback visual.


## Consolidación: SQL y archivos completos

- `replaceQuery` centraliza la confirmación de reemplazo. Sugerencias iniciales, sugerencias dinámicas, favoritas y acciones `setQueryInput` la utilizan; cancelar no ejecuta ni cierra favoritas. El contexto implícito conserva el borrador sin preguntar.
- El SQL inicial recibido por hash pasa por esa protección. Su ejecución diferida solo ocurre si el texto no cambió durante la espera.
- Edición manual, autocompletado y navegación del historial permanecen como operaciones explícitas del editor, no navegación entre tablas. No se afirma que todo reemplazo de texto tenga confirmación.
- `test_sql_draft_dom.js` comprueba los disparadores reales de chips iniciales/dinámicos y favoritas, con aceptación y cancelación; pasa localmente en jsdom.
- `test_download_exports.js` utiliza filas sintéticas y las bibliotecas SheetJS/JSZip incluidas en docs, sin red ni modificación de datos publicados. Captura los blobs descargados y vuelve a abrir los archivos.
- CSV pequeño: BOM UTF-8, separador, comillas, texto acentuado, cero y nulo. Excel pequeño: cabeceras, texto y cero.
- CSV grande: 250.001 filas → ZIP de dos partes; se verifican cabeceras, cada ID en orden y total íntegro.
- Excel grande: 150.001 filas → ZIP de dos partes; se reabren los libros y verifican cada ID, total y límite por hoja (incluyendo cabecera).
- Entrada vacía: error explícito y ninguna descarga.
- Son archivos reales generados/reabiertos automáticamente, no apertura manual en Excel, descarga de una tabla financiera completa ni prueba del navegador contra DuckDB. Esos límites continúan pendientes.
- Se incorporan exportaciones y SQL al workflow. DOM general sigue en 164/165 con la discrepancia de métricas heredada; móvil DOM 15/15. No se declara CI remota aprobada.


### Consolidación: alcance verificable de Descargas

- Cada tarjeta distingue el alcance CSV/Excel (serie completa o años elegidos, diaria o cierre mensual por indicador, no suma mensual) del Parquet original, que no aplica esos controles. Las tablas sin período indican que no admiten recorte por años.
- Rango invertido: aviso visible accesible, controles marcados y exportaciones temporales bloqueadas antes de arrancar el motor. Parquet sigue disponible.
- La descarga captura años y frecuencia al hacer clic, incluso si cambian durante la preparación del motor. El archivo exportado incorpora los años cuando corresponde.
- Evidencia automatizada: `test_download_scope.js` verifica SQL, aviso/bloqueo, tablas sin período y cambio de controles durante arranque simulado; añadido al workflow. DOM **167/168**, con los tres nuevos contratos de controles aprobados y la misma discrepancia heredada de métricas como único fallo. Exportaciones reales sintéticas CSV/XLSX y ZIP por partes siguen aprobadas; auditoría estática de interfaz aprobada.
- Límite: no constituye revisión visual en navegador ni validación de comprensión por usuarios. La prueba de captura usa motor simulado; no se atribuye ejecución DuckDB real.


### Consolidación: preparación recuperable

- Responsable probó Excel de la lista de fondos mutuos: vio aviso, pero no recibió archivo. Acepta provisionalmente continuar; **no se confirma descarga real ni se atribuye causa al entorno**. Pendiente comprobar fuera de vista previa.
- Hallazgo de código distinto: el bloqueo de operación empezaba después del arranque del motor y de preparar las columnas mensuales. Un fallo de arranque podía escapar del manejo de errores del panel y permitir solicitudes simultáneas.
- La operación protegida abarca ahora preparación, motor, consulta y generación. El botón muestra Preparando y `aria-busy`; las solicitudes simultáneas reciben explicación sin duplicar operación. La limpieza ocurre también ante error y permite reintentar; al terminar se reaplican restricciones actuales del rango/vista, sin deshabilitar Parquet.
- Prueba hermética ampliada: arranque pendiente, segunda solicitud bloqueada, rechazo simulado capturado, restauración de etiqueta/estado accesible y reintento exitoso. Pasa; no simula permisos de descarga del navegador.
- Verificación: alcance/carga y exportaciones sintéticas reales aprobados; DOM general 167/168 (único fallo: métricas heredadas); móvil DOM 15/15. Sin nueva validación visual ni CI remota afirmada.


### Consolidación: foco al navegar y quitar contexto

- Hallazgo de código: cerrar el esquema por cambio de pestaña restauraba el foco al disparador del Mapa, ya oculto. Quitar selección desde su botón también ocultaba el propio elemento enfocado.
- Cierre por navegación no restaura foco al origen; si el foco estaba en contenido que se abandona, se dirige a la pestaña de destino. Cierre explícito o Escape siguen restaurando el disparador. La acción Explorar datos usa ese mismo cierre por navegación.
- Quitar selección desde la barra dirige el foco a la pestaña activa; si se limpia programáticamente desde otro sitio no mueve el foco por ese motivo. No se modifica el borrador SQL.
- DOM **169/170**: dos regresiones nuevas aprobadas, navegación desde esquema conserva identidad seleccionada y quitar contexto conserva borrador. La prueba del botón Quitar verifica su enlace onclick y llama al método porque jsdom outside-only no ejecuta manejadores inline. Único fallo general: métricas heredadas.
- También aprobados: móvil DOM 15/15, contexto hermético, SQL DOM, alcance/carga de descargas y auditoría estática de interfaz. Sin afirmación de revisión visual, lector de pantalla real ni CI remota.


### Consolidación: recorrido de regresión completo T5/T6

Se añaden tres comprobaciones al DOM real de la aplicación: se sigue una selección, se introducen filtros manuales de grupo/sector/búsqueda/años en Descargas, se busca otra información en Diccionario y se navega por SQL antes de volver. Se verifican resultados visibles no vacíos e idénticos, controles conservados, borrador intacto y búsqueda manual del Diccionario no sustituida por la ficha seleccionada. Las tres pasan. No se modificó comportamiento de producto en esta iteración; se amplió evidencia y se separó estado vigente de la cronología del plan.
