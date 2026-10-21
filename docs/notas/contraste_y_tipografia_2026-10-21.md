# Contraste y piso tipográfico — 2026-10-21

> **Actualización, mismo día:** el piso tipográfico subió después de **11 a 12 px** y la
> tipografía pasó de Inter a Schibsted Grotesk, al cerrar los hallazgos que quedaban
> (`diseno_detector_2026-10-21.md`). Los contrastes de esta nota siguen vigentes.

**Encargo:** aplicar las correcciones que salieron de la evaluación de Impeccable
(`docs/notas/evaluacion_impeccable_2026-10-21.md`).
**Alcance:** sólo `docs/`. Sin datos, sin pipelines, sin dependencias nuevas.

---

## 1. Qué se cambió

| Archivo | Cambio |
|---|---|
| `docs/css/app.css` | Token `--text-muted` del tema por defecto y del tema Informe; dos tokens nuevos de texto (`--accent-mint-text`, `--accent-blue-text`); 56 declaraciones `font-size` subidas al piso de 11 px; el tinte de `.dict-role-tag.pk` bajó de 20 % a 12 % |
| `docs/index.html` | La etiqueta «Chile» de 10 a 11 px; los 20 activos locales pasan a la etiqueta de versión `fl-202610-2250-a11y-contraste` |
| `docs/js/data_dictionary.js` | El rótulo «Interpretación Económica / Financiera» de 9,5 a 11 px |

### 1.1 Los tokens de texto

El acento (`--accent-mint`) se usa para fondos, bordes **y texto**. Como fondo y como borde está
bien, pero como texto no alcanzaba AA: `#3B82F6` mide 4,46:1 sobre el panel elevado y 3,70:1 sobre
las insignias que llevan su propio tinte al 15 %. En vez de aclarar el acento de marca (que habría
cambiado botones, focos y bordes), se separó el uso:

```css
--accent-mint:      #3B82F6;  /* fondo, borde, foco */
--accent-mint-text: #55A0F8;  /* sólo color de TEXTO: 6,07:1 sobre el panel y 5,03:1 sobre el tinte */
```

Lo mismo con el azul semántico (`--accent-blue` → `--accent-blue-text`), que también se usaba como
color de texto en nueve reglas. Los otros cinco temas ya cumplían con su acento tal cual, así que
allí el token apunta al acento (`var(--accent-mint)`), salvo el tema claro, que necesitó un verde
apenas más oscuro (`#0A664C`).

`--text-muted` subió de `#7B828E` a `#828996` en el tema por defecto (4,24 → 4,67 sobre el panel) y
de `#6C7079` a `#666A73` en el tema Informe (4,30 → 4,69 sobre la barra lateral). Los otros cuatro
temas no se tocaron: ya estaban sobre 4,5 en sus superficies principales.

### 1.2 El piso tipográfico

Había 56 declaraciones bajo 11 px (6 de 9 px, 9 de 9,5 px, 13 de 10 px y 28 de 10,5 px) y dos
tamaños en línea (HTML y JS). Todas subieron a 11 px. La rampa queda:

```
11 px × 109   11,5 × 34   12 × 22   12,5 × 23   13 × 9   13,5 × 4   14 × 8   14,5 · 15 · 16 · 17 · 18 · 19 · 22 · 23 · 24
```

**Bajo 11 px: 0 declaraciones.** Debajo de 12 px siguen 143, las mismas de antes: no se adoptó la
recomendación de 14 px para texto de cuerpo porque este es un panel de datos denso y la densidad es
deliberada. El mínimo de la interfaz ahora es 11 px.

---

## 2. Cómo se verificó

### 2.1 Detector de Impeccable

```bash
DO_NOT_TRACK=1 npx -y impeccable@4.7.0 detect --no-config --json docs/
```

| Regla | Antes | Después |
|---|---:|---:|
| `low-contrast` (aviso, WCAG AA) | 22 | **0** |
| `undersized-ui-text` | 37 | **0** |
| `tiny-text` (bajo 12 px) | 59 | 59 |
| `side-tab` / `dark-glow` / `overused-font` | 13 | 13 |
| `cramped-padding` | 1 | 1 |
| **Total** | **132** | **73** |

