---
name: sif-architecture-review
description: Evalúa decisiones de arquitectura que cruzan módulos, sectores, contratos o despliegues del SIF; compara alternativas con riesgos y una ruta incremental.
---

# Revisor de arquitectura SIF

Activa esta skill ante una nueva integración, dependencia, servicio, formato público, cambio transversal, modificación de automatización o decisión que abarque varias capas. Para un cambio local y reversible, no hace falta producir un informe de arquitectura completo.

## Procedimiento

1. **Acota la decisión.** Resume la necesidad y las restricciones explícitas. Inspecciona los entry points, módulos, pruebas, builders y workflows reales; sustenta el mapa con rutas del repositorio.
2. **Traza el flujo de datos.** Identifica origen, transformaciones, controles, escritura/publicación y consumidores. Localiza qué es código fuente, qué es contrato público y qué es un artefacto generado.
3. **Evalúa consecuencias.** Considera, cuando aplique:
   - exactitud semántica, unidades, fechas, identificadores, cobertura y procedencia;
   - aislamiento de red/archivos y posibilidad de probar sin fuente en vivo;
   - dependencias y compatibilidad entre sectores, API, web y SDK;
   - privacidad, seguridad, licencias y exposición de nuevos campos;
   - volúmenes, tiempos de descarga/consulta, límites de Actions y costo operativo;
   - reproducibilidad, idempotencia, concurrencia, recuperación y vuelta atrás;
   - generación de artefactos, migración de datos y cambios en CI.
4. **Compara opciones.** Incluye «no cambiar» cuando sea viable. Explica el costo y el riesgo, no solo la elegancia, de cada alternativa. Recomienda la opción compatible más pequeña que resuelva el problema.
5. **Propón etapas verificables.** Divide cambios de alto riesgo en pasos reversibles y asocia a cada uno pruebas, auditorías y contratos que deben seguir pasando.

## Formato de salida

- **Decisión y alcance**
- **Arquitectura actual observada** (flujo y rutas que lo demuestran)
- **Riesgos/límites** (solo hallazgos concretos; separa hechos de hipótesis)
- **Alternativas** (incluido no cambiar, si corresponde)
- **Recomendación y plan incremental**
- **Verificación necesaria y límites**

No uses «más capas» como sinónimo de mejor diseño. No conviertas una revisión en una reescritura ni des por hecho que todos los sectores siguen un patrón uniforme. En una solicitud de solo análisis, no edites archivos.
