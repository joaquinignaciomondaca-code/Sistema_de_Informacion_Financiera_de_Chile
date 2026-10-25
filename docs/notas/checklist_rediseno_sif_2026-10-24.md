# Checklist vivo del rediseño del SIF Chile

**Estado:** preparación y decisiones de alcance; no es autorización para rediseñar de una vez toda la web.  
**Actualizado:** 2026-10-24.  
**Documento de referencia:** propuesta de rediseño SIF Chile, versión 3.0, compartida en esta conversación.

## Cómo mantener esta checklist

- Antes de cada tarea de rediseño, revisar esta checklist y el estado real del repositorio; no asumir que lo propuesto ya está implementado.
- Añadir subpuntos cuando una tarea revele decisiones, dependencias o pruebas nuevas. Mantenerlos aquí, en vez de abrir listas paralelas que se contradigan.
- Marcar `[x]` solo cuando exista evidencia verificable (código, documentación, prueba o decisión explícita). Una propuesta, una inspección parcial o una tarea “casi lista” sigue como `[ ]`.
- Después de cada cambio, actualizar estado, pruebas realizadas, problemas pendientes y siguiente paso. No cerrar un bloque por haber terminado el código si su criterio de salida no está probado.
- Mantener las decisiones controvertidas como pendientes hasta acordarlas; no resolverlas silenciosamente mediante cambios de interfaz.

## Principio permanente: mentalidad premium y experiencia de usuario

Aplicar estos criterios a **cada** decisión de producto, diseño, código y documentación; no son una fase estética al final:

- [ ] La experiencia ayuda primero a una persona que llega con una pregunta, no conociendo el esquema interno del repositorio.
- [ ] En cada pantalla se entiende qué es, qué se puede hacer, cuál es la acción principal y qué ocurrirá al elegirla.
- [ ] Cada elemento visual tiene un propósito; no añadir tarjetas, gráficos, animaciones o métricas solo para que la interfaz parezca más completa.
- [ ] Priorizar claridad, consistencia y jerarquía editorial; lenguaje directo en español, etiquetas comprensibles y términos técnicos explicados cuando hacen falta.
- [ ] Cuidar el detalle de producto: alineación, espaciado, tipografía, estados, microcopy, enlaces, foco, vacíos y errores. Evitar soluciones “suficientemente parecidas” entre vistas equivalentes.
- [ ] Mantener una identidad sobria, propia e independiente; no imitar marcas de organismos fuente ni sugerir respaldo institucional.
- [ ] Diseñar con accesibilidad desde el inicio: teclado, foco visible, contraste, etiquetas, anuncios de estado y no depender solo del color.
- [ ] Probar móvil con tareas reales; no limitarse a que la página quepa en una captura.
- [ ] La velocidad y la estabilidad son parte de la calidad premium: carga progresiva, no descargar/ejecutar lo que no se necesita y errores que ofrecen una salida útil.
- [ ] No sacrificar precisión, confianza o trazabilidad por una portada más atractiva. No inventar períodos, frecuencias, unidades, filas, estados ni cobertura.
- [ ] Antes de aceptar una interfaz, completar el recorrido como usuario: encontrar → comprender → decidir si sirve → abrir/descargar/consultar → volver o compartir.

## Estado inicial comprobado

- [x] Revisada la propuesta v3 y anotados los principales riesgos: tratamiento visible de problemas materiales, fuente de verdad, rutas en ambos hostings y resguardos técnicos.
- [x] Confirmado en `docs/index.html` que la sección **«Cómo sumar sin sobreestimar»** y sus cifras/enlace siguen presentes. Ubicación revisada: área de guía de uso (aprox. líneas 549 y 697–699 al 2026-10-24). No se ha retirado.
- [x] El sitio es estático y las consultas SQL se ejecutan en el navegador; no se debe describir una API de archivos como endpoint SQL compartido.
- [x] Resguardos de tráfico existentes que se deben preservar: inicialización perezosa de DuckDB, cola serial por conexión, preparación remota acotada a cuatro operaciones por pestaña, deduplicación de solicitudes concurrentes y auditoría de tamaño publicada.
- [x] `no-store` y el sufijo anti-caché de Parquet son resguardos deliberados para lecturas HTTP Range; no cambiarlos sin prueba reproducible en los navegadores afectados.

