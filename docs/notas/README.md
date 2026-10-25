# Notas: decisiones, mediciones y auditorías

<!-- Generado por scripts/build_indice_notas.py. No editar a mano:
     --check falla si no coincide con las notas de la carpeta. -->

Las 63 notas de esta carpeta. Cada una registra una decisión, una
medición o una corrección, con la fecha en que se hizo y el motivo. Se citan
desde el código, la web y las respuestas a las revisiones externas, así que
están escritas para poder verificarse: qué se afirmó, contra qué se contrastó
y qué quedó abierto.

Para añadir una: crea `AAAA-MM-DD_tema.md` con un `# Título` y ejecuta
`python3 scripts/build_indice_notas.py`; el índice se rehace solo.


## octubre de 2026

- [Checklist vivo del rediseño del SIF Chile](checklist_rediseno_sif_2026-10-24.md) — preparación y decisiones de alcance; no es autorización para rediseñar de una vez toda la web.
- [Banca: valores normalizados y maestro validado — 2026-10-23](ruta_banca_valores_2026-10-23.md) — Dos cosas en la sección «Banca y estados financieros CMF»:
- [Revisión externa del 2026-10-23: qué aguanta y qué no](revision_externa_2026-10-23.md) — una revisión externa del sitio afirmó que ffmmcarteranacional publica
- [La repetición no es ocasional: se midió período por período](repeticion_por_periodo_2026-10-23.md) — una revisión externa señaló que el titular de la portada decía
- [La portada, escrita para quien entra por primera vez](portada_registro_2026-10-23.md) — revisión de la portada «de cara a una persona que entra a la
- [La portada muestra lo que el proyecto mide](portada_calidad_2026-10-23.md) — una revisión externa del sitio desplegado dijo que la capa técnica ya
- [Mapa relacional, cifras y contrato: lo que se corrigió el 2026-10-23](mapa_cifras_2026-10-23.md) — tres defectos vistos en pantalla —los títulos del mapa relacional se
- [Claves primarias: el defecto del 2026-10-23 y su corrección](claves_duplicados_2026-10-23.md) — scripts/verificarclaves.py, docs/api/claves.csv y el contrato docs/api/v2/.
- [El monitor normativo se cayó por el origen, no por el repositorio](ci_normativa_origen_caido_2026-10-23.md) — la corrida [40038135849](https://github.com/joaquinignaciomondaca-code/SistemadeInformacionFinancieradeChile/actions/runs/40038135849),
- [Ruta de optimización para celulares — 2026-10-22](ruta_movil_2026-10-22.md) — que el sitio sea usable con una mano en un teléfono de 360–430 px, sin
- [Ruta de implementación — API pública SIF v1](ruta_api_v1_2026-10-22.md) — [apipublicafactibilidad2026-10-22.md](apipublicafactibilidad2026-10-22.md)
- [¿Se pueden publicar estos datos?](licitud_publicacion_datos_2026-10-22.md)
- [Explorador sin solapes en pantalla pequeña — 2026-10-22](diseno_explorador_sin_solapes_2026-10-22.md) — En un teléfono (captura de 319 px de ancho) el árbol del explorador
- [Decisiones pendientes de la API v1 (D1–D4)](decisiones_api_v1_2026-10-22.md) — cuesta cambiarla después.
- [Publicar el RUT del emisor en `fi.cartera_nacional`: plan y justificación](decision_publicacion_rut_2026-10-22.md) — propuesta, no ejecutada.
- [P3 · API pública documentada y ejemplos reproducibles — estudio de factibilidad](api_publica_factibilidad_2026-10-22.md) — qué tan factible es añadir una API pública documentada, ejemplos
- [Rendimiento de carga: qué se cambió tras el informe Lighthouse — 2026-10-21](rendimiento_carga_2026-10-21.md) — el informe de Lighthouse del sitio desplegado señaló TBT de 680 ms, 21 peticiones que
- [Prueba de instalación de las cinco herramientas — 2026-10-21](prueba_de_instalacion_herramientas_2026-10-21.md) — instalar y probar todo lo que se venía evaluando en notas.
- [Evaluación de UI UX Pro Max — 2026-10-21](evaluacion_uiux_pro_max_2026-10-21.md) — revisar <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill> y decidir si sirve para
- [Evaluación de SkillSpector — 2026-10-21](evaluacion_skillspector_2026-10-21.md) — revisar <https://github.com/NVIDIA/SkillSpector> y decidir si sirve para este proyecto.
- [Evaluación de Cloudflare `security-audit-skill` — 2026-10-21](evaluacion_security_audit_skill_2026-10-21.md) — revisar <https://github.com/cloudflare/security-audit-skill> y decidir si sirve para este proyecto.
- [Evaluación de Impeccable (skill de diseño + detector) — 2026-10-21](evaluacion_impeccable_2026-10-21.md) — revisar <https://github.com/pbakaus/impeccable> y decidir si sirve para este proyecto.
- [Evaluación de Hallmark — 2026-10-21](evaluacion_hallmark_2026-10-21.md) — revisar <https://github.com/Nutlope/hallmark> y decidir si sirve para este proyecto.
- [Evaluación de ECC — 2026-10-21](evaluacion_ecc_2026-10-21.md) — revisar <https://github.com/affaan-m/ECC> y decidir si sirve para este proyecto.
- [Diseño: cierre de los hallazgos del detector — 2026-10-21](diseno_detector_2026-10-21.md) — 73 hallazgos primarios tras la corrección de contraste y tipografía
- [Corrida completa de `security-audit-skill` — 2026-10-21](corrida_security_audit_skill_2026-10-21.md) — ejecutar de verdad la skill cloudflare/security-audit-skill sobre el sitio, no
- [Contraste y piso tipográfico — 2026-10-21](contraste_y_tipografia_2026-10-21.md) — aplicar las correcciones que salieron de la evaluación de Impeccable
- [Circular 1835 completa y vistas analíticas — 2026-10-21](circular_1835_extendida_2026-10-21.md) — El catálogo y el extractor ahora cubren los registros B.1–B.14 del anexo técnico, en el orden del manual.
- [Auditoría de calidad: registros tipo 6 de la Circular 1835](auditoria_calidad_registros_tipo6_2026-10-21.md) — ingestión, normalización, publicación Parquet, linaje, validaciones y exposición en la web de los registros tipo 6 hallados en B.11 (archivos E) y B.14 (archivos G), más…
- [Anexos técnicos 2024 (B.1–B.14): qué hay hoy en el repo y qué falta para publicarlos todos](anexos_1835_cobertura_14_registros_2026-10-21.md) — 2026-10-21 · Alcance: extractor de seguros (seguros/scripts/), inventario de
- [Cómo citar la base, reproducibilidad y privacidad (2026-10-20)](version_academica_y_privacidad_2026-10-20.md) — Nota de implementación.
- [Verificación de descargas contra el manifiesto — 2026-10-20](verificacion_descargas_2026-10-20.md) — Punto 5 de la checklist.
- [Recorte visual de industrias (2026-10-20)](recorte_visual_industrias_2026-10-20.md) — El sistema publica 15 industrias, 75 conjuntos y 13,5 millones de filas, pero el valor
- [Diagnóstico del motor SQL (DuckDB-Wasm) y tiempo de arranque — 2026-10-20](diagnostico_motor_sql_2026-10-20.md) — Punto 1 de la checklist de auditoría: reproducir el fallo de inicialización y registrar la etapa exacta.
- [Cifras oficiales del sitio — 2026-10-20](cifras_oficiales_2026-10-20.md) — Única referencia para las cifras de portada, README y notas.
- [Cardinalidad de las uniones del mapa relacional (punto 10)](cardinalidad_relaciones_2026-10-20.md) — Fecha: 2026-10-20.
- [Búsqueda por pregunta o concepto (punto 9)](busqueda_por_pregunta_2026-10-20.md) — Fecha: 2026-10-20.
- [Auditoría de punta a punta: fuente → fila publicada (punto 6)](auditoria_fuente_a_fila_2026-10-20.md) — Fecha: 2026-10-20.
- [Revisión de accesibilidad — 2026-10-20 (punto 11)](accesibilidad_2026-10-20.md) — - HTML estático (docs/index.html) con axe-core 4 sobre jsdom, con la regla color-contrast desactivada (jsdom no calcula estilos reales).
- [Seguros (Circular 1835): todos los campos de la ficha, con el nombre original de la CMF](campos_completos_seguros_1835_2026-10-08.md) — 2026-10-08 · Alcance: extractor de cartera de inversiones de seguros
- [Cobertura de operaciones REPO (pactos) — revisión 2026-10-07](cobertura_repos_pactos_2026-10-07.md) — En esta nota, REPO significa operación de compra/venta con pacto; no repositorios de código.
- [Auditoría profunda de los datos de compañías de seguros (CMF, Circular 1835) — 2026-10-07](auditoria_seguros_2026-10-07.md) — Objeto auditado: todos los datos publicados del sector seguros — las 8 tablas de
- [Auditoría de calidad de datos FI — 2026-10-07](auditoria_calidad_fi_2026-10-07.md) — Revisión local de los extractores fi/scripts/actualizarcarteras.py y fi/scripts/eeffxml.py,
- [Revisión de la extracción de balance y estado de resultados por industria](revision_extraccion_eeff_industrias_2026-10-01.md) — Fecha: 2026-10-01 · Alcance: la lógica que convierte las fuentes de la CMF en las tablas
- [Revisión de cobertura de fondos de inversión — 2026-06](revision_cobertura_fi_2026-10-01.md) — no falta una categoría completa.
- [Balance y estado de resultados de fondos mutuos (FFMM): cómo obtenerlos del XML de la CMF](ffmm_estados_financieros_xml_2026-10-01.md) — IMPLEMENTADO y publicado el 2026-10-01 (ffmmbalance y ffmmresultados, workflow ffmmeeff.yml,

## septiembre de 2026

- [Rediseño de la sección Macroeconomía — propuesta de estructura (2026-09-30)](rediseno_seccion_macro_2026-09-30.md) — Objeto: la sección macro del sitio (docs/), hoy desplegada en Vercel.
- [Las 8 oportunidades, implementadas — y el veredicto de la pestaña SQL](implementacion_8_oportunidades_y_guardia_sql_2026-09-30.md) — Fecha: 2026-09-30 · Corte de datos: 2026-06 (69 trimestres publicados)
- [Diagnóstico: `TProtocolException: Invalid data` mata el motor DuckDB-Wasm](diagnostico_tprotocol_exception_2026-09-30.md) — diagnóstico del navegador (Windows 10, Chrome 153) con
- [Traspaso para la auditoría de eficiencia y funcionalidades](traspaso_auditoria_2026-09-29.md) — la sesión que audite rendimiento y funcionalidades.
- [Auditoría de formatos de RUT entre industrias](rut_formatos_2026-09-29.md) — todas las columnas rut y run de los Parquet publicados en docs/outputs/.
- [Revisión del README — 2026-09-29](revision_readme_2026-09-29.md) — Revisión línea por línea del README.md, contrastando cada afirmación contra el
- [El README como pieza de venta — 2026-09-29](readme_como_pieza_de_venta_2026-09-29.md) — La revisión anterior preguntaba ¿es cierto?.
- [Auditoría y medición de eficiencia — 2026-09-29](auditoria_eficiencia_2026-09-29.md) — revisar el proyecto completo; todo es susceptible de auditoría y de
- [Rediseño de interfaz y cambio de nombre (2026-09-28)](rediseno_ui_2026-09-28.md) — Objeto: el sitio estático de docs/ (ahora Sistema de Información Financiera de
- [Serie IFRS CMF para Factoring y Leasing: extracción y publicación automática](factoring_leasing_serie_cmf_plan_2026-09-27.md) — El backfill descarga el histórico del índice CMF para los RUT del catálogo de Factoring/Leasing.
- [Avance del backfill y publicación automática IFRS Factoring/Leasing (2026-09-27)](factoring_leasing_avance_backfill_2026-09-27.md) — La corrida [36340541773](https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile/actions/runs/36340541773) terminó correctamente: 70/70 cierres del índice…
- [Cotejo de muestra — Factoring y Leasing (archivo estructurado CMF vs ficha)](cotejo_muestra_factoring_leasing_2026-09-27.md) — Fecha: 2026-09-27.
- [Auditoría del trabajo de la sesión (2026-09-27)](auditoria_del_trabajo_2026-09-27.md) — Objeto auditado: mis propios cambios de la sesión en la rama

## Sin fecha en el nombre

- [Capacidad y tráfico del sitio](capacidad_trafico.md) — - El sitio y la API son archivos estáticos; DuckDB-Wasm procesa SQL en la pestaña del visitante.
- [Borrador de consulta técnica a CMF: tipo de registro 6 en B.11/B.14](consulta_cmf_registro_tipo6_1835.md) — en pausa; no se requiere una consulta para incorporar los registros tipo 6 como datos de origen conservados y normalizados.
- [Fuentes XML/XBRL por industria (auditoría y oportunidades)](fuentes_xml_por_industria.md) — Fecha de revisión: 2026-09-27
- [Plan de revisión de las industrias restantes](plan_revision_otras_industrias.md) — Continuación del trabajo XML/XBRL.
