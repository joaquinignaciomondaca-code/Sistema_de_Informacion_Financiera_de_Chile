# ETL con api-anything · CMF y SPensiones (experimento)

Este directorio prueba si `api-anything` puede servir como capa de ingesta para
fuentes HTML de la CMF y la Superintendencia de Pensiones, sin escribir un
parser por página. **No es un publicador de datos**: no escribe Parquet ni toca
`docs/outputs/`. Es un experimento con fixtures y un runbook para cuando se
quiera llevar a fuentes vivas.

## Qué está probado aquí

`scripts/probar_api_anything_etl.py` (evidencia en `docs/api/api_anything_etl.log`):

1. Extracción **tier 1** (HTTP puro, sin navegador) de tablas HTML con una receta
   `items` + `fields`.
2. `verify --strict` en verde con la fixture original.
3. **Deriva**: se cambia la clase de la tabla en la fixture y `verify` falla.
4. **Reparación**: se actualiza el selector de la spec y `verify` vuelve a pasar.

Las fixtures (`fixtures/cmf_entidades.html`, `fixtures/spensiones_afp.html`) son
**sintéticas**: imitan la estructura de tabla de esas páginas, pero no son datos
publicados ni se presentan como una extracción viva verificada.

## Qué no está probado

- La extracción contra `cmfchile.cl` o `spensiones.cl` en vivo. El entorno de
  desarrollo bloquea esos hosts (y `github.io`), así que no hay evidencia de una
  corrida real contra la fuente.
- Tier 2/3 (navegador). No hay Chromium/Playwright en el entorno; las páginas que
  exijan JavaScript o sesión no se ejercitaron.
- La estabilidad de los selectores de la fuente real. Las páginas de la CMF
  cambian de plantilla; una spec aprendida hoy puede derivar mañana. Por eso el
  ciclo `verify → falla → reparar → verify` es parte del diseño, no un accidente.

## Runbook para fuentes vivas (cuando haya red y navegador)

```bash
# 1. Aprender la operación desde la página real (tier 2/3 si hace falta navegador).
npx -y api-anything@0.3.2 learn https://www.cmfchile.cl/... --example rut=97004000

# 2. Revisar la receta HTML sugerida (items/fields) y guardarla como spec local.
npx -y api-anything@0.3.2 inspect <capture> <n> --outline

# 3. Verificar con casos positivos y negativos.
npx -y api-anything@0.3.2 verify <sitio> --strict

# 4. Programar verify periódico. Si falla, la deriva es esperable:
#    reparar el selector (heal) y volver a verificar antes de publicar.
npx -y api-anything@0.3.2 heals <sitio>
```

Antes de convertir esto en un publicador:

- Contrastar la extracción con el parser determinista existente del sector
  (`bancos/`, `seguros/`, `pensiones/`) y exigir cuadratura. Ningún número
  publicado debe provenir de una receta HTML sin validación.
- Declarar la fuente y su cita en `pipelines/api/fuentes.py` y en el catálogo.
- Añadir el workflow con horario y su responsable en `pipelines/auto/inventario.json`,
  como exige el guardián de automatización.
- Mantener `verify --strict` en CI contra una fixture congelada de la página real
  (no sintética) para detectar deriva sin depender de la red en cada PR.
