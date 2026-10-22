# Diseño: cierre de los hallazgos del detector — 2026-10-21

**Punto de partida:** 73 hallazgos primarios tras la corrección de contraste y tipografía
(`contraste_y_tipografia_2026-10-21.md`).
**Resultado:** **0** hallazgos.

| Regla | Antes | Después | Qué se hizo |
|---|---:|---:|---|
| `tiny-text` | 59 | **0** | Piso tipográfico de 12 px en toda la hoja (11 y 11,5 → 12) |
| `side-tab` | 9 | **0** | Barra lateral gruesa → borde completo de 1 px con el mismo tinte |
| `dark-glow` | 3 | **0** | Halos difusos → anillo nítido de 2 px; halos de botones → elevación neutra |
| `cramped-padding` | 1 | **0** | `padding` con `max()/calc()` → `padding` literal + centrado por `max-width` |
| `overused-font` | 1 | **0** | Inter → Schibsted Grotesk (ver §4) |

---

## 1. Qué dispara cada regla (medido, no supuesto)

Antes de tocar nada se probaron variantes en un banco de pruebas aislado. Esto es lo que el
detector mira realmente:

| Prueba | Resultado |
|---|---|
| `border-left: 3px solid` **sin** fondo ni radio | no se marca |
| `border-left: 3px solid` + fondo | se marca (`side-tab`) |
| `border-left: 2px solid` + `border-radius` | se marca |
| `border: 1px solid` en los cuatro lados | no se marca |
| `box-shadow: 0 0 8px color` | se marca (`dark-glow`) |
| `box-shadow: 0 0 0 3px color` (anillo) | **también** se marca |
| `border: 2px solid rgba(color, .22)` | no se marca |
| `outline: 2px solid rgba(color, .22)` | no se marca |
| `font-size: 11px` / `11.5px` | se marca (`tiny-text`) |
| `font-size: 12px` / `12.5px` | no se marca |

Dos conclusiones prácticas: **el anillo de foco con `box-shadow: 0 0 0 2px` también cuenta como
halo**, y **el filete lateral sólo molesta cuando hay fondo de por medio**, que es exactamente el
patrón de tarjeta de plantilla.

## 2. Los cambios, regla por regla

### 2.1 `tiny-text` (59 → 0)

Se subió **todo** el texto de 11 y 11,5 px a 12 px: 143 declaraciones en `app.css` (109 + 34) y
cinco tamaños en línea (`index.html`, `chat_terminal.js`, `data_dictionary.js`). La rampa ahora
empieza en 12 px y no hay ningún valor menor en la hoja:

```
12 × 165   12,5 × 23   13 × 9   13,5 × 4   14 × 8   14,5 · 15 · 16 · 17 · 18 · 19 · 22 · 23 · 24
```

**Coste asumido:** la interfaz gana ~9 % de ancho de texto en insignias, pestañas y chips. Se eligió
la coherencia (un solo piso para el HTML estático y para todo lo que generan `sidebar.js`,
`data_dictionary.js`, `erd_graph.js`…) frente a subir sólo lo que ve el escáner estático, que habría
dejado un chip a 12 px en la cabecera y el mismo chip a 11 px en la barra lateral.

### 2.2 `side-tab` (9 → 0)

Nueve tarjetas llevaban `border-left` de 2–3 px con fondo y esquina redondeada. Pasaron a **borde
completo de 1 px** con el mismo color y tinte:

| Selector | Antes | Ahora |
|---|---|---|
| `.normativa-evidence` | 3 px acento | 1 px acento al 38 %, radio 6 |
| `.normativa-review-summary` | 3 px ámbar, radio `0 7 7 0` | 1 px ámbar, radio 7 |
| `.dl-context-card` | 1 px azul + 3 px acento | 1 px acento al 45 % (una sola línea) |
| `.dl-item-warn` | 3 px ámbar | 1 px ámbar al 50 % + tinte + radio 6 |
| `.tree-tier-aviso` | 2 px ámbar, radio `0 4 4 0` | 1 px ámbar al 45 %, radio 4 |
| `.erd-scope-note` | 2 px ámbar, radio `0 4 4 0` | 1 px ámbar al 45 %, radio 4 |
| `.dict-scope-box` | 3 px ámbar al 75 % | 1 px ámbar al 50 %, radio 5 |
| `.scope-banner` | 3 px ámbar, radio `0 6 6 0` | 1 px ámbar al 50 %, radio 6 |
| `.dl-tier-aviso` | 3 px ámbar, radio `0 6 6 0` | 1 px ámbar al 50 %, radio 6 |

También `.dict-warning-box`, que el escáner no marcaba pero era el mismo patrón. Se conservaron los
tres filetes que **no** son tarjetas: `.tree-row.selected`, `.tree-circular` (indicadores de estado)
y `.dict-role-tag.pk`.

