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
4. En PC, desde la raíz: `python -c 'from macro.scripts.pipeline_stream_macro_bcch import run_macro_pipeline; run_macro_pipeline()'`. Deja los seis archivos en `.local-data/macro/` (ignorado por Git). También se puede pasar `output_dir=` para una ruta externa.
5. Auditar y publicar explícitamente: `python -m macro.scripts.publish_macro`. Valida los tres Parquet, los JSON, continuidad mensual y no regresión frente a `docs/outputs/macro/`; solo después copia las salidas y actualiza el corte/filas de `data_manifest.json`. Revisar `git diff --stat` y los periodos, luego subir cambios mediante PR.
6. Primero fusionar el PR que incorpora `.github/workflows/macro.yml` a la rama principal: GitHub solo ofrece `workflow_dispatch` cuando el archivo está presente en la rama por defecto. Entonces el workflow puede dispararse **manualmente para la primera prueba** sin habilitar nada más. Para activar además la ejecución programada (día 8 de cada mes), configurar la variable de repositorio `ENABLE_MACRO_AUTOMATION=true`. **No hace commits ni publica directamente**: produce el artifact `macro-validada` (30 días de retención) con `docs/outputs/macro/` y `data_manifest.json`. Descargarlo, revisar los datos, copiarlos a una rama de trabajo y abrir un PR para fusionarlos. Si faltan secrets, falla antes de tocar los datos publicados. Más adelante se puede considerar crear PR automáticamente con un bot de permisos acotados, separado de esta sesión.

**No activar automáticamente otros sectores**. Sus códigos pueden conservarse en el repo y ejecutarse en PC; promocionarlos uno a uno con el mismo contrato de staging/auditoría/publicación. La auditoría global `scripts/audit_web_full.py` es adicional y requiere `pyarrow` y Node; no sustituye controles sectoriales. Los archivos ya publicados no se regeneran al instalar dependencias.
