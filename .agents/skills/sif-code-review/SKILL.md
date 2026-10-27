---
name: sif-code-review
description: Revisa diffs del SIF buscando errores verificables de lógica financiera, datos, contratos, privacidad, seguridad, automatización y regresiones antes de integrar cambios.
---

# Code review del SIF

Usa esta skill antes de cerrar un cambio o cuando se solicite una revisión. Revisa el diff y su contexto; no asumas que un cambio es correcto porque compila o porque una auditoría genérica termina sin errores.

## Pasos

1. Lee `git status`, el diff completo y el código cercano. Confirma si hay trabajo previo que no pertenece al cambio.
2. Sigue el comportamiento afectado a sus pruebas, consumidores, constructores y workflows. Identifica contratos de entrada/salida y artefactos generados.
3. Busca defectos concretos en:
   - parsing, coerciones silenciosas, redondeo/tolerancias, fechas, unidades, duplicados y datos faltantes;
   - normalización RUT/RUN y emparejamiento de entidades (un formato similar no prueba identidad);
   - paginación, reintentos, respuestas incompletas, concurrencia, paths y publicación parcial;
   - privacidad, secretos, exposición de columnas, XSS/inyección SQL y uso de dependencias;
   - esquemas/API/SDK/URLs, artefactos derivados desactualizados y compatibilidad;
   - pruebas insuficientes para el nuevo camino de éxito y sus fallos relevantes.
4. Comprueba solo los comandos que correspondan al alcance. Contrasta el diff con sus artefactos generados y no atribuyas a una prueba cobertura que no tiene.

## Hallazgos

Ordena los hallazgos por impacto y usa prioridad solo si está sustentada:

- **P0:** riesgo crítico de pérdida/exposición de datos o daño amplio e inmediato.
- **P1:** bug importante, probable o regresión que invalida una función/resultado publicado.
- **P2:** defecto acotado o caso borde real que debería corregirse.
- **P3:** observación menor; inclúyela solo si es accionable y no cosmética.

Cada hallazgo debe incluir archivo y línea aproximada, escenario reproducible, consecuencia y corrección sugerida. No inventes severidad, no conviertas preferencias de estilo en bugs y no informes asuntos preexistentes fuera del alcance salvo que bloqueen el cambio.

## Respuesta final de revisión

Muestra primero los hallazgos. Si no encuentras ninguno, dilo claramente y agrega alcance revisado, verificaciones ejecutadas y riesgos o limitaciones que quedan. En una revisión solamente, no modifiques el código.
