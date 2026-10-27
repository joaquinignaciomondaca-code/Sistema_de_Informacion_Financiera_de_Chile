# SIF: investigación sobre experiencia de uso y plan de validación

Fecha de revisión: 27 de octubre de 2026.

## Resumen ejecutivo

La bibliografía consultada respalda tratar la experiencia como un conjunto de tareas de descubrimiento, evaluación, interpretación y uso de datos, no simplemente como acceso a archivos. Para SIF recomiendo un catálogo comprensible y una ficha de conjunto como articuladores del recorrido, manteniendo acceso directo a SQL, esquema y Parquet. Esta arquitectura es una hipótesis de diseño informada, no un resultado experimental obtenido con usuarios del SIF.

No se propone implementar un rediseño en esta etapa. Primero deben definirse tareas, medir el funcionamiento actual, prototipar alternativas y observar personas reales.

## Alcance y límites

Revisión dirigida, no revisión sistemática ni metaanálisis. Se buscaron estudios sobre búsqueda de conjuntos, comprensión de datos, usabilidad de portales abiertos, filtros, diferencias de experiencia y métodos de investigación. Se consultaron artículos originales, resúmenes académicos y guías institucionales. No todos los documentos fueron leídos íntegramente; las cifras citadas proceden de sus resúmenes, métodos o resultados consultados.

La evidencia proviene mayoritariamente de otros dominios y países. No demuestra qué arquitectura funciona mejor para datos financieros chilenos. Las capturas compartidas y la lectura del código permiten detectar fricciones, pero no sustituyen sesiones con participantes. Tampoco las pruebas automáticas de interfaz validan comprensión financiera o éxito de una tarea.

## 1. Evidencia relevante

### 1.1 Buscar datos implica evaluar si sirven