## Fase 0 — auditoría y decisiones de viabilidad

### Estado real y experiencia actual
- [ ] Recorrer el sitio desplegado como usuario, sin asumir que observaciones anteriores siguen vigentes.
- [x] Registrar las rutas y pantallas que existen hoy (inventario estático de código; falta validar la experiencia publicada en navegador).
  - [x] `docs/index.html` concentra la aplicación principal en una sola página: Información, Mapa, Diccionario, Visor, Consultas SQL, Descargas y Guía; no hay páginas HTML individuales por conjunto.
  - [x] `docs/privacidad.html` es la otra página HTML independiente encontrada.
  - [x] La selección de tablas ocurre en el árbol lateral; la búsqueda y el cambio de pestañas son controles de la aplicación, no rutas nuevas.
  - [x] El enlace profundo implementado es `#sql=<consulta codificada>`; no se encontró ruta `/datos/<id>/` ni parámetro de ficha `?tabla=<id>`.
  - [x] En el repositorio, canonical/OG apuntan a GitHub Pages y `vercel.json` redirige `/api/*` hacia GitHub Pages. La API de GitHub reporta Pages `built` en modalidad `legacy`; falta comprobar en navegador qué URL recibe al usuario y el despliegue activo de Vercel.
- [ ] Probar navegación, búsqueda, acceso directo, recarga, descarga y SQL en navegadores disponibles; separar defectos reproducidos de hipótesis.
- [ ] Auditar el buscador actual: el inventario estático está hecho; falta evaluar relevancia y experiencia en navegador real.
  - [x] El filtro del árbol busca nombre de tabla, familia/subsector y rótulos visibles; aplica coincidencia literal tras pasar a minúsculas, no búsqueda por columnas.
  - [x] Hay un segundo buscador por pregunta/concepto; el índice mezcla términos curados, nombre/vista, descripción, nombres y significado de columnas. La selección reutiliza el filtro del árbol.
  - [x] La búsqueda por pregunta normaliza mayúsculas y tildes, puntúa términos (frase curada > coincidencia de concepto/nombre/descripción > columnas), limita a ocho resultados y comunica el motivo cuando lo encuentra.
  - [x] No hay tolerancia difusa a errores de tipeo: términos con errata pueden quedar sin resultados. El índice actual trae 90 entradas, se generó el 2026-10-22 y pesa 292.436 bytes sin compresión.
  - [x] Corrida exploratoria local contra el índice vigente: consultas «uf», «inflación», «dólar», «TPM», «desempleo», «bonos», «cobre», «factoring», «bancos balance», «derivados», «Ley fintec» y «tipo de cambio» devolvieron resultados; «inflación» e «inflacion» dieron el mismo orden y una consulta aleatoria/una errata («inflasión») no devolvieron resultados. Esto comprueba ejecución, no certifica por sí solo relevancia.
  - [ ] Comparar cada consulta de una batería de 15–20 con el objeto esperado y registrar falsos positivos/negativos; revisar especialmente ambigüedades y términos no cubiertos.
  - [ ] Medir peso transferido/comprimido, latencia en navegador y comportamiento cuando falla la carga del índice.
  - [ ] Probar el filtro y los resultados en móvil, teclado y tecnologías de asistencia; la inspección CSS no sustituye la prueba de uso.
- [ ] Registrar qué tareas ya se resuelven bien y no deben duplicarse ni degradarse.

