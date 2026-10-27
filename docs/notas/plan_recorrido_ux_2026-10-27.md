# Recorrido de datos: diagnóstico inicial y plan incremental

Fecha: 2026-10-27. Estado: planificación iniciada; sin rediseño adicional aprobado.

## Método acordado

El responsable del producto dará feedback sobre tareas completas. No hay participantes externos disponibles. Las perspectivas sin experiencia/intermedia/experta son criterios de revisión, no personas entrevistadas. Las comprobaciones automáticas prueban comportamiento técnico, no comprensión o usabilidad poblacional.

Base bibliográfica y límites: [investigación UX](investigacion_ux_2026-10-27.md).

## Avance que se preserva en este PR

- Seleccionar una tabla del explorador abre el Visor.
- Columnas ajustables, descarga directa y formatos disponibles desde el Visor.
- Filtros Grupo/Sector en Mapa, Diccionario y Descargas.
- Contexto compartido entre pestañas, con protección del borrador SQL.
- Diferenciación de ausencia publicada, errores técnicos y observaciones sobre la fuente.
- Ayudas desplegables y cabecera de Descargas compacta.

Son implementaciones pendientes de revisión integral en navegador; no constituyen evidencia de mejora frente a usuarios nuevos.

## Diagnóstico del recorrido actual (inspección de código)

| Objetivo | Entrada y comportamiento observado | Fricción o hipótesis | Próxima propuesta |
|---|---|---|---|
| Explorar sin nombre técnico | `portada.js`, `accion`: Explorar sector abre Mapa | El diagrama puede ser una primera pantalla demasiado técnica; pendiente de feedback | Prototipar catálogo filtrado como destino alternativo |
| Encontrar una tabla conocida | Explorador, buscadores de Diccionario y Descargas | Hay varias entradas; falta comprobar vocabulario y consistencia | Mantener accesos directos y probar nombres comprensibles |
| Decidir si sirve | Visor muestra muestra; Diccionario reúne definiciones; Descargas presenta cobertura y archivos | La evaluación requiere alternar vistas | Bocetar ficha compacta de conjunto, sin duplicar metadatos |
| Entender una columna | Selección compartida abre ficha exacta del Diccionario | Comprobar si la restricción por tabla resulta clara y puede abandonarse | Probar navegación a definición y regreso |
| Descargar datos | Descargas permite formatos, archivos, años y frecuencia | El recorte y la frecuencia no tienen el mismo efecto en Parquet y exportaciones | Revisar claridad de alcance antes de descargar |
| Analizar con SQL | Terminal conserva borrador ante selección implícita | Acciones SQL explícitas pueden reemplazar consulta; comprobar expectativa | Distinguir contexto de tabla y acción explícita de abrir consulta |
| Interpretar ausencia o repetición | Aviso cerrable de ausencia; nota sobre repeticiones de la fuente | Confirmar que no se interpreta ausencia como cero ni duplicación como fallo del sistema | Mantener estado breve visible y acceso a explicación |

## Bloques y compuertas de revisión

1. **A: entrada y descubrimiento.** Proponer destino de Explorar y jerarquía de portada. No cambiar aún todas las pestañas.
2. **B: ficha de conjunto.** Reunir significado de fila, cobertura, fuente, unidades/monedas y acciones, solo cuando esos metadatos existan. No inferir datos faltantes.
3. **C: continuidad.** Selección, filtros manuales, botón Quitar selección, retorno y consultas en edición.
4. **D: acceso avanzado.** SQL, esquema, relaciones y archivos sin recorrido introductorio obligatorio.
5. **E: consistencia.** Escritorio/móvil, teclado, foco, menús, avisos, carga y errores.

Cada bloque: propuesta breve → implementación acotada → pruebas técnicas → tarea sin instrucciones de navegación → feedback → decisión registrada. No se inicia un rediseño global como efecto lateral.

## Tareas para feedback del responsable

| ID | Tarea (sin indicar controles) | Criterio de término |
|---|---|---|
| T1 | Encontrar un conjunto de seguros adecuado para identificar compañías | Explicar qué representa una fila y de dónde procede |
| T2 | Obtener todos sus registros en un formato utilizable en Excel | Archivo completo; no confundir muestra con total |
| T3 | Explicar una columna, revisar fuente y volver a la tabla | Misma tabla; sin rehacer búsqueda |
| T4 | Abrir una tabla sin publicaciones y explicar el estado | No concluir ausencia de reporte a la fuente ni importes cero |
| T5 | Escribir un borrador SQL, seleccionar otra tabla y volver | Borrador conservado en navegación implícita |
| T6 | Cambiar un filtro manual después de seguir la selección y regresar | No se reaplica selección inesperadamente |

Por tarea registrar versión, dispositivo, resultado, duda, expectativa y observación. Usar capturas con acción previa y resultado esperado; no presentar screenshots como prueba suficiente de comprensión.

## Registro de decisiones

| Decisión | Estado | Evidencia |
|---|---|---|
| Mejorar incrementalmente con feedback del responsable | Acordada | Conversación del 2026-10-27 |
| No introducir tres modos por nivel | Propuesta, no validada | Revisión bibliográfica; faltan pruebas locales |
| Preservar avances en PR de la rama actual | Solicitada | Conversación del 2026-10-27 |
| Cambiar Explorar para abrir catálogo en lugar de Mapa | Hipótesis pendiente | Inspección de `portada.js`; aún no implementada |
| Ficha compacta como centro del recorrido | Hipótesis pendiente | Literatura de descubrimiento/comprensión de datos |

## Limitaciones conocidas

- Capturas automáticas intentadas, sin éxito: Chromium no arranca por biblioteca `libnspr4.so` ausente.
- Pruebas DOM opcionales requieren jsdom; no confundir omisión con aprobación.
- No se han ejecutado tareas con usuarios externos.
- El contexto y los nuevos controles requieren revisar su convivencia con las auditorías DOM anteriores y las comprobaciones de CI.