### 2.3 `dark-glow` (3 → 0)

Nueve puntos de estado (`.badge.live::before`, `.context-chip::before`, `.freshness-dot`,
`.normativa-status-dot`, `.normativa-event-dot`, `.theme-item-indicator`, `.sql-engine-dot` y sus
variantes `ready`/`failed`) cambiaron el halo por `outline: 2px solid rgba(…, 0.22–0.38)`. El
`outline` sigue el `border-radius`, no ocupa espacio y no dispara la regla.

Los siete halos que quedaban fuera de los puntos también se fueron, por coherencia con la propia
recomendación de la regla («elevación neutra»):

- foco de `.sidebar-search-box input` y `#chat-input` → `box-shadow: 0 0 0 2px var(--accent-mint-dim)`
  (anillo nítido; además mejora la visibilidad del foco);
- `.send-btn` y su `:hover` → `0 1px 3px` / `0 2px 8px` en negro translúcido;
- `.dl-btn-primary:hover` y `.info-core-btn:hover` → `0 2px 8px rgba(0,0,0,.3)`;
- `.sidebar-resizer:hover` → sólo el fondo de acento.

Como `--accent-green` y `--accent-red` son colores hex, `rgba(var(--accent-green), .35)` habría sido
CSS inválido: se añadieron los canales `--accent-green-rgb` y `--accent-red-rgb` a las seis paletas.

### 2.4 `cramped-padding` (1 → 0)

No era un problema de relleno. El inset del breakpoint angosto se calculaba con

```css
padding: 9px max(14px, calc((100% - 1440px) / 2)) 11px;
```

y **el escáner no interpreta `max()`**: lee el relleno horizontal como 0 y concluye que los hijos
están pegados al borde. Se comprobó aislando el caso: con el mismo `padding` en literal la regla
desaparece; con 40 px de relleno seguía apareciendo.

La solución mantiene el comportamiento responsive sin cálculo opaco:

```css
.chat-input-bar { padding: 9px 14px 11px; }
.chat-input-bar > * { width: 100%; max-width: 1440px; margin-inline: auto; }
```

En pantallas de más de 1440 px el contenido queda igual de centrado que antes.

## 3. Verificación

| Comprobación | Resultado |
|---|---|
| Detector (`detect --no-config docs/`) | 73 → **0** |
| `font-size` mínimo en la hoja | 12,0 px (222 declaraciones) |
| `border-left` de 2 px o más | 3 (los indicadores de estado, a propósito) |
| `box-shadow: 0 0 <blur>` | 0 |
| Llaves balanceadas · variables sin definir · propiedades repetidas | 768/768 · ninguna · ninguna |
| `audit_interfaz.py` | INTERFAZ COHERENTE |
| `audit_navigation.py` | 13 familias, 90 tablas, 90 opciones |
| `audit_web_full.py` | TODAS LAS SECCIONES 100 % OPERATIVAS |

**Lo que no se pudo verificar aquí:** no hay navegador en el entorno, así que el efecto visual del
piso de 12 px (posibles quiebres de línea en pestañas e insignias) y de los bordes completos hay que
mirarlo en la vista previa. Todo son cambios de 1 px y de color; ningún cambio de estructura.

## 4. La tipografía (1 → 0)

El último hallazgo señalaba a **Inter** como una de las familias más repetidas de la web. Antes de
elegir se midió qué acepta la regla, porque no es una lista fija:

| Familia probada | Resultado |
|---|---|
| Inter · Instrument Sans · Instrument Serif | marcadas |
| Schibsted Grotesk · Archivo · Sora · Manrope · Newsreader · Bricolage Grotesque · Georgia | aceptadas |

Se eligió **Schibsted Grotesk**: grotesca de origen editorial (diseñada para cabeceras de prensa),
con formas más cerradas y un ancho algo menor que Inter, que en un panel de datos se traduce en
filas más compactas sin perder legibilidad a 12 px. JetBrains Mono sigue a cargo del código y de
las cifras alineadas, así que la retícula numérica no cambia.

- `docs/index.html`: la hoja de Google Fonts pasa a `Schibsted+Grotesk:wght@400;500;600;700` (mismo
  origen y mismo `preconnect`, sin dependencias nuevas).
- `docs/css/app.css`: `--font-sans: 'Schibsted Grotesk', 'Inter', …`. Inter queda como respaldo si
  la webfont no carga; el lockup del logo es SVG con su propia tipografía y no se toca.

**A vigilar en la vista previa:** al cambiar de familia cambian las métricas. Los puntos donde podría
notarse son las pestañas del panel (seis, con letras ajustadas) y las insignias de una línea; los
anchos son flexibles y hay reglas de compresión, pero conviene mirarlo en 1280 y 1920 px.

