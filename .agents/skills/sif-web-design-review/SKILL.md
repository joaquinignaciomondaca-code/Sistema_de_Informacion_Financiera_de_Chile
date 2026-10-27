---
name: sif-web-design-review
description: Revisa y mejora la interfaz del Sistema de Información Financiera de Chile con criterios de producto, visualización, accesibilidad y evidencia local del repositorio.
---

# Revisión de diseño web del SIF

Usa esta skill cuando la tarea trate sobre diseño, UX, interfaz, visualización o accesibilidad del sitio público. Es una guía propia del proyecto; no copia la skill de Vercel ni sustituye una prueba real en navegador.

## Objetivo del producto

Ayudar a personas investigadoras, analistas y público general a encontrar datos financieros chilenos, entender su cobertura y unidad de observación, evaluar si sirven para una pregunta, y luego consultarlos o descargarlos. La claridad sobre fuente, período, alcance y limitaciones importa más que adornar el dashboard.

## Antes de proponer cambios

1. Lee `docs/index.html` y `docs/css/app.css`; sigue los módulos pertinentes de `docs/js/` antes de asumir cómo funciona el flujo.
2. Inspecciona las variables/tokens y variantes de tema existentes. Extiéndelos antes de introducir colores, tipografías, radios, sombras o escalas paralelas.
3. Describe la audiencia, la tarea principal y el punto de fricción con evidencia del código o del comportamiento observado. No inventes contenido ni capacidades del producto.
4. Para rediseños, propone primero un rumbo compacto (paleta/roles, tipografía, jerarquía, composición y elemento distintivo) y compáralo contra la interfaz real. Conserva una identidad sobria y específica de información financiera chilena; evita convertirla en un dashboard SaaS genérico.
5. No reabras ni edites la checklist de validación de datos por iniciativa propia. Un análisis de UI no es evidencia para cerrar verificaciones de datos.

## Criterios de diseño

- Dar prioridad a búsqueda, cobertura, fecha, fuente, unidad de observación y siguientes acciones; distinguir claramente datos, metadatos y controles.
- Usar gráficos y mapas solo cuando la pregunta y la granularidad de los datos los justifiquen. Indicar unidades, período, fuente, notas y estados sin datos; ofrecer una alternativa textual o tabular cuando corresponda.
- Mantener diseño responsive, navegación por teclado, foco visible, etiquetas y nombres accesibles, contraste suficiente y respeto a `prefers-reduced-motion`.
- Mantener consistentes los temas ya soportados y los patrones de navegación. No ocultar metadatos importantes por ganar espacio ni representar inferencias como cifras oficiales.
- Evitar decoración que compita con lectura y comparación; no añadir animaciones, dependencias, fuentes remotas o iconos nuevos sin una razón y una evaluación de impacto.
- No cambiar contenido financiero, definiciones o semántica de campos como parte de un retoque visual sin evidencia y autorización expresa.

## Verificación disponible en el repositorio

Usa solo los comandos pertinentes al alcance y registra exactamente qué cubren; las auditorías estáticas/DOM no demuestran por sí solas funcionamiento en todos los navegadores ni una prueba con usuarios.

- `python3 scripts/audit_interfaz.py`
- `node scripts/audit_interfaz_dom.js`
- `python3 scripts/audit_movil.py`
- `node scripts/audit_movil_dom.js`
- `node scripts/test_busqueda_dom.js`

Si una herramienta o dependencia no está disponible, informa la limitación. Si se modifica la interfaz, revisa el diff y contrasta los estados afectados (vacío, error, carga, éxito), temas y tamaños de pantalla, no solo la portada.

## Entrega de una revisión

Separa hallazgos observados de recomendaciones; prioriza por impacto en comprensión/uso, no por preferencia estética. Para cada hallazgo importante indica archivo/selector o ubicación, consecuencia para la persona y propuesta. No afirmes haber validado visualmente algo si no se renderizó y revisó en un navegador.