Los 59 de `tiny-text` son el mismo conjunto de texto que ahora mide 11–11,5 px en vez de 10–11,5:
la regla pide 12 px como mínimo y aquí se decidió 11. Los otros 14 se dejan a propósito (bordes
laterales, halos del terminal, Inter) o son el falso positivo de `.chat-input-bar` ya documentado.

### 2.2 Contraste recalculado en las seis paletas

Peor caso de cada token sobre las cuatro superficies grandes (`--bg-primary`, `--bg-secondary`,
`--panel-elevated`, `--bg-sidebar`), y para el acento, además, sobre su propio tinte al 8–15 %:

| Tema | `--text-muted` | `--accent-mint-text` | `--accent-blue-text` |
|---|---:|---:|---:|
| por defecto | 4,67 | 5,03 | 6,07 |
| SwissBorg | 4,51 | 4,67 | 6,16 |
| Bloomberg | 4,54 | 6,20 | 8,10 |
| Nord | 4,57 | 4,61 | 4,64 |
| Midnight | 4,58 | 6,32 | 8,33 |
| Informe | 4,69 | 4,89 | 6,14 |

Todo ≥ 4,5:1 (WCAG AA para texto normal).

### 2.3 Auditorías del repositorio

| Comprobación | Resultado |
|---|---|
| `python scripts/audit_interfaz.py` | INTERFAZ COHERENTE |
| `python scripts/audit_navigation.py` | 13 familias, 90 tablas, 90 opciones |
| `python scripts/audit_web_full.py` (venv con pyarrow 21) | TODAS LAS SECCIONES 100 % OPERATIVAS |

También se comprobó a mano: llaves balanceadas, ninguna variable `var(--…)` sin definir, ningún
bloque con propiedades repetidas y una sola etiqueta de versión para los 20 activos locales.

---

## 3. Lo que queda pendiente (a propósito)

- **`--bg-tertiary`** (#22242B) sigue dando 4,40:1 con `--text-muted` en el tema por defecto, y
  3,66–4,01 en los demás. No se corrigió porque ninguna regla del CSS combina texto apagado con ese
  fondo (revisión bloque por bloque de este cambio, no una auditoría automática); si algún día
  aparece un caso anidado, la salida es subir ese texto a `--text-secondary` (6,4:1) y no cambiar el
  token global.
- **Tintes de acento al 20 % o más** quedaban bajo AA en SwissBorg y Nord; el único uso
  (`.dict-role-tag.pk`) bajó al 12 %, que es el mismo valor de `.dv-scroll-tag`. Si se agrega un
  tinte nuevo más cargado con texto encima, hay que usar `--accent-mint-text`.
- **Guardián automático: resuelto después.** El detector de Impeccable corre ahora como paso
  bloqueante de `web_audit.yml` (`diseno_detector_2026-10-21.md` §6), así que una regresión de
  contraste o de tamaño falla el PR.

## 4. Reproducir

```bash
# Contraste de los tokens nuevos (sin navegador)
python3 - <<'PY'
def lin(c):
    c = c/255
    return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
def L(h):
    h=h.lstrip('#'); r,g,b=[int(h[i:i+2],16) for i in (0,2,4)]
    return .2126*lin(r)+.7152*lin(g)+.0722*lin(b)
def ratio(a,b):
    la,lb=L(a),L(b); hi,lo=max(la,lb),min(la,lb); return (hi+.05)/(lo+.05)
print(ratio("#828996","#1E1F26"))   # 4.67  --text-muted sobre el panel
print(ratio("#55A0F8","#222E45"))   # 5.03  acento de texto sobre su tinte al 15 %
PY

# Ningún tamaño bajo el piso
grep -o 'font-size: *[0-9.]*px' docs/css/app.css | awk -F: '{gsub(/[^0-9.]/,"",$2); if ($2+0<11) print}'
```
