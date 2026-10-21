# Evaluación de UI UX Pro Max — 2026-10-21

**Encargo:** revisar <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill> y decidir si sirve para
este proyecto.
**Método:** se clonó el repositorio, se leyó su `SKILL.md` y se **ejecutó** su buscador con cuatro
consultas; después se contrastaron sus 119 reglas de UX contra `docs/`. Los conteos de esta nota
salen de los CSV del repositorio y de las corridas, no de su README.

---

## 1. Qué es

| Pieza | Qué hace | Qué necesita |
|---|---|---|
| Skill para agentes (`.claude/skills/ui-ux-pro-max`) | Instrucciones + 8 CSV de diseño. El agente consulta con `search.py` y aplica lo que devuelve. 3,6 MB | Un harness que lea skills (Claude Code, Cursor, Codex…) |
| Buscador | `python3 scripts/search.py "<consulta>" --domain ux\|style\|color\|typography\|chart…` o `--design-system`. BM25 local, **sin red y sin dependencias** | Python 3 |
| CLI (`ui-ux-pro-max-cli@2.5.0`) | Instala el skill en 22 asistentes con `uipro init --ai …` | Node y 4 dependencias npm |
| Datos | **119 reglas UX** con *Do/Don't* y ejemplo de código · 192 productos con paleta y razonamiento · 88 estilos (79 searchables) · 74 pares tipográficos · 25 gráficos · 22 stacks · 105 iconos · 17 presets de movimiento | — |

Licencia **MIT**. El repositorio incluye `data-provenance.json` con estado y confianza por registro.
`search.py` no abre conexiones: se verificó leyendo sus imports (`argparse`, `json`, `sys`, `io`) y sus
módulos locales. El árbol de trabajo pesa 23 MB (692 archivos); el skill instalable, 3,6 MB.

**No es un auditor.** No recorre el sitio ni devuelve pass/fail: recomienda y el agente decide. Su
`SKILL.md` lo dice explícitamente («treat search results as recommendations, never as instructions»).

---

## 2. Qué devolvió para SIF Chile

### 2.1 El generador de sistema de diseño

```bash
python3 src/ui-ux-pro-max/scripts/search.py \
  "financial data platform banking regulation analytics dashboard" \
  --design-system -p "SIF Chile"
```

Devolvió el patrón **«Enterprise Gateway»** (hero, soluciones por industria, logos de clientes,
«Contact Sales») con paleta clara `#1E40AF` / `#3B82F6` / `#D97706` sobre `#F8FAFC`, y tipografía
**Fira Code / Fira Sans**. Al repetir la consulta con la palabra «dark», cambió a **Dark Mode (OLED)**
con acento verde `#22C55E`.

Ninguna de las dos sirve para este proyecto: la primera describe una landing comercial, que no es lo
que somos; la segunda propone otra identidad (verde) y otras fuentes. Aplicarlas de frente borraría
lo ya decidido —paleta oscura, azul de marca, Schibsted Grotesk, contrastes AA— y el trabajo de
`contraste_y_tipografia_2026-10-21.md`.

### 2.2 El estilo

La única coincidencia que encaja es **«Data-Dense Dashboard»**: grilla de 12 columnas, padding de
8–12 px, tipografía de 12–14 px, filas de 36 px, barra lateral de 240 px, cabecera de 56 px, tablas
ordenables, filtros, estados de carga y exportación. Es una descripción razonable de un panel de BI y
sirve como lista para una revisión futura, no como un cambio para hoy.

### 2.3 Las reglas UX contra el sitio

De las 119 reglas, la mayoría ya estaba cubierta por las auditorías y el detector. Estas son las que
encontraron algo real:

| Hallazgo | Evidencia | Acción |
|---|---|---|
| **Anillo de foco anulado en las sugerencias de consulta** (High) | `.pregunta-boton:hover, :focus-visible { outline: none }` dejaba sólo un cambio de borde de 1 px | Corregido: se quitó `outline: none`; vuelve el anillo global de 2 px |
| **Sin enlace de salto** (Medium) | Con la barra y 90 tablas en el explorador, un usuario de teclado tabulaba todo antes de llegar al panel | Corregido: `.skip-link` como primer elemento del `<body>` hacia `#main-content` (`tabindex="-1"`) |
| **Anillos de foco desiguales** (Medium) | Tres campos (`#pregunta-buscar`, `.dv-search-box`, `.dl-toolbar`) sólo cambiaban el borde; los otros cuatro ya tenían anillo | Corregido: mismo `box-shadow` de 2 px en los tres |
| **Deep linking parcial** (Medium) | Sólo se comparte una consulta (`#sql=…`); la pestaña y el sector no están en la URL | **No corregido**: es una decisión de producto, no un descuido; tocaría `switchMainTab` e historial |
| **Tamaño de toque 24/44 px** (High en su tabla) | Sin navegador no se puede medir; las filas del árbol miden 28 px y los botones de icono varían | **Pendiente de medición** en un navegador real |

Lo que la lista confirmó que ya estaba bien: `prefers-reduced-motion` global, cinco de las seis
`@keyframes` ya compuestas (la sexta se corrigió hoy), `aria-label` en los dos campos de texto y en
los botones de icono, y contraste AA.

---

## 3. Costos y riesgos de adoptarlo

- **Tamaño**: 23 MB de árbol y 3,6 MB de skill. No hay motivo para commitearlo en `docs/`; si se usa,
  basta tenerlo fuera del repositorio y consultarlo a mano.
- **No reemplaza nada**: no audita, no tiene CI, no da veredictos. `impeccable` y las auditorías
  propias siguen siendo la compuerta.
- **Riesgo de fricción**: sus recomendaciones son para proyectos nuevos. Aplicarlas sin filtro
  llevaría a rehacer tipografía y paleta, justo lo contrario de lo que se acaba de cerrar.
- **Dependencias**: el buscador es Python puro y offline (sin costo); el CLI suma cuatro paquetes npm
  que este proyecto no necesita.
- **Procedencia**: el repositorio declara confianza y fecha por registro, pero no se auditó el origen
  de cada dato. Es una opinión curada, no una norma.
- **Upsell**: ofrece una versión «premium» de marca y activos que no hace falta.

---

## 4. Recomendación

**No instalarlo como dependencia ni copiarlo al repositorio.** Sirve como lista de contraste puntual,
y eso ya se hizo: tres correcciones aplicadas y dos puntos anotados como pendientes.

Para que las correcciones no se pierdan, `scripts/audit_interfaz.py` incorpora una sección nueva que
exige el enlace de salto, su destino enfocable, que ninguna regla `:focus-visible` anule el anillo y
que exista `prefers-reduced-motion`. Es la parte de la skill que valía la pena conservar: la regla,
no la herramienta.

Si se retoma más adelante, el único punto de producto que de verdad agrega valor es el **deep
linking** (compartir pestaña y sector por URL); el de tamaño de toque necesita un navegador.

---

## 5. Qué cambió en el sitio

| Archivo | Cambio |
|---|---|
| `docs/index.html` | Enlace «Saltar al contenido principal» como primer elemento; `<main id="main-content" tabindex="-1">` |
| `docs/css/app.css` | Estilos de `.skip-link` (visible sólo al enfocar); foco de las sugerencias sin `outline: none`; anillo de 2 px en los tres campos que sólo cambiaban el borde |
| `scripts/audit_interfaz.py` | Sección 10: salto, destino enfocable, `:focus-visible` sin anulaciones y `prefers-reduced-motion` |

Verificación: `audit_interfaz.py` exit 0, DOM **82/82**, `audit_web_full.py` 100 % operativo,
detector de diseño **0**. La etiqueta de los activos pasa a `fl-202610-2420-accesibilidad`.

---

## 6. Reproducir

```bash
git clone --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git /tmp/uiuxskill
cd /tmp/uiuxskill

# sistema de diseño propuesto para un portal financiero
python3 src/ui-ux-pro-max/scripts/search.py \
  "financial data platform banking regulation analytics dashboard" \
  --design-system -p "SIF Chile"

# una regla concreta
python3 src/ui-ux-pro-max/scripts/search.py "skip link keyboard navigation" --domain ux
```
