# Monitor de novedades normativas CMF

El módulo consulta el listado oficial de legislación y normativa de la CMF, conserva identificadores y huellas para deduplicar publicaciones, descarga los documentos oficiales y publica un feed JSON estático en `docs/outputs/normativa_cmf/feed.json`. El índice incremental se mantiene en `data/normativa_cmf/state.json`.

## Ejecución local

```bash
python -m venv .venv
.venv/bin/python -m pip install -r pipelines/normativa_cmf/requirements.txt
.venv/bin/python -m unittest discover -s pipelines/normativa_cmf/tests -v
.venv/bin/python -m pipelines.normativa_cmf.audit
node scripts/audit_normativa_web.js
python scripts/audit_navigation.py
```

Para actualizar desde CMF se puede ejecutar `python -m pipelines.normativa_cmf.pipeline`. La fuente se consulta en vivo; si no responde o su estructura cambia, la ejecución falla sin reemplazar el último feed válido. El sandbox local puede no tener acceso TLS a la CMF; ese fallo no se considera un listado vacío.

## GitHub Actions y Gemini

El workflow `.github/workflows/normativa_cmf.yml` corre en días hábiles, al modificar el módulo y mediante `workflow_dispatch`. En Actions la credencial se lee exclusivamente del secreto `API_GOOGLE_AI_STUDIO`; no se copia al estado, al feed ni a la web, y nunca se imprime en logs. La llamada usa la **Interactions API REST** (`/v1beta/interactions`), la revisión `2026-05-20`, salida JSON estructurada y `store: false` para no retener en Interactions los documentos enviados. Los IDs se fijan en el workflow a los modelos estables documentados: `gemini-3.5-flash-lite` y `gemini-3.8-flash`; no dependen de variables de repositorio que puedan estar desactualizadas. Google recomienda Interactions como interfaz predeterminada desde junio de 2026 y considera legacy a `generateContent`, aunque la mantiene soportada. La migración era apropiada; como Interactions también devolvió HTTP 403 en la prueba, el endpoint legacy no explica por sí solo el fallo.

El flujo utiliza Flash-Lite para el análisis ordinario y escala a Flash cuando la confianza es baja o la salida deja evidencia ambigua, sujeto al límite de llamadas de la ejecución. También limita las descargas de PDF por corrida (`NORMATIVA_MAX_PDF_CHECKS`) para dejar tiempo al workflow; los documentos diferidos permanecen pendientes y se retoman después. Si no hay clave, se agota la cuota o Gemini devuelve una respuesta no utilizable, la publicación se conserva con `analysis_status: "pendiente"` y marca de revisión; ante HTTP 400/401/403/404/429 el flujo suspende nuevos intentos de Gemini durante esa ejecución para no gastar llamadas repetidas. Para diagnosticar errores HTTP, Actions muestra el estado y un mensaje breve de Google tras redactar claves; el feed público conserva solo el código HTTP. Una consulta exitosa de la CMF no se presenta como ausencia de novedades.

Referencias oficiales: [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview), [salida estructurada](https://ai.google.dev/gemini-api/docs/structured-output), [Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) y [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).

## Evidencia, fechas y revisión

- `publication_date` es la fecha del listado CMF; `effective_date` solo se publica si su cita puede verificarse en el texto extraído del PDF.
- Resúmenes, asociaciones sectoriales, normas relacionadas y vigencias conservan citas literales y páginas. Una asignación sectorial sin cita verificable se descarta.
- PDF sin texto nativo, baja confianza, ambigüedad y ausencia de clasificación se marcan para revisión humana. La extracción no realiza OCR.
- `last_checked_at` marca la última consulta exitosa a la fuente. `last_detected_at` se actualiza cuando el monitor incorpora una publicación nueva o detecta un cambio; cada evento también conserva su propia fecha de detección.
- La fecha de publicación y la vigencia se muestran por separado. Los resúmenes son informativos, no conclusiones ni asesoría legal.

Antes de publicar, el workflow ejecuta pruebas unitarias, audita feed y estado, y valida la conexión de la vista web con la industria activa del explorador. El secreto no se necesita para las pruebas.