## 5. Lo que el detector no ve: el texto dibujado en canvas

El escáner sólo lee HTML y CSS. Los dos lienzos del sitio —`chart_renderer.js` (gráfico de barras de
los resultados SQL) y `erd_graph.js` (mapa relacional)— se quedaron fuera de la primera pasada y
seguían con la tipografía anterior y con tamaños de 9,5 a 11 px:

| Archivo | Antes | Ahora |
|---|---|---|
| `chart_renderer.js` | `Inter`; título 11, eje 10, etiquetas 9,5, tooltip 10,5 | `'Schibsted Grotesk'`; 12 en los cuatro |
| `erd_graph.js` | `Inter` y `sans-serif`; título 11, filas 10, insignia 10, avisos 10 | `'Schibsted Grotesk'`; 12 en todos |

El aumento de tamaño obligó a ajustar la geometría, que estaba calculada para letra más chica:

- **Gráfico:** el margen izquierdo pasa de 65 a 74 px para que quepan las cifras del eje; el tooltip
  crece de 24 a 26 px de alto; y el recorte de las etiquetas del eje X ahora **se mide contra el ancho
  real de la barra** en vez de cortar siempre a 8 caracteres, que a 12 px dejaba etiquetas pisadas
  cuando hay muchas barras.
- **ERD:** la insignia de filas pasa de 16 a 18 px de alto y los avisos de cardinalidad de 16 a 18 con
  su línea base corrida 1 px; la leyenda de medidas usa 17 px de interlineado. Las filas de columnas
  mantienen 16 px de paso: 5 columnas llegan a 131 px y la tarjeta más baja mide 148, así que no
  desbordan. Los `ctx.font` están verificados con `node --check`, pero **el resultado visual hay que
  mirarlo en la vista previa**.

## 6. Verificación final

```bash
DO_NOT_TRACK=1 npx -y impeccable@4.7.0 detect --no-config docs/
# 24 files scanned with regex matching only (.css, .js) … exit 0
```

Cero hallazgos. Para descartar que el escáner se hubiera apagado, se inyectó a propósito un
`font-size: 9px` en una copia fuera del repositorio y la regla volvió a dispararse
(`undersized-ui-text`), así que la compuerta sigue viva.

---

## 7. La compuerta en CI

El detector quedó montado en `.github/workflows/web_audit.yml` como paso «Diseño: anti-patrones de
interfaz», dentro del job `audit` (corre en cada push a `main` que toque `docs/**` y en cada PR).

Cómo está construido, y por qué:

| Decisión | Motivo |
|---|---|
| Versión fijada (`impeccable@4.7.0`) | El detector es determinista; una regla nueva sólo entra cuando alguien sube esta línea a mano |
| `--no-config` | Sin configuración local: hoy no hay reglas silenciadas y así nadie puede apagarlas por accidente desde el repo |
| Anotaciones generadas desde `--json` | `--github` no emite nada en la 4.7.0 (probado con `GITHUB_ACTIONS=true`). El script arma un `::error` por hallazgo, con archivo y línea |
| Precondición `docs/index.html` + `docs/css/app.css` | Una ruta inexistente **no** es error para el detector: devuelve 0 con cero archivos escaneados. Sin la comprobación, mover `docs/` apagaría la compuerta en silencio |
| Reintento ante código 1 | El código 1 es «no pudo escanear» (red, binario), no un hallazgo: se reintenta una vez y, si persiste, falla con mensaje explícito |
| JSON ilegible = fallo del paso | Un error de parseo no debe leerse como «sin hallazgos» |
| Caché de `~/.impeccable/bin` y `~/.npm` | Evita bajar 9 MB de npm y 21 MB de binario en cada corrida |
| Artefactos en `$RUNNER_TEMP` | `diseno.json` no queda como archivo sin versionar en la raíz del repo |

**Simulacro completo del paso** (no sólo de los comandos sueltos): se extrajo el bloque `run:` del
YAML y se ejecutó en cuatro escenarios.

| Escenario | Salida | Código |
|---|---|---:|
| `docs/` limpio | `::notice` «0 hallazgo(s)» | 0 |
| un `font-size: 9px` inyectado | `::error` con archivo y regla, más el resumen | 2 |
| `docs/` ausente | `::error` «falta docs/index.html» | 1 |
| JSON con forma inesperada | `::error` «no se pudo leer el JSON» | 1 |

Y el YAML se validó con un parser (`yaml.safe_load`): 16 pasos en el job `audit`, el nuevo en la
posición 5. Ojo con el detalle que rompió el primer intento: un `name:` con dos puntos
(`Diseño: anti-patrones…`) invalida el YAML si no va entre comillas.
