# Evaluación de Impeccable (skill de diseño + detector) — 2026-10-21

**Encargo:** revisar <https://github.com/pbakaus/impeccable> y decidir si sirve para este proyecto.
**Estado:** corregido el 2026-10-21 — ver `docs/notas/contraste_y_tipografia_2026-10-21.md`.
**Método:** se leyó el repositorio y se **ejecutó** su detector contra `docs/`. Ninguna cifra de esta
nota sale del README de Impeccable: los conteos son de la corrida y los contrastes se recalcularon
a mano con los colores de `docs/css/app.css`.

---

## 1. Qué es

| Pieza | Qué hace | Qué necesita |
|---|---|---|
| Skill para agentes | 24 comandos (`/impeccable audit`, `polish`, `critique`, `distill`, `bolder`, `optimize`…), escribe `PRODUCT.md`/`DESIGN.md`, hook que analiza cada edición de archivos de UI, modo *live* para iterar variantes en el navegador | Un harness que lea skills: Claude Code, Cursor, Codex, Copilot, Gemini CLI, Grok… |
| Motor / CLI | `npx impeccable detect <archivo-o-url>`: 61 reglas deterministas, **sin LLM y sin API key**; `--json`, `--github`, `--list-rules`, salidas 0 (limpio) / 2 (hallazgos) / 1 (no pudo escanear) | Node sólo para el shim de `npx`; el trabajo lo hace un binario de ~21 MB (9 MB comprimido) por plataforma |
| Configuración | `.impeccable/config.json` con `detector.ignoreRules`, `ignoreFiles`, `ignoreValues`; comentarios `impeccable-disable*` dentro del archivo | — |

Datos de la versión probada: `impeccable@4.7.0` (npm, publicada el 2026-10-19), licencia **Apache-2.0**,
repositorio con ~2.500 commits y actividad diaria. Telemetría: al elegir una dirección visual el skill
consulta una API que registra qué mano se mostró; se apaga con `DO_NOT_TRACK=1`,
`IMPECCABLE_NO_TELEMETRY=1` o `npx impeccable telemetry off`.

---

## 2. Qué se ejecutó y qué devolvió

```bash
DO_NOT_TRACK=1 npx -y impeccable@4.7.0 detect --no-config --json docs/ > scan.json
```

Entorno: Node 22.22.3, Linux x64, **sin Chromium**. Eso deja fuera el escaneo de URL (DOM renderizado)
y el modo live; todo lo demás es el escaneo estático de `docs/index.html` + `docs/css/app.css`.

**Resultado: 100 hallazgos primarios (6 reglas) + 32 avisos (2 reglas).** Salida 2.

| Regla | Nº | Qué mide | Veredicto |
|---|---:|---|---|
| `tiny-text` | 59 | texto bajo 12 px | **Sostiene** (ver §3.2), aunque el número está inflado |
| `undersized-ui-text` | 27 | texto funcional bajo 11 px | **Sostiene** en los de 9–10 px |
| `side-tab` | 9 | borde de color grueso en un costado | Discutible: es la forma de los *callouts* |
| `dark-glow` | 3 | halo de color sin desplazamiento | Discutible: indicadores tipo LED del terminal |
| `overused-font` | 1 | tipografía sobreusada (Inter) | No aplica: es identidad de marca |
| `cramped-padding` | 1 | hijos pegados al borde | **Falso positivo** (ver §3.4) |
| `low-contrast` (aviso) | 22 | WCAG AA | **Sostiene** (ver §3.1); corregido: hoy queda **1**, y luego **0** |
| `undersized-ui-text` (aviso) | 10 | 10 px, versión consultiva | Sostiene |

Aclaración importante sobre el 59: la regla cuenta **coincidencias de CSS aplicadas al HTML**, no
elementos distintos; el HTML repite la misma declaración muchas veces con `line: 0` (sin línea). El
número útil es el del CSS, medido aparte: **143 de las 222 declaraciones `font-size` de `app.css`
(64 %) están bajo 12 px**.

---

## 3. Hallazgos verificados a mano

### 3.1 Contraste: la revisión del 2026-10-20 se quedó corta

La nota `accesibilidad_2026-10-20.md` calculó `--text-muted` sobre `--bg-primary` y `--bg-secondary`,
pero **no sobre `--panel-elevated`**, que en el tema por defecto es más claro que ambos (`#1E1F26`) y
por lo tanto el fondo más exigente. Recalculado sobre las seis paletas:

| Tema | `--text-muted` sobre primary / secondary / **panel** | `--accent-mint` como texto sobre primary / secondary / **panel** |
|---|---|---|
| por defecto | 4,80 / 4,53 / **4,24** ✗ | 5,05 / 4,77 / **4,46** ✗ |
| swissborg | 5,34 / 4,51 / 4,51 | 7,30 / 6,16 / 6,16 |
| bloomberg | 5,01 / 4,54 / 4,54 | 8,95 / 8,10 / 8,10 |
| nord | 5,34 / 4,57 / 4,57 | 7,29 / 6,24 / 6,24 |
| midnight | 4,83 / 4,58 / 4,58 | 5,12 / 4,85 / 4,85 |
| informe | 4,59 / 4,96 / 4,51 | 5,69 / 6,15 / 5,59 |

Sólo falla el tema por defecto, y falla por poco: `--text-muted` en panel elevado queda en 4,24 y
`--accent-mint` como color de texto en 4,46 (AA pide 4,5). El `:hover` de los enlaces de acento
(`#182438`) baja a 4,23. El aviso del detector coincide, con la salvedad de que él mezcla el degradado
de `.info-core-card` (`#1E1F26 → #18191E`) y lo atribuye a veces a un color interpolado.

**Corregido el 2026-10-21** (detalle en `contraste_y_tipografia_2026-10-21.md`): `--text-muted`
pasó a `#828996` y el acento como texto se separó en `--accent-mint-text` / `--accent-blue-text`
(#55A0F8). Las seis paletas quedan sobre 4,5:1 en las cuatro superficies principales.

Candidatos que se midieron para corregirlo (sin cambiar la identidad visual):

- `--text-muted: #828996` → 4,67 en panel y 5,28 en primary (hoy `#7B828E`).
- o bien oscurecer el panel: `--panel-elevated: #1A1B21` → `--text-muted` sube a 4,44 (todavía no
  alcanza) y `#181A1F` recién llega a 4,50. La palanca barata es aclarar el token de texto.
- `--accent-mint` como **texto** en el tema por defecto: `#4A8CF7` da 4,99/4,74 y `--accent-mint-hover`
  (`#60A5FA`, que ya existe) da 6,46. Conviene separar «acento de fondo/borde» de «acento de texto»
  en vez de tocar el token de marca.

### 3.2 Piso tipográfico

| Tamaño | Declaraciones | Uso típico |
|---:|---:|---|
| 9 px | 6 | micro-etiquetas |
| 9,5 px | 9 | abreviaturas de industria (SE, FM, FI) |
| 10 px | 13 | etiquetas de sección, hints de teclado |
| 10,5 px | 28 | metadatos mono, fuentes de tarjeta |
| 11 px | 53 | cuerpo denso de tablas y panel lateral |
| 11,5 px | 34 | cuerpo denso |

El piso de 11 px de la regla `undersized-ui-text` es una convención, no WCAG; pero a 9 px el problema
es real en pantallas de alta densidad y en móvil. Un objetivo razonable para este proyecto no es
«todo a 14 px» (rompería la densidad del terminal), sino **eliminar los 9–10 px** y dejar 11 px como
el mínimo de la interfaz.

### 3.3 Bordes laterales y glows

`app.css` tiene 19 `box-shadow: 0 0 …` (de ellos, varios son anillos `0 0 0 Npx` legítimos) y 9
bordes laterales de color —`border-left: 3px solid` en 8 lugares y dos de 2 px, por ejemplo
`.normativa-evidence` en la línea 3568—. El detector los trata como
«señales de UI generada por IA». Aquí son decisiones de identidad (indicadores LED, bloques de
evidencia). Si se adopta el detector, **estas dos reglas se ignoran por configuración**, no se
reescribe la interfaz para complacerlas.

### 3.4 Falso positivo comprobado

`cramped-padding` sobre `<div class="chat-input-bar">`: la regla tiene `padding: 10px 14px`
(línea 1692) y en el breakpoint angosto `9px max(14px, calc((100% - 1440px)/2)) 11px` (línea 3968).
No hay hijos pegados al borde. Es el recordatorio de que el escaneo estático no ve el layout real.

---

## 4. Encaje con este proyecto

**Lo que sirve hoy, sin LLM y sin instalar nada en el repo:** el detector como *aviso* en
`.github/workflows/web_audit.yml`. `npx impeccable detect --github docs/` imprime una anotación por
hallazgo y no requiere clave. Nunca como paso bloqueante: con 100 hallazgos hoy, y con reglas de
estética discutible, un `exit 2` dejaría el push en rojo para siempre.

**Lo que choca:** tres de las seis reglas disparadas (`overused-font`, `dark-glow`, `side-tab`) son
de estética y están calibradas para landings y SaaS
(Inter, glows de color, gradientes violeta, tarjetas anidadas). Este sitio es un terminal de datos
oscuro con seis paletas deliberadas, 64 % de su tipografía bajo 12 px y una identidad ya definida
(`docs/assets/logo_sif*.svg`, `theme_switcher.js`). Aplicar Impeccable al pie de la letra pelearía
con el sistema de diseño en lugar de mejorarlo.

**La mitad «skill» no aplica en este entorno.** Arena Agent no expone `/impeccable`; para usarla hay
que tener Claude Code, Cursor o Codex instalado en la máquina. Si algún colaborador lo hace, el
instalador escribe `.claude/` o `.cursor/` (versionables) más `.impeccable/` (efímero: capturas,
sesiones, caché; el README trae el bloque de `.gitignore`). Además requiere registrar `PRODUCT.md` y
`DESIGN.md`, que aquí serían duplicados de `docs/notas/` y de la propia `app.css`.

**Cobertura:** el escaneo estático sólo ve `index.html` y `app.css`. La barra lateral, el diccionario,
los modales, las vistas y el ERD se generan por JS (`sidebar.js`, `data_dictionary.js`, `erd_graph.js`),
así que hoy quedan fuera. Un escaneo de URL (`detect https://…`) los cubriría, pero necesita Chrome
instalado y en este entorno no lo hay.

**Coste:** cero dependencias en el repo con `npx` (Node ya se usa en CI para jsdom); 21 MB de binario
en `~/.impeccable/bin` por máquina; ~1,2 s por escaneo de `docs/` una vez cacheado el binario
(la primera corrida incluye la descarga).

---

## 5. Recomendación

1. **Hecho.** Lo de §3.1 está aplicado (tokens de texto separados y piso tipográfico, que luego
   subió a 12 px; ver `contraste_y_tipografia_2026-10-21.md` y `diseno_detector_2026-10-21.md`). El detector pasó de 100 primarios + 32 avisos a
   73 primarios + 0 avisos.
2. **Hecho.** El detector quedó como paso de `web_audit.yml` (job `audit`), **bloqueante**, porque
   el sitio está en cero hallazgos. Ya no hace falta ignorar reglas: se corrigieron en su lugar
   (ver `diseno_detector_2026-10-21.md`).
3. **El skill sigue fuera del repo.** Aporta escritura de `PRODUCT.md`/`DESIGN.md`,
   hooks por edición y estado en `.impeccable/`; en un sitio estático sin build y con el diseño ya
   decidido, el costo (ruido, archivos nuevos, telemetría que hay que apagar) supera el beneficio.
   Si alguien lo quiere para trabajar en su máquina, que sea instalación global y con
   `DO_NOT_TRACK=1`.

No se instaló el skill ni se modificó el sitio: **esta nota es el único archivo nuevo**.

---

## 6. Configuración probada (si se adopta)

Probado sobre una copia de `index.html` + `app.css` fuera del repo. Con este `.impeccable/config.json`:

```json
{
  "detector": {
    "ignoreRules": ["overused-font", "dark-glow", "side-tab", "cramped-padding"]
  }
}
```

el escaneo pasó de 132 resultados (100 primarios + 32 avisos) a **118 (86 primarios + 32 avisos)**, y
seguía saliendo con código 2 (hoy, tras corregir contraste y tipografía: **73 primarios y ningún aviso**,
código 2 igual por `tiny-text`). Es decir: la configuración sirve para apagar las reglas de estética, pero
**no** alcanza para que el paso sea bloqueante mientras queden `tiny-text` y `low-contrast`. El job
tendría que publicar anotaciones con `--github` y terminar en verde siempre (`|| true`), resumiendo el
conteo en un `::notice`, teniendo en cuenta que GitHub muestra como máximo 10 anotaciones por tipo y
paso (el resto queda en el log).

## 7. Reproducir

```bash
# Detector, sólo lectura (no escribe nada en el repo con --no-config)
DO_NOT_TRACK=1 npx -y impeccable@4.7.0 detect --no-config docs/

# Resumen legible por regla
DO_NOT_TRACK=1 npx -y impeccable@4.7.0 detect --no-config --json docs/ \
  | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); \
print(collections.Counter(x["antipattern"] for x in d).most_common())'

# Tipografía bajo 12 px en el CSS
grep -o 'font-size: *[0-9.]*px' docs/css/app.css | sort | uniq -c | sort -rn
```
