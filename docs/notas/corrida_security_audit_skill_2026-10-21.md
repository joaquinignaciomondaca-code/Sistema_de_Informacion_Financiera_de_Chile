# Corrida completa de `security-audit-skill` — 2026-10-21

**Encargo:** ejecutar de verdad la skill `cloudflare/security-audit-skill` sobre el sitio, no
sólo evaluarla. **Alcance:** sitio desplegado (`docs/`), respaldos por CDN, despliegue y CI.
**Perfil:** `quick`, corrida acotada. **Fuente:** `d3dac31`, árbol limpio.
**Contrato:** los artefactos (`findings.json`, `coverage-ledger.json`) pasaron los dos
validadores de la skill: `PASS: 4 findings valid` y `PASS: 6 coverage units valid`.

Esta corrida **no cambia** lo que decía `evaluacion_security_audit_skill_2026-10-21.md`: la
metodología de la skill ya se había seguido a mano. Aquí se corrió su protocolo completo con
sus propios formatos y validadores, para dejar la evidencia en el formato que la herramienta
exige.

---

## 1. Estado de la corrida: incompleta

La skill exige que cada candidato lo refute un verificador distinto del cazador (fase 3), y
que la cobertura la cierre un crítico independiente (fase 2). **Aquí no hubo subagentes**: la
corrida la hizo un solo agente. Por eso `run-metadata.json` declara
`run_status: incomplete` con la razón `single_agent_no_independent_verifier`, y la cobertura
se reporta como parcial, no como garantía. Es la diferencia entre «revisé todo» y «revisé lo
que alcancé».

---

## 2. Cobertura: 6 unidades, todas cerradas con evidencia de fuente

| Unidad | Frontera | Clase |
|---|---|---|
| Feed CMF → DOM | `escapeHtml` + allowlist de URL | DOM-based XSS |
| `#sql=` → consola | `textarea` + guardia de solo lectura | DOM-based XSS |
| Interfaz desplegada | `frame-ancestors` / `X-Frame-Options` | Clickjacking |
| Motor vendorizado | SHA-256 + versión fijada | Mutable build inputs |
| Workflows de PR | `contents: read`, sin `pull_request_target` | Untrusted code en workflow privilegiado |
| Consola SQL | `sql_guard` | Injection |

El `coverage-ledger.json` lleva las referencias canónicas por unidad (superficie, frontera,
subclase y bloque de ataque). No se cubrieron clases de memoria/binarios, nube, RPC,
aislamiento de datos ni IPC: el producto no las expone. Quien ejecute una corrida futura puede
partir de este ledger en vez de partir de cero.

---

## 3. Resultados

| Veredicto | Cantidad |
|---|---|
| `confirmed` | **0** |
| `needs_validation` | **0** |
| `rejected` | **4** |

Los cuatro rechazos quedan registrados en el `findings.json` para que una corrida futura no
repita la misma afirmación sin evidencia nueva:

1. **`xss-feed-normativa`** — todo campo del feed pasa por `escapeHtml`
   (`normativa_monitor.js:48`) y las URL exigen `https://www.cmfchile.cl/` (`:8`).
2. **`xss-hash-sql`** — el SQL del fragmento termina en `input.value` (`chat_terminal.js:125`)
   y en un aviso escapado (`:131`); no hay sumidero HTML.
3. **`clickjacking-sin-accion`** — sin cuentas ni escritura en servidor no hay acción con
   efecto de seguridad que redirigir. Las cabeceras se añadieron igual como endurecimiento.
4. **`malware-duckdb-1.29.2`** — el aviso GHSA-w62p-hx95-gf2c (alto) afecta a
   `@duckdb/duckdb-wasm` 1.29.2; el sitio ejecuta **1.28.0** y sus bytes están fijados por
   huella en `manifiesto.json`.

---

## 4. Endurecimiento registrado (no son hallazgos)

La skill separa explícitamente los huecos de defensa de las vulnerabilidades. Quedaron
anotados, sin cambiar su categoría:

- **CSP completa pendiente**: hoy aplica `frame-ancestors 'none'; object-src 'none';
  base-uri 'self'`. Una política de `script-src` necesita validación en navegador (manejadores
  inline, dos CDN, `blob:` para el worker, `wasm-unsafe-eval`).
- **Actions por etiqueta mayor**: una etiqueta puede moverse; fijarlas por SHA es el siguiente
  escalón si el repositorio gana colaboradores externos.
- **Respaldo por CDN del motor**: los endpoints `+esm` construyen el bundle en la petición y no
  admiten `integrity`; sólo se usan si falla la copia local.
- **Google Fonts**: origen de terceros que recibe la IP del visitante; self-hostear es mejora
  de privacidad, no vulnerabilidad.

---

## 5. Lo que no se pudo medir

- **Sin verificación independiente**: la fase 3 de la skill no se cumplió (un solo agente), y
  por lo mismo tampoco el crítico de cobertura de la fase 2.
- **Sin navegador**: las rutas DOM se verificaron por fuente y con las auditorías del
  repositorio (`audit_interfaz_dom.js` 82/82; `audit_xss_celdas.js` 8/8), no con un motor real.
- **Sin salida a Internet salvo GitHub, npm y PyPI**: no se observaron las cabeceras del
  despliegue ni el contenido que sirven los CDN.
- **Sin ejecutar código del objetivo**: los validadores de la skill son propios de la skill; el
  código del sitio se revisó leyéndolo. La skill recomienda un sandbox con límites de recursos
  para confirmar resultados; sin esa capacidad, ningún candidato se declaró confirmado.

---

## 6. Evidencia y reproducción

Artefactos versionados junto a esta nota:

- `corrida_security_audit_skill_2026-10-21_findings.json` — los 4 rechazos con su traza.
- `corrida_security_audit_skill_2026-10-21_cobertura.json` — las 6 unidades cubiertas.
- `corrida_security_audit_skill_2026-10-21_metadatos.json` — commit, perfil y estado incompleto.

```bash
# validadores de la skill (copiados del clon de la herramienta)
node validate-findings.cjs   corrida_security_audit_skill_2026-10-21_findings.json
node validate-coverage-ledger.cjs corrida_security_audit_skill_2026-10-21_cobertura.json
```

Los validadores comprueban formato y consistencia del ledger, no la veracidad de los hallazgos:
son la gramática de la skill, no su criterio.
