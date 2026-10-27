---
name: sif-clean-architecture
description: Revisa límites y dirección de dependencias entre extracción financiera, reglas de dominio, publicación, contrato, web estática y SDK del SIF; úsala al diseñar módulos o tocar lógica compartida.
---

# Clean Architecture aplicada al SIF

Usa esta guía al crear un módulo, mover responsabilidades o modificar dependencias entre capas. El objetivo es mantener lógica financiera comprobable y publicación predecible, no imponer una arquitectura de capas rígida ni convertir el repositorio en una aplicación de framework.

## Lee el flujo real primero

Como mapa inicial, sigue:

`fuente → adaptador/parseo → normalización y reglas → validación/publicación → artefactos del contrato → web/SDK/ejemplos`

Confirma la secuencia con imports, entry points, scripts `build_*`, workflows de `.github/workflows/` y pruebas. Hay diferencias entre sectores: no supongas que todos comparten la misma pipeline ni que cada archivo bajo `docs/outputs/` tiene el mismo proceso de generación.

## Límites que conviene conservar

- El adaptador de cada fuente se ocupa de I/O, peculiaridades de formatos y mapeo de entrada. Evita que una regla contable o de identidad dependa innecesariamente de una respuesta HTTP, un selector HTML o un elemento DOM.
- Las transformaciones y validaciones puras deben poder ejercitarse con entradas pequeñas, sin red ni escritura en la publicación. Extrae una función pura cuando reduzca acoplamiento real; no agregues interfaces, capas o inyección de dependencias por rutina.
- `pipelines/auto/` contiene contratos compartidos. Antes de generalizar desde un sector, comprueba que los demás consumidores necesitan la misma semántica y que las pruebas cubren sus casos.
- Los constructores de `scripts/` enlazan salidas y artefactos derivados. No sustituyas ese flujo por ediciones manuales de JSON/índices/esquemas ni dupliques reglas de negocio en la web.
- La web consulta archivos/contratos publicados y ejecuta SQL en el navegador. No introduzcas un backend o base central como solución por defecto; evalúa primero el contrato estático y el SDK existentes.
- Mantén la automatización fuera de la lógica de dominio: workflows orquestan pasos; las reglas reutilizables viven en código testeable.

## Revisión de dependencias

1. Nombra la regla o responsabilidad que se modifica y quién debe poseerla.
2. Traza quién importa a quién y qué paso produce cada artefacto afectado.
3. Señala toda dependencia que invierte el flujo (por ejemplo, lógica de dominio que necesita UI o red) y verifica si es una necesidad real o un límite accidental.
4. Comprueba efectos sobre otros sectores, el contrato publicado, SDK, rutas, workflows y datos existentes.
5. Propón el cambio compatible más pequeño. Si el límite actual es razonable, conserva la estructura en vez de refactorizar por apariencia.

## Señales de una abstracción prematura

- Una utilidad común con una sola implementación y excepciones sectoriales crecientes.
- Capas que solo reenvían argumentos o reflejan carpetas sin aislar una razón de cambio.
- Dos implementaciones que parecen similares pero expresan reglas de fuente/contabilidad distintas.
- Código de presentación que decide cómo limpiar o interpretar importes financieros.

Al informar, cita evidencia del repositorio y distingue una dependencia observada de una recomendación. No describas el sistema como «Clean Architecture» implementada si solo estás evaluando algunos de sus principios.
