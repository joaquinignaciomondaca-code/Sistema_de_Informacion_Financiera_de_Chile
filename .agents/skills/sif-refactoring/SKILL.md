---
name: sif-refactoring
description: Planifica refactorizaciones pequeñas y seguras del SIF, manteniendo datos, API, CLI, archivos y comportamiento observables.
---

# Refactorización segura del SIF

Activa esta skill al limpiar código heredado, separar responsabilidades o eliminar duplicación. Refactorizar significa mejorar estructura sin cambiar resultados; si también cambia la semántica, decláralo como cambio funcional y no lo escondas bajo «refactor».

## Flujo

1. **Define el comportamiento que debe permanecer.** Revisa consumidores, columnas y tipos, orden/filtros, formatos, rutas, CLI, períodos, unidades, metadatos y errores observables.
2. **Establece una línea base.** Corre las pruebas focalizadas antes del cambio. Si no existen, añade pruebas de caracterización pequeñas para las entradas/errores de mayor riesgo antes de mover lógica.
3. **Elige una sola responsabilidad.** Mantén el parche local; evita renombrar/mover muchos archivos o reorganizar varios sectores a la vez. Separa I/O de transformaciones solo cuando mejore la prueba o el acoplamiento de verdad.
4. **Haz el cambio incremental.** Conserva firmas, esquemas, nombres y contratos. Mantén I/O bajo control y usa datos sintéticos/temporales en pruebas. No consultes fuentes reales para comparar salidas.
5. **Compara y verifica.** Corre las mismas pruebas después; agrega casos necesarios; revisa salidas y metadatos afectados y ejecuta `--check`/auditorías asociadas.
6. **Revisa el diff.** Busca cambios de comportamiento accidental, artefactos irrelevantes, datos generados masivos y modificaciones fuera del alcance.

## Invariantes de datos

- No conviertas `null`/ausencia en cero ni cambies unidad, escala, clave, fecha o período como parte de una limpieza interna.
- Mantén política explícita de orden, duplicados, zonas horarias, precisión y tolerancias.
- Respeta la procedencia/hash y los gates de publicación existentes. No escribas sobre `docs/outputs/` ni regeneres históricos sin comprobar quién los posee y qué tarea lo autoriza.
- Si un resultado cambia, detén el refactor y determina si es un bug preexistente, un cambio intencional o una regresión; documenta el criterio y ajusta el alcance.

Prefiere una mejora pequeña, verificable y reversible a una abstracción especulativa o una reescritura completa.