### Rutas, hosting y fuente de verdad
- [ ] Identificar qué sirve actualmente Vercel y qué sirve GitHub Pages, incluidas rutas `/api/*`, archivos de datos, manifests y descargas.
- [ ] Decidir URL canónica (Vercel, GitHub Pages o dominio propio) antes de generar fichas masivas.
- [ ] Probar cualquier ruta piloto directamente, tras recarga y desde los dos orígenes pertinentes; verificar archivos y enlaces.
- [ ] Inventariar las referencias de dominio en web, README, SDK, API, ejemplos, workflows y documentación; diseñar compatibilidad para URLs circulantes.
- [ ] Definir una fuente de verdad para cifras generables y sus definiciones: objeto/tabla/conjunto/vista/consulta, filas, sectores, fuentes, formatos y edición.
- [ ] Separar hechos derivados del catálogo de metadatos editoriales curados (p. ej., unidad de observación, limitaciones, método y condiciones de reutilización).
- [ ] Contrastar fuentes efectivas con el catálogo; alinear README y web sin atribuir datos a una institución que solo figure como regulador o enlace.
- [ ] Documentar discrepancias y evidencia; no corregir por intuición las cifras o afirmaciones que aún requieren auditoría.

### Decisiones de producto que requieren acuerdo
- [ ] Definir cómo se comunicará una limitación **material y no resuelta** a quien usa un dataset, sin añadir una métrica genérica de repeticiones a la portada.
- [ ] Resolver la tensión entre retirar todo aviso específico de la interfaz y evitar que alguien obtenga una agregación engañosa desde visor, SQL o descarga.
- [ ] Acordar si el control será: corregir/bloquear usos afectados, una nota de limitación acotada al dataset/consulta, o ambas. No cambiar la interfaz sobre este punto sin decisión.
- [ ] Definir qué significa “edición reproducible” y no prometer recuperación histórica si no se conservan archivos inmutables.
- [ ] Registrar las decisiones con fecha y evidencia antes de escalar la implementación.

### Primer spike de ruta/ficha
- [ ] Construir una ficha técnica mínima desde metadatos para un ID estable.
- [ ] Probar HTML/metadata servidos sin depender de que JavaScript termine de renderizar el contenido esencial.
- [ ] Abrir la URL en ventana nueva, recargar y seguir acciones reales de visor, descarga y SQL.
- [ ] Verificar que la ficha coincide con el catálogo, el manifest, el esquema y los archivos disponibles.
- [ ] Confirmar que URLs existentes continúan funcionando o tienen alternativa probada.

**Criterio de salida Fase 0:** inventario reproducible, dominios/orígenes entendidos, definición de métricas acordada, decisiones de riesgo abiertas visibles y una ruta piloto técnicamente viable.

## Fase 1 — fichas piloto

- [ ] Seleccionar cinco a diez objetos representativos: seguros, fondos mutuos, fondos de inversión, macro, estado financiero, archivo, gran tamaño y metadatos incompletos.
- [ ] Diseñar una plantilla que exponga solo metadatos existentes y omita honestamente lo que falta.
- [ ] Mostrar nombre, ID, fuente efectiva, período, unidad de observación, esquema, formatos, tamaños/hashes cuando existan, edición y limitaciones pertinentes.
- [ ] Añadir acciones solo cuando funcionen para ese objeto; ninguna acción decorativa o enlace genérico que pierda el contexto.
- [ ] Generar enlaces desde ID estable, no desde títulos editables.
- [ ] Revisar condiciones de reutilización por fuente y diferencias entre licencia del código y datos.
- [ ] Probar objetos con nombres largos, esquemas distintos, metadatos ausentes y muchos archivos.
- [ ] Probar cada ficha directa y en móvil; verificar textos, lectura, foco, estados vacíos y errores.
- [ ] Revisar que la ficha no convierta un hash o `data_release` en promesa de archivo histórico recuperable.

**Criterio de salida Fase 1:** cero fallos críticos de ruta/acción; metadatos coincidentes; campos ausentes no inventados; comprensión probada con alguien ajeno al proyecto.

## Fase 2 — catálogo y búsqueda

