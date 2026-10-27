# Skills locales del repositorio

Estas guías viven en este checkout; no se instalaron globalmente ni agregan dependencias. Se escribieron para los flujos, contratos y restricciones reales del SIF. Carga solo las que correspondan a la tarea para mantener el contexto acotado.

## Ingeniería y calidad

| Skill | Cuándo usarla |
|---|---|
| [`sif-clean-architecture`](sif-clean-architecture/SKILL.md) | Límites de módulos, dirección de dependencias y lógica compartida. |
| [`sif-architecture-review`](sif-architecture-review/SKILL.md) | Decisiones transversales, integraciones, formatos o servicios nuevos. |
| [`sif-refactoring`](sif-refactoring/SKILL.md) | Limpieza o reestructuración que debe preservar comportamiento. |
| [`sif-test-design`](sif-test-design/SKILL.md) | Nuevas reglas, bugs, pruebas y cobertura de casos límite. |
| [`sif-code-review`](sif-code-review/SKILL.md) | Revisión final de diffs, regresiones, seguridad y contratos. |
| [`sif-best-practices`](sif-best-practices/SKILL.md) | Reglas permanentes de datos, privacidad, seguridad y publicación. |

Combinaciones sugeridas: arquitectura + review para cambios transversales; refactor + tests para refactorizar; tests + buenas prácticas para nuevas transformaciones; code review al cerrar un cambio. No cargues todo el conjunto para una tarea simple.

## Interfaz web

- [`frontend-design`](frontend-design/SKILL.md): skill de diseño de interfaz importada desde `anthropics/skills`; conserva su licencia en `frontend-design/LICENSE.txt` y la procedencia en `frontend-design/SOURCE.md`. Úsala al crear o rediseñar una interfaz.
- [`sif-web-design-review`](sif-web-design-review/SKILL.md): revisión propia del SIF para UX, accesibilidad, gráficos y verificaciones locales. Úsala en cambios/revisiones de interfaz.

No uses las guías de diseño para trabajos ETL o cambios solo de datos.

## Procedencia y selección

Las seis skills de ingeniería anteriores son guías locales nuevas, redactadas para este proyecto; no son copias de los repositorios enlazados en una propuesta externa ni instalaciones de paquetes upstream. Se priorizó una versión pequeña, auditable y vinculada al contrato real del repositorio. Las skills originales de interfaz mantienen sus propias fuentes/licencias.

No se copió **Web Design Guidelines** de Vercel: en la revisión previa no se encontró una licencia explícita y su flujo de actualización consulta un host que no está disponible en este entorno. No se añadió **UI/UX Pro Max** en esa pasada: cubre en gran parte la misma fase de dirección visual que `frontend-design`; se puede evaluar si aparece una necesidad concreta.
