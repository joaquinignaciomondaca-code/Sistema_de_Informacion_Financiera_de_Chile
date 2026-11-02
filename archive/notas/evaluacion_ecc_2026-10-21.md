# Evaluación de ECC — 2026-10-21

**Encargo:** revisar <https://github.com/affaan-m/ECC> y decidir si sirve para este proyecto.
**Método:** se clonó el repositorio (`--depth 1`, 103 MB, **4.627 archivos**) y se leyeron `README.md`,
`package.json`, la tabla de conteos, el listado de `skills/` y `agents/`, y sus dos skills de accesibilidad.
Después se aplicó la skill `accessibility` (WCAG 2.2 AA) a mano sobre `docs/`: dos pasadas de grep y
`audit_interfaz_dom.js` antes y después. No se instaló nada y no se ejecutó su instalador.

---

## 1. Qué es

| Pieza | Qué hace | Qué necesita |
|---|---|---|
| Harness de agentes | Ciclo `plan → test → implement → review → verify → remember → improve`: **71 agentes**, **311 skills**, **97 shims** de comandos, hooks y memoria | Instalarse en el harness que uses |
| Instalador | `npx ecc-universal@2.2.3 setup` / `install --guided`; copia agentes, skills, comandos, hooks y configuración MCP en **siete** harnesses (Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, Copilot) | Node ≥18 y permisos de escritura sobre la configuración del harness |
| AgentShield | Escaneo de prompts, hooks, servidores MCP, permisos y secretos | Su propio runtime |
| Skills de accesibilidad | `accessibility` (WCAG 2.2 AA, multi-plataforma web/iOS/Android) y `frontend-a11y` (React/Next) | Sólo un LLM que las lea |

Licencia **MIT**, pero el modelo es OSS + **ECC Pro** (GitHub App para repos privados, desde 19 USD por
asiento al mes) y patrocinios (CodeRabbit, Greptile, Kimi, Itô, SerpApi). El repositorio no es una
herramienta de verificación: **no trae un binario que audite este sitio**. Lo que trae es un entorno
de trabajo completo para agentes.

---

## 2. Qué encontró en el sitio

La skill `accessibility` es genérica y correcta: tamaño de objetivo (24 px AA / 44 px AAA), apariencia
del foco, `aria-live`, y una tabla cruzada con lo equivalente en iOS y Android. Aplicada a mano, marcó
dos huecos reales; ambos estaban en tablas que ya generaban HTML a mano.

| Hueco | Evidencia medida | Severidad | Acción |
|---|---|---|---|
| **Encabezados de tabla que sólo responden al ratón** | El explorador de datos y los resultados de la consola SQL generaban `<th onclick="…sortTable(…)">`: sin `tabindex`, sin `<button>`, sin `scope="col"` y sin `aria-sort`. El único indicador de orden era el glifo `▲`/`▼`, invisible para un lector de pantalla; con teclado no se podía ordenar ninguna de las dos tablas | major | **Corregido**: el control pasa a ser un `<button type="button" class="th-sort-btn">` dentro del `<th scope="col">`; `aria-sort` alterna `ascending`/`descending`/`none` en cada ordenamiento; el botón hereda tipografía y color y tiene `:focus-visible` propio |
| **El esquema del mapa no era un diálogo** | `#schema-modal` era un `div` con `position: absolute` y clase `.visible`: sin `role="dialog"`, sin nombre accesible, sin foco al abrir, sin Escape y sin devolver el foco al cerrar. El único cierre era el botón `×`, sin `aria-label` | major | **Corregido**: `role="dialog"` + `aria-labelledby="modal-table-name"`; al abrir el foco va al botón de cerrar; **Escape** cierra; al cerrar el foco vuelve al elemento que lo tenía; el `×` declara `aria-label="Cerrar el esquema de la tabla"` |

Lo que la misma lista confirmó que ya estaba bien, medido: `aria-live="polite"` en el chat, la pregunta,
las descargas y la normativa; `role="status"` o `role="alert"` en **11** sitios; `aria-expanded` en la
barra lateral y en la cabecera; enlace «Saltar al contenido» con `<main tabindex="-1">`; y
`prefers-reduced-motion` global.

---

## 3. Encaje con este proyecto

