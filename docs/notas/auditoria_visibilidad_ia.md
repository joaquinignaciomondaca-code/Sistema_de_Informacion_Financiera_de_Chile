# Informe de Auditoría de Visibilidad IA — SIF Chile

Generado aplicando el skill comunitario `ai-visibility-audit` (wakqasahmed/ai-visibility-skills) — modelo de 6 pilares.

## Resumen Ejecutivo

**Puntuación global: 94/100**

| Pilar | Peso | Puntuación | Estado |
|-------|------|------------|--------|
| 1. Discovery | 20% | 100/100 | ✅ Óptimo |
| 2. Technical Accessibility | 20% | 100/100 | ✅ Óptimo |
| 3. Machine Understanding | 20% | 85/100 | ⚠️ Mejora menor |
| 4. Answer Readiness | 20% | 95/100 | ✅ Óptimo |
| 5. Trust & Authority | 15% | 85/100 | ⚠️ Mejora menor |
| 6. Agent/Action Readiness | 5% | 100/100 | ✅ Óptimo |

**Veredicto:** `YES` — La IA puede descubrir, entender, citar y recomendar este sitio.

## Detalle por Pilar

### Pilar 1: Discovery (20%) — 100/100
- **robots.txt accesible**: Sí — docs/robots.txt existe, permite todo, apunta a sitemap.xml
- **sitemap.xml accesible**: Sí — docs/sitemap.xml existe, enviado a Google Search Console y Bing Webmaster Tools
- **canonical declarado**: Sí — <link rel='canonical'> en index.html
- **indexabilidad**: Sí — No hay noindex, robots.txt permite todo
- **redirecciones limpias**: Sí — GitHub Pages sirve HTTPS directo, sin cadenas

### Pilar 2: Technical Accessibility (20%) — 100/100
- **HTML servido por servidor**: Sí — GitHub Pages sirve HTML estático, sin dependencia de JS para renderizar
- **JSON-LD en HTML crudo**: Sí — <script type='application/ld+json'> presente en index.html
- **Jerarquía de encabezados**: Sí — <h1> presente, estructura lógica
- **Core Web Vitals**: Sí — PageSpeed: FCP 0.3s, LCP 0.3s, CLS 0.023-0.027, TBT 0-20ms
- **Diferencia raw vs hidratado**: No detectada — Todo el contenido crítico está en HTML crudo

### Pilar 3: Machine Understanding (20%) — 85/100
- **JSON-LD Organization/Dataset**: Sí — schema.org/Dataset en index.html con name, description, url, publisher, distribution
- **Grafo de entidades**: Parcial — Catalog.json define relaciones pero no sameAs hacia Wikidata ni @id estables cruzados
- **sameAs autoridad**: No — No hay sameAs hacia páginas de referencia externas
- **JSON-LD visible a no-JS**: Sí — Está en HTML crudo, no depende de hidratación

### Pilar 4: Answer Readiness (20%) — 95/100
- **Respuestas directas extraíbles**: Sí — 159 consultas SQL con resultados ya calculados en /api/v2/resultados/
- **Estructura de encabezados**: Sí — H1, H2 lógicos en index.html
- **Especificidad de contenido**: Sí — Cada objeto tiene descripción, fuente, atribución, corte, filas

### Pilar 5: Trust & Authority (15%) — 85/100
- **Identidad verificable**: Sí — Atribución por fuente (CMF, Banco Central, SPensiones) en cada objeto
- **Atribución de autor**: Parcial — Fuentes institucionales, no autores individuales
- **Transparencia de contacto**: Parcial — No hay página de contacto explícita, pero hay PRIVACIDAD.md y DATA_LICENSE.md
- **Casos de uso cuantificados**: Sí — 19,7 millones de filas, 90 objetos, 159 consultas

### Pilar 6: Agent/Action Readiness (5%) — 100/100
- **Endpoints machine-readable**: Sí — API REST estática con catalog.json, datapackage.json, queries.json, schema/, partitions/
- **Documentación para agentes**: Sí — llms.txt, ai-catalog.json, opensearch.xml
- **Formularios/acciones**: N/A — Sitio de consulta de datos, no tiene formularios de conversión

## Plan de Acción Priorizado

### P0 (Inmediato)
1. Añadir `sameAs` hacia páginas de autoridad (Wikidata, data.gob.cl) en el JSON-LD de `index.html` — mejora Pilar 3.
2. Añadir `@id` estable y resoluble en el JSON-LD para reconciliación de entidades — mejora Pilar 3.

### P1 (Próximo)
3. Añadir página de contacto o autor institucional en `index.html` — mejora Pilar 5.
4. Crear página `/acerca-de/` con información del equipo y metodología — mejora Pilar 5.

### P2 (Mejorar)
5. Considerar `indexnow-instant-indexing` para notificar cambios inmediatos a Bing/Yandex.
6. Añadir `hreflang` si se publica versión en inglés del sitio.

### P3 (Opcional/Experimental)
7. El archivo `ai-catalog.json` ya está publicado en `/.well-known/ai-catalog.json` y `/ai-catalog.json` (protocolo ARD experimental, no reduce el puntaje core).
8. Monitorear `llms.txt` periódicamente a medida que el estándar evoluciona.

## Evidencia Técnica

- **Sitio:** https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile
- **Data release:** 2026-10-30.db40671ee177
- **Objetos publicados:** 90
- **Filas totales:** 19,777,581
- **Consultas SQL:** 159
- **robots.txt:** Permite todo, apunta a sitemap.xml
- **Sitemap:** Enviado a Google Search Console y Bing Webmaster Tools (ambos aceptados)
- **JSON-LD:** schema.org/Dataset válido en HTML crudo
- **llms.txt:** Presente y válido (H1 + descripción del contrato)
- **ai-catalog.json:** 95 recursos registrados (estándar ARD)
- **PageSpeed:** Rendimiento 100, SEO 100, Mejores prácticas 100, Accesibilidad 100

## Guardrails
- Esta auditoría se basa en evidencia observable públicamente (HTML, JSON-LD, sitemap, robots.txt, PageSpeed Insights).
- No se consultaron APIs privadas de motores de IA.
- Protocolos experimentales (llms.txt, ARD) no reducen el puntaje core de 100 puntos.
