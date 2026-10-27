# Guía de trabajo para agentes

## El proyecto en una página

El Sistema de Información Financiera de Chile (SIF) es un producto de datos: integra fuentes públicas de la CMF, el Banco Central y la Superintendencia de Pensiones, valida y publica tablas/series, y ofrece un sitio estático para consultarlas con SQL en el navegador. La mayor parte del procesamiento está en Python 3.11; la web es HTML/CSS/JavaScript sin framework ni build central. No des por hecho que hay un servicio de consultas o una base de datos central.

## Mapa para orientarse

- `pipelines/` y `<sector>/scripts/`: extracción, adaptación de fuentes, normalización, validación y publicación por flujo/sector.
- `pipelines/auto/`: reglas compartidas de identificadores, cuadraturas, privacidad y estabilidad. Revisa sus contratos antes de modificar una regla común.
- `<sector>/tests/`, `pipelines/**/tests/`, `scripts/test_*.py` y `scripts/test_*.js`: pruebas específicas; el proyecto usa principalmente `unittest` y scripts de prueba Node, no un runner único.
- `data_manifest.json` y `docs/outputs/`: manifiesto y datos publicados. Comprueba quién los genera antes de tocar una salida.
- `scripts/build_*.py`, `scripts/audit_*.py`, `scripts/auditar_*.py`: constructores y controles del contrato, catálogo, métricas y web. Si un artefacto es derivado, usa su constructor y su opción `--check` cuando exista; no edites a mano el resultado generado.
- `docs/api/`, `docs/js/`, `docs/css/` y `docs/index.html`: contrato estático y aplicación web. `sdk/python/` y `examples/`: consumidores del contrato.
- `.github/workflows/`: secuencia real de pruebas, despliegues y actualizaciones programadas. Léela si un cambio toca automatización, publicación o datos.
- `.agents/skills/`: guías locales específicas. Elige las pertinentes; no cargues todas por defecto.

## Límites y cuidado con los datos

- Trata el flujo extracción → parseo/normalización → validación → publicación → contrato derivado → consumidores como un mapa inicial, no como una arquitectura que haya que imponer. Confirma dependencias, orden de generación y responsables en el código y en Actions antes de cambiar límites.
- Mantén el código específico de una fuente/sector en su adaptador cuando corresponda; comparte lógica solo si la regla es realmente común. Mantén la lógica de dominio comprobable sin red ni interfaz cuando sea razonable, sin añadir capas o abstracciones por ceremonia.
- Preserva el significado financiero, las unidades, monedas, fechas/cierres, granularidad, procedencia, nombres de columnas, esquemas, rutas y comportamiento público. Ausencia no significa cero; una clave con formato parecido no prueba que dos campos identifiquen la misma entidad. No inventes observaciones ni completes información sin una regla documentada.
- Las extracciones pueden consultar o descargar fuentes reales. No ejecutes actualizadores, backfills, publicadores ni comandos con efectos externos como parte de una prueba rutinaria: primero inspecciona sus efectos, requiere la tarea correspondiente y, cuando sea posible, usa fixtures y temporales.
- No publiques datos locales/privados, secretos ni identificadores personales por accidente. Si el cambio toca privacidad o exposición de campos, revisa `PRIVACIDAD.md`, las reglas existentes y el workflow de auditoría pertinente.
- No regeneres grandes conjuntos ni dependencias derivadas por inercia. Investiga qué productos deben cambiar, usa el orden oficial documentado y revisa tamaño/diff. No introduzcas dependencias, frameworks o servicios nuevos sin necesidad justificada.
- Evita migraciones globales, cambios de formato o reestructuraciones masivas si el pedido se resuelve con un cambio pequeño y compatible. Si una incompatibilidad es necesaria, identifícala y documenta el impacto.

## Flujo recomendado

1. **Explorar:** comprueba `git status --short --branch`; lee el módulo, sus pruebas, documentación y workflow relacionados. No sobrescribas trabajo preexistente.
2. **Planificar:** para cambios de varias capas, contratos o alto riesgo, resume el flujo afectado, los invariantes y una secuencia incremental antes de editar. Para cambios pequeños, basta un plan breve.
3. **Implementar:** una responsabilidad por cambio; primero conserva el comportamiento observable. Mantén las pruebas herméticas, con datos sintéticos y sin red.
4. **Verificar:** ejecuta la prueba más cercana y los controles derivados directamente afectados. Después de refactorizar, corre las pruebas de caracterización antes/después. Usa `--check` si el constructor lo ofrece.
5. **Revisar:** inspecciona `git diff`, `git diff --check` y los archivos generados. Informa qué comandos corriste, qué cubren y qué no; no afirmes que toda la suite o una revisión visual pasó si no se ejecutó.

## Comandos y límites de verificación

- Entorno esperado: Python 3.11; dependencias declaradas en `requirements.txt` y, para el SDK, `sdk/python/pyproject.toml`.
- Prueba Python puntual: `python -m unittest ruta.del.modulo_de_prueba -v`.
- Descubrimiento de una suite concreta: `python -m unittest discover -s ruta/al/directorio/tests -v`.
- Prueba JavaScript existente: `node scripts/test_nombre.js` o el comando explícito de su workflow. No existe un `package.json` raíz que defina un runner/linter general.
- Los constructores del contrato suelen aceptar `--check`; confirma el script y su documentación antes de asumirlo. Para cambios de web/datos consulta `.github/workflows/web_audit.yml` y ejecuta las auditorías pertinentes, no todas indiscriminadamente.
- No hay un único comando local que garantice reproducir toda CI: algunos jobs instalan dependencias, leen el historial completo, necesitan artefactos/datos publicados o tienen efectos externos. Declara cualquier limitación del entorno.

## Selección de skills

- Cambios de límites, dependencias o módulos compartidos: `sif-clean-architecture`; si la decisión abarca varias capas, `sif-architecture-review`.
- Refactorización: `sif-refactoring` + `sif-test-design`.
- Nueva lógica o cambio de datos/contrato: `sif-test-design` + `sif-best-practices`.
- Revisión final o solicitud de auditoría: `sif-code-review`.
- UI/UX: `sif-web-design-review`; carga `frontend-design` al crear o rediseñar interfaz, no para ETL.

Las skills son criterios de trabajo, no evidencia de que se ejecutaron las comprobaciones. Registra resultados reales y hallazgos con archivo/línea cuando corresponda.