**Koesten et al. (2017), The Trials and Tribulations of Working with Structured Data, CHI.** Estudio mixto con entrevistas a 20 personas que trabajan con datos y análisis de registros de búsqueda de un portal. Examina búsqueda, selección y evaluación en el contexto del trabajo. Los participantes incluyen perfiles profesionales diversos; no representa una muestra de ciudadanos sin conocimientos técnicos. [1](https://dl.acm.org/doi/pdf/10.1145/3025453.3025838)

**Aplicación propuesta:** no basta encontrar una tabla por su nombre. La ficha debe ayudar a decidir si corresponde al objetivo: contenido, cobertura, unidad de observación, fuente y acceso.

### 1.2 La comprensión alterna entre datos y contexto

**Koesten, Gregory, Groth y Simperl (2020), Talking datasets: Understanding data sensemaking behaviours.** El estudio combina entrevistas, pensamiento en voz alta y análisis de grabaciones de pantalla de 31 investigadores trabajando con datos conocidos y desconocidos. Identifica actividades de inspección, profundización en el contenido y contextualización. No establece una secuencia obligatoria de pantallas. [2](https://arxiv.org/abs/1911.09041)

**Aplicación propuesta:** conectar muestra, definiciones y procedencia alrededor del mismo conjunto. Permitir volver entre ellas conservando contexto. No exigir que el usuario lea todo el Diccionario antes de ver datos.

### 1.3 Los resultados de búsqueda deben permitir juzgar relevancia

**Wu et al. (2019), Data Discovery Paradigms, Data Science Journal.** Analiza cualitativamente 79 casos de búsqueda y deriva nueve requisitos, complementados con evaluación heurística y revisión experta. Recomienda múltiples accesos, resultados evaluables y metadatos legibles. No es un ensayo controlado que mida el efecto de cada recomendación. [3](https://datascience.codata.org/articles/10.5334/dsj-2019-003)

**Aplicación propuesta:** combinar búsqueda con exploración por temas. Mostrar contexto suficiente en resultados, no solo un identificador SQL o un botón de descarga.

### 1.4 Buen aspecto o satisfacción no garantizan resolver tareas

**Usability considerations for open data portals (2025), Universal Access in the Information Society.** Reporta 50 participantes, cinco portales y 200 tareas; 64 % de respuestas correctas. Es una advertencia contra evaluar únicamente satisfacción o impresión general. No debe trasladarse ese porcentaje a SIF ni usarse como un objetivo universal. [4](https://link.springer.com/article/10.1007/s10209-025-01227-1)

**Aplicación propuesta:** medir si las personas encuentran el conjunto correcto y entienden su alcance, no solo si les gusta la página.

### 1.5 Filtros y búsqueda pueden complementarse, pero el control concreto debe probarse

**Yee et al. (2003), Faceted Metadata for Image Search and Browsing, CHI.** Comparación intra-participantes con 32 estudiantes de historia del arte y una colección de unas 35.000 imágenes. El resumen reporta una preferencia aproximada del 90 % por la interfaz facetada. El dominio es distinto y el estudio no demuestra que dos desplegables superen a botones en SIF. [5](https://people.ischool.berkeley.edu/~hearst/papers/flamenco-chi03.pdf)

**Aplicación propuesta:** conservar búsqueda y refinamiento visible. Probar si las categorías se entienden y si ayudan a llegar al conjunto correcto. Grupo y Sector son una jerarquía dependiente, no dos facetas independientes. Una clasificación editorial interna puede no coincidir con el vocabulario de los usuarios.

### 1.6 No confundir experiencia financiera con experiencia técnica

**Kalyuga (2007), Expertise Reversal Effect and Its Implications for Learner-Tailored Instruction.** Revisión de investigación educativa sobre cómo el apoyo útil para principiantes puede resultar redundante para personas con conocimiento previo. La transferencia a un portal web es indirecta. No prueba que debamos implementar tres modos de interfaz. [6](https://www.uky.edu/~gmswan3/EDC608/Kalyuga2007_Article_ExpertiseReversalEffectAndItsI.pdf)

**Aplicación propuesta:** ayudas y ejemplos opcionales, sin bloquear atajos técnicos. Reclutar por experiencia específica en finanzas, datos y herramientas, no por una etiqueta global de experto.

### 1.7 Ocultar información no es una solución universal

**GOV.UK Design System, componente Details.** Guía práctica institucional: desplegar contenido que solo algunas personas necesitan; no ocultar lo que necesita la mayoría. No es un ensayo experimental sobre SIF. La guía advierte también dificultades de descubrimiento y algunas interacciones con tecnologías de asistencia. https://design-system.service.gov.uk/components/details/

**Aplicación propuesta:** mantener visibles muestra parcial, unidad, moneda, período, fuente y observaciones materiales para interpretar resultados. Desplegar explicaciones extensas sobre procesamiento, automatización o implementación. No cerrar ni esconder una advertencia esencial solo para limpiar la pantalla.

**Hallazgo adicional, a investigar antes de generalizar:** el resumen de Designing Effective Training Dataset Explanations (2026) informa que la revelación progresiva no redujo eficazmente carga cognitiva, aunque mejoró aprendizaje percibido. Es otro dominio, y se revisó su resumen, no su experimento completo; sirve como cautela, no como fundamento central. [7](https://dl.acm.org/doi/10.1145/3742413.3789087)

## 2. Qué mantendría y qué revisaría de la propuesta actual

### Mantener como dirección de trabajo

- Selección de conjunto compartida y visible.
- Búsqueda y navegación por categorías como accesos complementarios.
- Descripción legible junto al nombre técnico.
- Distinción clara entre muestra en pantalla y conjunto completo.
- Formatos de descarga explícitos y cobertura antes de iniciar la descarga.
- Errores de carga separados de ausencia de publicaciones.
- Acceso directo a herramientas avanzadas.

Estas decisiones son coherentes con los estudios, pero sus implementaciones concretas todavía requieren validación local.

### Revisar antes de consolidar

- **Grupo → Sector:** comprobar que las etiquetas se entienden; especialmente inversión institucional, instituciones, archivo y registros.
- **Un solo menú Descargar:** reduce repetición visual, pero puede hacer menos visibles los formatos. Comparar el menú con botones explícitos en una ficha.
- **Sincronización entre pestañas:** puede ayudar o parecer una modificación inesperada de filtros. Explicar el contexto y permitir explorar sin seguirlo.
- **Avisos cerrables:** conservar un estado breve visible; no ocultar implicaciones relevantes para cálculos.
- **Ficha común:** mantenerla compacta; no duplicar la misma descripción en cada pestaña.
- **Mapa:** ofrecerlo como recurso disponible, sin afirmar todavía que todos deban pasar por un catálogo primero.

## 3. Arquitectura candidata, pendiente de prueba

Entrada por intención: Explorar datos / Descargar / Consultar con SQL. La ayuda inicial sería opcional.

Recorrido frecuente: necesidad → búsqueda o sector → evaluar conjunto → inspeccionar y entender → usar o descargar.

No debe ser un asistente lineal obligatorio: una persona que conoce el identificador debe poder llegar directamente a SQL o al archivo.

Ficha de conjunto candidata:

1. Nombre comprensible y nombre técnico secundario.
2. Qué representa cada fila.
3. Cobertura, frecuencia, unidades y monedas cuando corresponda.
4. Fuente, fecha de actualización y disponibilidad.
5. Observaciones que cambian la interpretación.
6. Acciones: ver muestra, entender columnas, descargar, SQL, relaciones.

## 4. Referencia de investigación futura (no es el plan operativo vigente)

**Actualización 2026-10-27:** no hay participantes externos disponibles. Las fases siguientes son una referencia para una eventual investigación futura, no requisitos para avanzar ni compromisos de reclutamiento. El plan vigente es el [recorrido interno incremental](plan_recorrido_ux_2026-10-27.md).

### Fase A. Preguntas y línea base

Preguntas principales:

- ¿La persona entiende qué puede obtener del sitio?
- ¿Encuentra un conjunto adecuado sin conocer su nombre técnico?
- ¿Distingue una entidad, una cartera y una serie macroeconómica?
- ¿Entiende qué representa una fila y si puede sumar una columna?
- ¿Sabe que el Visor muestra una muestra?
- ¿Puede cambiar de pestaña y conservar orientación?
- ¿Distingue ausencia publicada de error técnico?

Congelar una versión de referencia y usar datos sintéticos o publicados estables para evitar que cambios de cobertura alteren la comparación.

### Fase B. Reclutamiento

Propuesta inicial: 12 participantes, repartidos en dos rondas de seis. Intentar incluir dos personas por perfil en cada ronda; con esa cantidad solo se buscan problemas cualitativos, no estimaciones fiables por segmento.

Para cada persona registrar por separado:

- conocimiento financiero;
- experiencia buscando datos;
- uso de Excel, SQL, Python o R;
- familiaridad con CMF/BCCh;
- experiencia previa con SIF;
- necesidades de acceso y dispositivo.

Buscar usuarios potenciales externos al desarrollo. Incluir distintos dispositivos y, de ser posible, usuarios de tecnologías de asistencia. Si aparecen diferencias importantes entre segmentos, ampliar las rondas en lugar de considerar que dos o cuatro personas representan a todo el grupo.

La orientación GOV.UK propone habitualmente 4–8 participantes por ronda cualitativa y más rondas cuando sea necesario; esto no equivale a demostrar que cinco personas encuentran un porcentaje fijo de todos los problemas. [8](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service)

### Fase C. Sesiones moderadas

Sesiones de 35–50 minutos con tareas pertinentes para cada participante. Pedir pensamiento en voz alta y evitar instrucciones que revelen qué botón usar. La guía GOV.UK recomienda tareas realistas con una meta clara, sin dar la respuesta. [9](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing)

Tareas candidatas:

1. Encontrar un conjunto adecuado para estudiar las compañías aseguradoras y explicar qué representa cada fila.
2. Conseguir la serie completa, no solo lo mostrado en pantalla, en un formato que pueda abrir en su herramienta habitual.
3. A partir de una tabla seleccionada, explicar una columna, comprobar la fuente y volver a los datos.
4. Interpretar una sección sin publicaciones: explicar qué se sabe y qué no se puede concluir.
5. Para participantes técnicos: consultar una vista y revisar una relación sin perder una consulta en edición.

Preparar respuestas esperadas verificadas contra la documentación, no improvisar criterios durante la sesión. No exigir tareas SQL a quien no usa SQL.

### Fase D. Registro de evidencia

Por tarea registrar:

- éxito sin ayuda / éxito con ayuda / no completada;
- exactitud de la explicación del dato;
- errores críticos, como confundir muestra con total o moneda/unidad;
- primer destino elegido;
- búsquedas reformuladas y pérdida de contexto;
- tiempo como indicador diagnóstico, no único objetivo;
- dificultad percibida y confianza en la respuesta;
- comentario textual y momento concreto del problema.

Registrar también la carga real del motor por separado: no confundir espera de red con problemas de navegación. Una persona más rápida pero equivocada no representa una mejora.

### Fase E. Prototipos y segunda ronda

Comparar la experiencia actual con un prototipo compacto centrado en conjunto y tarea. Evitar cambiar simultáneamente taxonomía, colores, navegación y contenido. Si se reutilizan participantes, controlar aprendizaje; para comparaciones dentro de una sesión alternar orden y usar tareas equivalentes.

Priorizar por impacto: interpretación financiera errónea o descarga equivocada > bloqueo de tarea > pérdida de contexto > lentitud o confusión recuperable > detalle visual.

Definir objetivos después de observar la línea base. Con una muestra cualitativa pequeña no declarar superioridad estadística ni porcentajes de éxito de toda la población. No iniciar A/B sin estimar tráfico, diferencia de interés y tamaño muestral.

### Fase F. Capturas y grabaciones

Con consentimiento, capturar pantalla durante tareas y guardar versión de interfaz, tamaño de ventana, acción previa, resultado esperado y resultado observado. No registrar credenciales ni archivos privados. Las imágenes solas no explican intención ni comprensión; deben vincularse con observaciones de tarea.

Mapa de experiencia: etapas, objetivo, pregunta, información necesaria, acción, fricción y evidencia. Consolidar o separar recorridos según diferencias observadas, no solo según perfiles inventados. [10](https://www.gov.uk/service-manual/user-research/creating-an-experience-map)

## 5. Entregables previos al rediseño

1. Matriz de tareas, hipótesis y criterios de éxito.
2. Mapa del recorrido actual con evidencia.
3. Inventario de información: esencial, contextual o técnica.
4. Prototipo de una ficha de conjunto y una entrada de catálogo.
5. Registro priorizado de hallazgos de las rondas.
6. Decisiones justificadas: mantener, modificar o descartar.

## Conclusión

La evidencia favorece facilitar descubrimiento, evaluación, comprensión y uso, con contexto legible y acceso flexible. No prescribe una apariencia única ni valida automáticamente nuestros cambios. El siguiente paso es validar unas pocas tareas completas con usuarios potenciales antes de reestructurar globalmente SIF.