ECC resuelve un problema que aquí no existe: **orquestar agentes**. Este repositorio ya tiene su
propia disciplina —17 pasos de auditoría en `web_audit.yml`, cuatro auditorías node/python, detector de
diseño y compuertas en `audit_interfaz.py`— y no necesita un segundo ciclo de vida ni una memoria
externa. Sus 311 skills son, en su mayoría, de otros stacks (React/Next, Django, Laravel, cripto,
seguridad); las de frontend no aplican a JavaScript sin framework y las de accesibilidad sí, pero son
**texto**, no código: se leen una vez y se convierten en checklist.

Instalarlo tendría un costo concreto y medible: **103 MB y 4.627 archivos**, hooks que se ejecutan en
cada herramienta, memoria persistente y configuración MCP reescrita en siete harnesses. Es un runtime
ajeno dentro del flujo de trabajo, y su valor aquí se agota en el par de páginas que ya se leyeron.

---

## 4. Recomendación

**No instalarlo.** El repositorio es serio y está bien mantenido, pero su unidad de valor es el harness,
no la auditoría: no aporta ninguna compuerta que se pueda poner en CI. Se toma su skill `accessibility`
como **checklist manual** —igual que se hizo con Hallmark— y se queda lo que encontró, que era real y
está corregido. `frontend-a11y` se descarta porque asume React/Next.

---

## 5. Cambios aplicados

| Archivo | Cambio |
|---|---|
| `docs/js/data_viewer.js` | `<th scope="col" aria-sort>` + botón `.th-sort-btn`; `updateSortIcons` mantiene `aria-sort` en las tres columnas |
| `docs/js/chat_terminal.js` | Mismo patrón en los resultados SQL; `sortTable` actualiza `aria-sort`; cierre del esquema con Escape y retorno de foco (`cerrarEsquema`) |
| `docs/js/erd_graph.js` | Al abrir el esquema guarda el foco previo y lo lleva al botón de cerrar; el botón propio del modal usa `cerrarEsquema` |
| `docs/index.html` | `#schema-modal` con `role="dialog"`, `aria-labelledby` y `aria-label` en el `×` |
| `docs/css/app.css` | `.th-sort-btn` (hereda tipografía, sin borde ni fondo) y su `:focus-visible` |
| `scripts/audit_interfaz.py` | Cuatro comprobaciones nuevas en la sección 10: botón + `scope` + `aria-sort` en ambas tablas, `role="dialog"` con nombre y cierre por Escape con retorno de foco |

**Lo que no se hizo, y por qué:**

- **No hay trampa de foco** en el esquema: es un popup no modal (`position: absolute`, sin velo), así
  que atrapar el foco sería incorrecto. Se resuelve lo que pide AA: nombre, foco al abrir, Escape y
  retorno.
- **Tamaño de objetivo**: la fila del árbol mide 28 px y supera el mínimo AA de 24 px, pero no se midió
  en navegador; queda como pendiente, no como afirmación.
- **No se instaló ECC** ni se copiaron sus hooks, memoria o agentes.

---

## 6. Verificación

| Comprobación | Resultado |
|---|---|
| `python scripts/audit_interfaz.py` | exit 0 · sección 10 con las cuatro comprobaciones nuevas en `[OK]` |
| `node scripts/audit_interfaz_dom.js` | **82/82** |
| `python scripts/audit_web_full.py` | 100 % de las secciones |
| `python scripts/audit_navigation.py` | catálogo normalizado en 14 sectores |
| `python scripts/audit_rut_formatos.py` | 769 archivos, **0** problemas |
| `node scripts/audit_duckdb_client.js` · `audit_arranque_motor.js` · `audit_sql_guard.js` · `audit_xss_celdas.js` | exit 0 en las cuatro |
| `node --check` de los tres archivos tocados | sintaxis OK |

Etiqueta de activos: `fl-202610-2440-encabezados`.

---

## 7. Reproducir

```bash
git clone --depth 1 https://github.com/affaan-m/ECC.git /tmp/ecc
grep -rl "aria-sort\|role=\"dialog\"" docs/js docs/index.html   # los dos huecos corregidos
python scripts/audit_interfaz.py                                # incluye las compuertas nuevas
npm install --no-save --no-audit --no-fund jsdom                # sólo para la prueba de DOM
node scripts/audit_interfaz_dom.js
```