- [ ] Reutilizar lo que funcione del filtro actual; reemplazar solo brechas demostradas.
- [ ] Preparar 15–20 consultas de prueba, incluyendo IDs, nombres, instituciones, columnas, siglas, sinónimos, tildes, errores tipográficos, ambigüedad y cero resultados.
- [ ] Comparar alternativas de búsqueda con datos reales y escoger una; no mantener dos motores sin razón.
- [ ] Generar un índice estático de metadatos; medir peso, latencia, calidad de ranking y efecto en carga.
- [ ] Mantener sinónimos curados y semánticamente prudentes.
- [ ] Añadir únicamente filtros respaldados por metadatos consistentes.
- [ ] Diseñar resultados con nombre comprensible, ID, sector, fuente, período, formatos y enlace claro a la ficha.
- [ ] Diseñar estado sin resultados con próximos pasos útiles y sin telemetría invasiva.
- [ ] Probar búsqueda con teclado y en móvil; comprobar que no oculta resultados solo por una coincidencia estricta.

**Criterio de salida Fase 2:** las consultas prioritarias encuentran el objeto esperado arriba; filtros y enlaces son correctos; peso y rendimiento están medidos.

## Fase 3 — navegación y portada

- [ ] Prototipar navegación en cinco áreas como máximo: Datos, Ejemplos, Herramientas, Documentación y Sobre.
- [ ] Poner búsqueda/catálogo y acción principal a la vista sin scroll innecesario.
- [ ] Describir únicamente cobertura verificable; no prometer tiempo real, universalidad ni completitud no demostrada.
- [ ] Generar cifras de cobertura desde la fuente de verdad y explicar qué cuentan.
- [ ] Mostrar sectores y atajos que lleven a destinos/resultados reales.
- [ ] Seleccionar ejemplos neutrales y reproducibles; no publicar resultados que dependan de agregaciones no validadas.
- [ ] Trasladar contenido técnico largo sin eliminarlo ni romper sus enlaces.
- [ ] Mantener una jerarquía visual coherente entre portada, catálogo, fichas y herramientas.
- [ ] Revisar título, descripción, canonical, Open Graph y sitemap con contenido real.
- [ ] Comprobar compatibilidad con rutas anteriores antes de publicar.

**Criterio de salida Fase 3:** una persona nueva identifica qué es SIF, dónde buscar y cómo acceder; métricas y enlaces coinciden con artefactos publicados.

## Fase 4 — evidencia, calidad y documentación

### Repeticiones, claves y granularidad
- [ ] Retirar de la interfaz la sección «Cómo sumar sin sobreestimar» únicamente cuando el material técnico y la decisión sobre advertencias de riesgo material estén resueltos.
- [ ] No trasladar sus conteos, porcentaje o consulta SQL ilustrativa a otra pestaña como sustitución.
- [ ] Conservar las notas técnicas y la evidencia reproducible; no borrar el historial de auditoría.
- [ ] Revisar por objeto: edición/archivos, filas idénticas, fuente primaria, intermedio, pipeline, claves y unidad de observación.
- [ ] Clasificar cada caso con evidencia: fuente explicada, presente en fuente con causa indeterminada, introducido por pipeline, clave/granularidad o no reproducido.
- [ ] No llamar “legítima” a una repetición solo porque aparezca en la fuente; usar “presente en fuente, causa no determinada” cuando corresponda.
- [ ] No deduplicar automáticamente ni presentar una clave aparente como validada sin pruebas.
- [ ] Corregir/limitar o no promocionar los ejemplos materialmente afectados; valorar también riesgos en visor/SQL/descarga.
- [ ] Añadir al README una síntesis por objeto, con evidencia, impacto, acción y enlaces a notas técnicas.
- [ ] Mantener conteos detallados y consultas reproducibles en notas de auditoría, no como métricas de portada.

### README y metadatos
- [ ] Alinear las fuentes y modalidad de procesamiento del README con lo que el catálogo demuestra.
- [ ] Explicar objeto, conjunto, vista, consulta, fila y unidad de observación.
- [ ] Documentar transformaciones efectivas de identificadores y otros campos; evitar afirmaciones absolutas no compatibles con ellas.
- [ ] Documentar validaciones ejecutadas sin convertir controles parciales en un sello general de “calidad”.
- [ ] Separar fecha de publicación, fecha del dato, edición, hash de archivo y disponibilidad histórica.
- [ ] Aclarar licencia/código, condiciones por fuente, citación y limitaciones.

