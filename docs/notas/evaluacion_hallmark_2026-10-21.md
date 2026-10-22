# Evaluación de Hallmark — 2026-10-21

**Encargo:** revisar <https://github.com/Nutlope/hallmark> y decidir si sirve para este proyecto.
**Método:** se clonó el repositorio y se leyeron `SKILL.md`, `anti-patterns.md` (56 tells con nombre) y
`slop-test.md` (57 compuertas). Su verbo `audit` **no es un binario**: es un protocolo para que un LLM
lea el objetivo y devuelva una lista; se aplicó a mano sobre `docs/`. Los conteos de esta nota son de
esa corrida (grep y medición), no del README.

---

## 1. Qué es

| Pieza | Qué hace | Qué necesita |
|---|---|---|
| Skill para agentes | Cuatro verbos: construir (por defecto), **`audit <target>`** (lista priorizada, no edita), `redesign` (rehace la estructura) y `study` (extrae el «ADN» de una referencia) | Un harness que lea skills (Claude Code, Cursor, Codex) |
| Referencias | 21 temas, 21 macroestructuras, 56 anti-patrones con nombre, 57 compuertas de «slop test» y una autocrítica de seis ejes | — |
| Repositorio | 286 archivos, 18 MB de árbol; el skill instalable son **960 KB de markdown**. Licencia **MIT** | `npx skills add nutlope/hallmark` o copiar la carpeta |

No hay ejecutable, ni tests, ni CI: **no se puede correr como compuerta**. El «audit» es tan
determinista como el LLM que lo aplica. El propio README dice 57 compuertas y el `SKILL.md` dice 58;
el archivo lista 57 numeradas. Es un detalle menor, pero confirma que la numeración no es contrato.

---

## 2. Qué encontró en el sitio

| Tell (su nombre) | Evidencia medida | Severidad | Acción |
|---|---|---|---|
| **`transition: all`** (compuerta 10; arrastra la 14 y la 15) | **22 componentes** declaraban `transition: all`: `.tool-btn`, `.chip`, `.send-btn`, `#chat-input`, `.dl-btn`, `.panel-tab-btn`, `.zoom-btn`… Eso anima también `outline-color` —el anillo de foco de esos 22 aparecía con transición— y cualquier propiedad de layout | major | **Corregido**: listas explícitas por componente (`background-color`, `border-color`, `color`, `box-shadow`, `opacity`, `transform`). 22 → **0**, y `audit_interfaz.py` lo vigila |
| **Animar propiedades de layout** (compuerta 14) | `transition: margin-left 0.25s` en la barra lateral: al plegarse anima `margin-left` de `-320px` a `0` y obliga a recalcular el layout en cada frame | minor | **No corregido**: pasar a `transform` exige sacar la barra del flujo flex (overlay) y cambia el layout; el riesgo supera el beneficio de una animación de 250 ms |
| **Glow / orbe decorativo** (tells de `shadow-glow` y `floating-orb`) | `.info-hero::after`: dos anillos concéntricos con alfa 4 % y 2,5 %, estáticos | minor | **Mantenido**: es decoración quieta de la portada; el tell apunta a orbes animados o glows que compiten con el contenido |

Lo que la lista confirmó que ya estaba bien, medido: **cero** `#000`/`#fff` puros, **cero** degradados
púrpura, **cero** `background-clip: text`, **cero** emojis en el HTML, **cero** `hover: scale`,
`tabular-nums` en las celdas numéricas, `prefers-reduced-motion` global y un solo juego de iconos
(SVG propios).

---

## 3. Encaje con este proyecto

- Su `audit` está pensado para **páginas**: hero, nav, footer, tres tarjetas, CTA, macroestructura.
  La mitad de las compuertas no aplica a un panel de datos con seis pestañas y 90 tablas.
- Sus verbos de construir y `redesign` empujan una identidad nueva entre 21 temas; no es lo que
  buscamos y chocaría con la tipografía y los contrastes ya cerrados.
- Lo aprovechable es su lista de tells de **microinteracción y estados**, que es justo donde encontró
  el único problema real: las transiciones indiscriminadas.
- `study` podría servir si algún día se quiere extraer la estructura de una referencia; hoy no hace
  falta.

---

## 4. Costos y riesgos

- **No es una compuerta**: no da exit codes, no corre en CI, no reemplaza a `impeccable` ni a las
  auditorías propias. Es una opinión experta aplicada a mano.
- Juicio subjetivo: «parece generado por IA» depende del género; su propio `SKILL.md` admite
  excepciones por género.
- 18 MB de repositorio y 960 KB de markdown; no hay motivo para commitearlo.
- MIT y sin telemetría: no ejecuta nada.
- Fuerte sesgo a landing pages y a la estética editorial; un dashboard denso queda fuera de su
  marco principal.

---

## 5. Recomendación

**No instalarlo.** Sirve como auditoría puntual, y eso ya se hizo: una corrección real (22
transiciones), un pendiente anotado (el `margin-left` de la barra) y una decisión de mantener (los
anillos de la portada).

La regla que valía la pena se queda en CI: `scripts/audit_interfaz.py` falla si aparece
`transition: all`. Es barato de comprobar y evita que vuelva el problema, que además de ser un tell
de IA hacía que el foco de teclado no apareciera de inmediato en 22 controles.

---

## 6. Qué cambió

| Archivo | Cambio |
|---|---|
| `docs/css/app.css` | Las 22 declaraciones `transition: all` pasan a listas explícitas de propiedades |
| `scripts/audit_interfaz.py` | Sección 10: falla si vuelve `transition: all` |
| `docs/index.html` | Etiqueta de activos `fl-202610-2430-transiciones` |

Verificación: `audit_interfaz.py` exit 0, DOM **82/82**, `audit_web_full.py` 100 % operativo,
detector de diseño **0**.

---

## 7. Reproducir

```bash
git clone --depth 1 https://github.com/Nutlope/hallmark.git /tmp/hallmark

# no hay comando de auditoría: se leen las reglas y se aplican al objetivo
less /tmp/hallmark/skills/hallmark/references/anti-patterns.md
less /tmp/hallmark/skills/hallmark/references/slop-test.md

# la comprobación que quedó en el proyecto
grep -n "transition: all" docs/css/app.css   # debe salir vacío
python3 scripts/audit_interfaz.py            # sección 10 lo vigila
```
