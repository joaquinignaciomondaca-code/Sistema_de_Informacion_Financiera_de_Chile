# Recorrido de datos: plan operativo y primera revisión interna

Fecha: 2026-10-27. Estado: segunda entrega implementada como versión revisable; feedback visual pendiente.

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
| Quitar selección | Quita contexto global y selección exacta del Diccionario; comportamiento de búsqueda manual en Descargas requiere revisión adicional |
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
