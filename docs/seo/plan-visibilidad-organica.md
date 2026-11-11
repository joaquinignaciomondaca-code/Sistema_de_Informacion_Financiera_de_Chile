# Plan gratuito de visibilidad orgánica

**SIF Chile, perfil de Joaquín Mondaca y código de tesis**  
Actualizado: 10 de noviembre de 2026

Objetivo: aumentar el descubrimiento entre personas que buscan datos financieros públicos chilenos, carteras CMF, recursos Parquet/SQL o código de pronóstico. Este plan no promete posiciones: Google decide qué rastrea, indexa y muestra. No contempla anuncios, enlaces pagados ni compra de tráfico.

## Arquitectura de descubrimiento

1. **SIF Pages** es el destino para usar el sistema y buscar datos financieros de Chile. Es la propiedad web que se inspecciona en Search Console.
2. **GitHub SIF** aloja código, documentación, API y releases, y debe enlazar claramente a Pages. `github.com` no es propiedad del usuario; la propiedad de Search Console de GitHub Pages no permite enviar URLs de ese dominio.
3. **Perfil de GitHub** funciona como directorio entre autor y proyectos.
4. **Repositorio institucional USM** es la referencia académica estable de la tesis; GitHub complementa la ficha con código.

La ruta de enlaces recomendada es SIF Pages ↔ repo SIF ↔ perfil; perfil ↔ repo de tesis ↔ ficha USM. Evitar insertar enlaces a la tesis en páginas SIF solo para acumular enlaces: son temas distintos.

## Auditoría de partida

- SIF Pages ya tiene portada, tres páginas temáticas (seguros, fondos mutuos y fondos de inversión), sitemap, `robots.txt`, canonical, Open Graph, enlaces internos y marcado `Dataset`.
- Search Console reconoció páginas temáticas en inspecciones en vivo; se aceptó una solicitud de rastreo para seguros. Eso solo pone la URL en cola; no garantiza indexación ni posicionamiento.
- El informe de indexación puede retrasarse respecto de una inspección en vivo. No reenviar repetidamente la misma URL o sitemap: la repetición no acelera el rastreo.
- El perfil ya enlaza SIF y tesis. La tesis tiene resumen, métricas y repo públicos y está registrada en el repositorio institucional USM.
- No tenemos una exportación de consultas e impresiones de Search Console; las frases abajo son hipótesis de intención, no volúmenes ni posiciones observados.

## Grupos de búsqueda a cubrir

Usar luego las consultas reales de Search Console para ajustar esta lista. Las frases son temas, no una instrucción para repetir keywords mecánicamente.

| Activo | Intención | Temas de búsqueda candidatos | Acción útil |
|---|---|---|---|
| Portada SIF | Encontrar y reutilizar datos | datos financieros de Chile; datos abiertos financieros Chile; datos CMF descargables; datos financieros Parquet Chile; consultar datos financieros con SQL | Explicar en texto visible cobertura, fuentes, consulta y descarga. |
| Seguros | Analizar inversiones de aseguradoras | cartera de inversiones compañías de seguros Chile; cartera seguros CMF histórica; inversiones por instrumento | Documentar períodos, columnas, límites y ejemplos ejecutables. |
| Fondos mutuos | Explorar posiciones y EEFF | cartera fondos mutuos Chile CMF; datos históricos fondos mutuos; inversiones por emisor | Explicar unidades, moneda y alcance de cada serie. |
| Fondos de inversión | Analizar cartera y balances | cartera fondos de inversión Chile CMF; datos fondos de inversión descargar; estados financieros | Declarar con precisión qué series son parciales y cuáles continuas. |
| Repo SIF | Encontrar código reutilizable | GitHub datos financieros Chile; Parquet CMF; DuckDB finanzas Chile | Completar About, descripción, website y topics del repo. |
| Perfil | Identificar autor y proyectos | Joaquín Mondaca; Joaquín Mondaca datos; Joaquín Mondaca GitHub | Mantener bio consistente, enlaces claros y proyectos destacados. |
| Tesis | Consultar método y código | pronóstico demanda intermitente retail; forecasting demanda moda; pronóstico jerárquico SKU; ES-GBM retail | Enlazar código y ficha USM; explicar métricas y límites sin exagerar. |

No llamar el SIF “oficial”, “certificado” ni atribuirle respaldo institucional. Es un proyecto independiente que reutiliza publicaciones fuente; citar procedencia y condiciones.

## Plan de acción

### Hecho en esta implementación

- Añadido este plan al repo SIF.
- Reforzados en el perfil enlaces descriptivos hacia la plataforma, repositorio y registro académico.
- Añadido en el README de la tesis el enlace a su ficha USM, distinguiendo destino académico de destino del código.
- Documentada la configuración del About y topics de GitHub, campos que no se modifican editando un archivo del repositorio.
- Añadidos `CITATION.cff` al código de SIF y al repositorio de la tesis para ofrecer una cita descargable en GitHub.
- Publicado un tutorial reproducible de Python y DuckDB enlazado desde la página temática de carteras de seguros.

### Próximos 7 días

