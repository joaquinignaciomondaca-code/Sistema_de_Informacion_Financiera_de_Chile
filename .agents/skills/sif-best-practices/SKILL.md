---
name: sif-best-practices
description: Aplica prácticas de seguridad, integridad financiera, privacidad, reproducibilidad y mantenimiento a los flujos de datos y consumidores del SIF.
---

# Buenas prácticas específicas del SIF

Carga esta guía para cambios de datos, scraping, seguridad, publicación, contratos o código compartido. Úsala junto con las convenciones del módulo; no reemplaza una prueba ni la documentación de una fuente.

## Fuentes y extracción

- Respeta términos, atribución, límites de uso y ritmo razonable de cada fuente. Usa timeout, comprueba estado/contenido, maneja reintentos acotados y conserva evidencia de fallos; no interpretes una respuesta vacía/rota como «sin registros».
- Valida esquema, tamaño y estructura antes de publicar. Evita aceptar silenciosamente cambios de columnas, truncamientos, ZIPs problemáticos o formatos inesperados.
- Separa descarga/parsing de la transformación; favorece ejecuciones idempotentes. Conserva la trazabilidad disponible (URL/fuente, fecha/período, nombre y hash cuando el flujo lo use).
- En pruebas, sustituye red y filesystem publicados por fakes, fixtures y temporales. No corras un extractor en vivo como verificación del código.

## Semántica y calidad financiera

- Documenta unidad, moneda, base temporal, frecuencia, cierre, granularidad, inclusividad y significado de campos relevantes. Un total de filas no implica registros únicos ni cobertura íntegra.
- Distingue cero, nulo, no disponible, no publicado y no aplicable. No imputes, completes ni combines períodos sin una regla documentada.
- Define precisión, redondeo y tolerancia desde la fuente/regla. Nunca relajes un gate de cuadratura o cobertura solo para hacer verde la prueba.
- Sigue `pipelines/auto/rut.py` y sus tests antes de alterar identificadores. No trates `RUN` como `RUT`, no recalcules un dígito ya existente sin contrato y no deduzcas equivalencia de entidades por formato.
- Asegura determinismo cuando sea posible: orden, serialización, fechas, nombres de archivos y conteos reproducibles.

## Seguridad y privacidad

- No guardes secretos, tokens, cookies, rutas privadas, datos de sesión ni registros locales en Git/logs. Minimiza campos publicados y contrasta los cambios con `PRIVACIDAD.md`.
- Trata archivos públicos externos como entrada no confiable: controla paths, tamaños, encoding, HTML, SQL y tipos antes de usarlos. En la web aplica escape de contenido; para consultas sigue `docs/js/sql_guard.js` y las defensas/auditorías existentes.
- No debilites `scripts/audit_secretos.py`, auditorías de privacidad, XSS o SQL sin motivo verificable y pruebas equivalentes.
- No añadas servicios, CDN, fuentes remotas, paquetes o librerías nuevas por defecto. Justifica necesidad, licencia, mantenimiento, impacto en usuarios/offline y cadena de suministro.

## Publicación y operación

- Revisa `.github/workflows/` para entender disparadores, gates, permisos, concurrencia y commits automáticos. Un workflow exitoso no garantiza por sí mismo semántica correcta del dato.
- Los constructores son la fuente de verdad para sus salidas derivadas; sigue su orden y `--check` cuando esté disponible. No edites a mano una salida generada ni publiques un cambio de catálogo sin reconciliarlo con sus archivos.
- Mantén errores explícitos y fallos cerrados cuando el contrato exige validación. No registres datos sensibles al diagnosticar.
- Usa la auditoría concreta de CI y reporta su alcance real. No afirmes cobertura completa a partir de lint, un test unitario o un detector estático aislado.
