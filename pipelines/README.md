# Operación híbrida de datos

**Fuente → staging → auditoría → publicación**. Los scripts y los métodos quedan versionados; los datos pesados y las credenciales no. La web estática de `docs/` consume archivos publicados, no el staging.

| Flujo | Ejecución | Publicación |
| --- | --- | --- |
| Series estructuradas pequeñas y maduras (piloto: `macro/`) | PC o GitHub Actions | Artifact validado; revisión humana y publicación mediante PR |
| PDFs, descargas masivas, notas asistidas, métodos experimentales | PC (`pipelines/manual/`, scripts por sector) | Manual, tras auditoría sectorial |
| Cambios de esquema/catálogo de la web | Revisión humana | Junto con Parquet/JSON compatibles |

Criterios antes de mover otro sector a Actions: fuente estable y términos de uso compatibles, sin dependencia de carpetas personales; credenciales externalizadas; dependencias fijadas; staging separado de `docs/`; auditoría que falle con datos incompletos; frecuencia y coste acotados; revisión de cambios antes de fusionar.

## Piloto BCCh macro

1. **Urgente**: rotar la contraseña BCCh previamente expuesta en el historial Git (quitarla del HEAD no la revoca). Verificar si hay otros sistemas donde se reutilizó. Nunca poner credenciales en el repositorio ni enviarlas por chat.
2. Instalar Python 3.11 y `python -m pip install -r macro/requirements.txt` en un entorno virtual local.
3. Configurar `BCCH_EMAIL` y `BCCH_PASSWORD` como variables de entorno **locales**. En GitHub se usan los *repository secrets* `USER_BCCH` y `PASSWORD_BCCH` (*Settings → Secrets and variables → Actions*); el workflow los asigna a esas variables de entorno sin publicar valores. Usar **la contraseña nueva**. No usar `set -x` ni imprimir las variables.
4. En PC, desde la raíz: `python -m macro.scripts.daily_macro`. Consulta las 23 series **solo desde el primer día del último mes guardado**, no desde 2013: se vuelve a leer el mes en curso para recomputar promedios/cierres y recoger publicaciones rezagadas. Combina las observaciones nuevas con el histórico Parquet, valida y deja un checkpoint en `.local-data/checkpoint/macro/` (ignorado por Git). Sin Parquet previo, realiza backfill completo una sola vez. También se puede usar `run_macro_pipeline(output_dir=..., baseline_dir=...)` sin publicación.
5. Para publicar solo staging previamente generado: `python -m macro.scripts.publish_macro`. El orquestador diario lo hace automáticamente **en su copia local**, tras validar tres Parquet/JSON, continuidad mensual y no regresión. Revisar `git diff --stat` y los períodos y subir mediante PR; la web pública no cambia hasta la fusión.
6. Fusionar el PR que incorpora `.github/workflows/macro.yml` a `main`: GitHub ejecuta `schedule` solo desde la rama por defecto. El workflow corre **diariamente a las 10:00 UTC** (aprox. 07:00 u 08:00 en Santiago, según horario de verano), además de permitir ejecución manual. En cada runner efímero recupera el último checkpoint validado de Actions Cache, o usa los Parquet publicados si no hay cache; si tampoco existen hace backfill. Después de validar guarda un checkpoint nuevo **solo si cambió**. Si los datos públicos difieren del resultado validado, crea el artifact `macro-validada` (30 días), pero **no hace commits ni publica directamente**. Revisar/descargar los seis archivos más `data_manifest.json` y fusionarlos mediante PR. Si no hay novedades frente a la web publicada, no crea artifact. Los cambios ya detectados pero aún no fusionados reaparecerán en un artifact de corridas siguientes. Si faltan secrets, falla antes de consultar. Para correcciones históricas anteriores al último mes se requiere una reconstrucción deliberada fuera del job diario.

**No activar automáticamente otros sectores**. Sus códigos pueden conservarse en el repo y ejecutarse en PC; promocionarlos uno a uno con el mismo contrato de staging/auditoría/publicación. La auditoría global `scripts/audit_web_full.py` es adicional y requiere `pyarrow` y Node; no sustituye controles sectoriales. Los archivos ya publicados no se regeneran al instalar dependencias.