1. En Search Console, exportar Rendimiento → Resultados de búsqueda a 28 y 90 días: consulta, página, impresiones, clics, CTR y posición. Guardar la fecha de corte como línea base.
2. Inspeccionar primero la portada de Pages y luego URLs temáticas con impresiones. Pedir rastreo una vez si la versión publicada cambió y es accesible.
3. Revisar una vez el informe de Sitemaps y el estado del sitemap público. El informe de Google puede tardar en refrescarse aunque el archivo sea correcto.
4. Completar en About del repo SIF esta descripción: “Datos financieros públicos de Chile (CMF, Banco Central y SPensiones): catálogos, Parquet y consultas SQL con DuckDB.” Mantener como website la URL de Pages. Topics sugeridos: `chile`, `datos-abiertos`, `datos-financieros`, `cmf`, `banco-central-de-chile`, `parquet`, `duckdb`, `sql`, `open-data`, `financial-data`.
5. Completar About de la tesis: “Código de una tesis de pronóstico jerárquico de demanda intermitente en retail de moda femenina: ES-GBM, series de tiempo y benchmarks en Python.” Si se pone un website, usar la ficha USM y conservar el README como entrada al código. Topics: `demand-forecasting`, `hierarchical-forecasting`, `intermittent-demand`, `retail`, `time-series`, `machine-learning`, `python`.
6. Confirmar que los repos de SIF y tesis estén en los repositorios destacados del perfil. Usar la ficha USM como página de referencia de la tesis cuando el campo website esté libre, sin quitar el link al código.

### Próximos 30 días

- Usar consultas con impresiones para mejorar una página a la vez. Ajustar título y primer párrafo si no responden a la intención; revisar snippet si hay impresiones con CTR bajo; corregir rastreo solo ante un error real.
- Extender la guía de Python/DuckDB con la versión vigente del `data_release` y ejemplos adicionales después de medir qué conjuntos atraen consultas. Evitar páginas genéricas o duplicadas del catálogo.
- Compartir en LinkedIn una demostración concreta con consulta reproducible, procedencia, fecha de corte y enlace Pages; describir SIF como proyecto independiente. No comprar interacciones ni enviar mensajes masivos.
- Presentar código de tesis junto a la ficha USM en espacios académicos o de pronóstico que acepten proyectos; acompañarlo de método y limitaciones, no copiar el mismo anuncio en foros sin contexto.
- Revisar GitHub Insights/Traffic (vistas y clones, cuando estén disponibles) por separado de visitas/clics de Pages.

### Próximos 60–90 días

- Revisar consultas emergentes y priorizar temas con intención clara que el proyecto pueda responder con documentación verificable.
- Buscar menciones editoriales pertinentes en cursos, bibliotecas de datasets, docentes y proyectos de datos abiertos. Facilitar documentación y atribución, sin solicitar enlaces irrelevantes.
- Considerar un release etiquetado para reproducibilidad. Evaluar DOI solo si archivo, licencia, descripción y mantenimiento están resueltos.
- Trimestralmente revisar enlaces, ejemplos, fecha de actualización, límites y consistencia entre web, README, catálogo y datos.

## Medición gratuita

| Frecuencia | Métrica | Herramienta | Uso |
|---|---|---|---|
| Semanal durante cambios | Inspección de URLs prioritarias y errores de sitemap | Search Console | Corregir solo fallos concretos. |
| Mensual | Clics, impresiones, CTR y posición por consulta y página; ventana 28/90 días | Search Console | Distinguir poco descubrimiento de CTR débil. |
| Mensual | Vistas y clones del repo, si GitHub los muestra | GitHub Insights → Traffic | Medir interés por código y documentación. |
| Mensual | Clics y comentarios útiles de una publicación | Analítica de la red social | Repetir formatos que atraen visitas cualificadas. |
| Trimestral | Enlaces entrantes y consultas de marca | Search Console y búsqueda web | Fortalecer referencias relevantes; descartar directorios basura. |

Llevar una tabla con fecha, cambio, métrica y fuente. Esperar al menos 28 días para evaluar una mejora SEO menor; páginas nuevas pueden tardar más.

## Buenas prácticas y límites

- No pagar anuncios, reseñas, enlaces o visitas; no comprar/intercambiar enlaces, usar texto oculto, saturar palabras clave ni hacer spam en comentarios.
- No solicitar indexación de `github.com/...` desde la propiedad de Pages. Facilitar enlaces HTML rastreables desde el perfil y documentación.
- Un sitemap ayuda a descubrir URLs pero no obliga a indexarlas. Una solicitud de rastreo tampoco garantiza inclusión o posición.
- Mantener las páginas rápidas, legibles en móvil y útiles. Documentar fuente, fecha, unidad y límites de los datos y ejemplos.
- En la tesis, alinear métricas con la memoria y no ampliar conclusiones más allá de la muestra y evaluación realizadas.

## Referencias

- [Guía de inicio SEO de Google](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Cómo funciona Google Search](https://developers.google.com/search/docs/fundamentals/how-search-works)
- [Solicitar rastreo de una URL](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)
- [Informe de rendimiento de Search Console](https://support.google.com/webmasters/answer/7576553)
- [Documentación de GitHub Pages](https://docs.github.com/pages)