**Criterio de salida Fase 4:** afirmaciones principales trazables a evidencia; cuestiones abiertas identificadas; problemas materiales no escondidos detrás de una interfaz limpia.

## Fase 5 — herramientas, accesibilidad y evaluación de usuarios

- [ ] Aclarar estados del SQL: inicialización, listo, ejecución, éxito, error de motor y error de consulta.
- [ ] Ante fallo de SQL, ofrecer alternativa real: resultado precalculado, archivo o ejemplo reproducible cuando exista.
- [ ] Comprobar qué representa el visor: muestra, rango o conjunto completo; no insinuar carga total si no la hay.
- [ ] Probar Chrome, Firefox, Safari y móvil cuando estén disponibles; registrar entorno y pasos reproducibles.
- [ ] Revisar contraste WCAG AA, navegación por teclado, foco, nombres accesibles, estados anunciados y tablas en pantallas pequeñas.
- [ ] Probar con cinco personas ajenas al proyecto; registrar dónde dudan sin guiarlas.
- [ ] Medir éxito de tareas concretas: encontrar datos, fuente/período, descarga, definición de columna, ejemplo y limitación.
- [ ] Registrar limitaciones y pendientes en vez de afirmar que todos los problemas están resueltos.

**Criterio de salida Fase 5:** no hay bloqueos críticos en encontrar, comprender, abrir o descargar; los pendientes están visibles y priorizados.

## Fase 6 — publicación y seguimiento

- [ ] Confirmar dominio canónico, redirecciones, enlaces antiguos, sitemap, metadata y archivos.
- [ ] Publicar primero una versión candidata/staging si la arquitectura lo permite.
- [ ] Verificar rutas, descargas, respuestas de rango y SQL antes de ampliar el lanzamiento.
- [ ] No cambiar `no-store` ni el sufijo anti-caché de Parquet sin pruebas de integridad de rangos en los navegadores afectados.
- [ ] Mantener la arquitectura estática y límites de ráfagas ya existentes salvo evidencia que justifique modificarlos.
- [ ] No hacer pruebas de carga agresivas en producción.
- [ ] Instalar analítica solo con necesidad real, privacidad revisada y datos agregados; no capturar consultas identificables por defecto.
- [ ] Registrar línea base desde la fecha en que exista medición; no inventar retroactivamente métricas.

## Fase 7 — subproducto independiente

- [ ] Empezar después de validar el dataset y las agregaciones que consumirá.
- [ ] Elegir una pregunta estrecha, usuario y medida claramente definidos.
- [ ] Consumir el SIF como cliente reproducible (archivo/API/SDK según disponibilidad real); no fingir que existe SQL remoto.
- [ ] Documentar claves, unidades, períodos, método, validaciones, limitaciones y alternativas descartadas.
- [ ] Reproducir desde un entorno limpio y separar la identidad del subproducto de la plataforma neutral.

## Revisión antes de cerrar cualquier tarea

- [ ] ¿Resuelve una tarea de usuario demostrable?
- [ ] ¿La persona entiende qué verá y qué puede hacer a continuación?
- [ ] ¿Datos, copy, enlaces y cifras tienen evidencia y coinciden entre catálogo, web y documentación?
- [ ] ¿Se probaron el estado exitoso, el vacío, el error y la recuperación?
- [ ] ¿Se revisaron móvil, teclado, accesibilidad, rendimiento y coherencia visual?
- [ ] ¿Se mantuvieron las salvaguardas de rutas, privacidad y HTTP Range?
- [ ] ¿La mejora reduce fricción real sin añadir complejidad de mantenimiento injustificada?

## Próximo paso

- [ ] Completar la Fase 0 con una ficha técnica piloto y una decisión sobre dominio/orígenes.
- [ ] Resolver explícitamente cómo manejar en la experiencia los riesgos materiales todavía no aclarados antes de retirar el bloque actual de repeticiones.
