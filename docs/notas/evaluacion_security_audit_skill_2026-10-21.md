# Evaluación de Cloudflare `security-audit-skill` — 2026-10-21

**Encargo:** revisar <https://github.com/cloudflare/security-audit-skill> y decidir si sirve para este proyecto.
**Método:** se clonó el repositorio (575 KB, **22 archivos**) y se leyeron `SKILL.md`, `CLIENT-SIDE.md`,
`SUPPLY-CHAIN-AND-RELEASE.md` y `VALIDATION-AND-REPORTING.md`. Sus dos validadores se corrieron con
`node --test`: **65 pruebas, 65 en verde**. No se instaló la skill. Después se aplicó a mano su método
—fuente, sumidero, frontera y resultado— sobre `docs/` y sobre las 17 workflows de `.github/`.

---

## 1. Qué es

| Pieza | Qué hace | Qué necesita |
|---|---|---|
| Skill de auditoría | Seis fases: reconocimiento y ledger de cobertura, caza por unidades, validación adversarial de candidatos, salida estructurada, verificación independiente y reporte | Un agente con subagentes y un sandbox del sistema operativo para ejecutar código del objetivo |
| Validadores | `validate-findings.cjs` y `validate-coverage-ledger.cjs`: sin dependencias, con esquema JSON y **65 pruebas** | Node |
| Origen | Es la skill con la que Cloudflare armó su harness de descubrimiento de vulnerabilidades; el repositorio es el punto de partida de un solo repo | — |

Licencia **MIT**. No es un escáner: es un **protocolo de auditoría para un LLM**, con reglas duras sobre
qué se puede afirmar. La más importante, y la que ordenó este trabajo: *«un candidato sin principal,
recurso o resultado de seguridad concreto no es un hallazgo confirmado»*. Su propio README avisa que
una sola pasada encuentra más o menos la mitad de lo que encuentran varias.

---

## 2. Resultado de aplicarlo: ninguna vulnerabilidad confirmada

Se recorrieron las superficies que la skill marca para un sitio estático, buscando siempre fuente
controlable → sumidero que ejecute o divulgue, y un afectado distinto del atacante.

| Superficie | Qué se comprobó | Resultado |
|---|---|---|
| Sumideros DOM | **24** asignaciones dinámicas a `innerHTML`/`outerHTML`/`insertAdjacentHTML` en el JS propio; todas las que reciben datos los escapan (`escapeHtml`, `dvEscapar`) o son constantes | Sin hallazgo |
| Monitor normativo | Es el único contenido de terceros que llega al DOM: **28** usos de `escapeHtml` y allowlist de URL `/^https:\/\/www\.cmfchile\.cl\//i` para los enlaces; modelo y confianza también escapados | Sin hallazgo |
| Consultas guardadas | `localStorage` → `innerHTML` en `chat_terminal.js`: `q.title` y `q.sql` pasan por `escapeHtml`; los chips, también | Sin hallazgo |
| Enlace `#sql=` | El texto va a un `textarea` y a un mensaje escapado; no hay sumidero HTML. Ejecuta SQL de solo lectura contra datos públicos y lo anuncia antes de correr | Sin hallazgo |
| Celdas y alias hostiles | `audit_xss_celdas.js`: **8** comprobaciones, incluido el SQL del enlace compartido | Sin hallazgo |
| Mensajería y workers | **2** `postMessage`, ambos del *plumbing* interno del worker de DuckDB; sin `addEventListener("message")` que acepte datos externos; sin service worker | Sin hallazgo |
| Ejecución dinámica | Cero `eval` y cero `new Function` en el código propio | Sin hallazgo |
| Enlaces externos | Todos con `rel="noopener noreferrer"` salvo uno con `noopener` (constantes del módulo de créditos; se completó igual) | Sin hallazgo |
| Workflows | Sin `pull_request_target`; `contents: write` sólo en los *cron* de datos; Pages usa `id-token: write` con `contents: read` | Sin hallazgo |
| Secretos | `audit_secretos.py`, ya en CI | Sin hallazgo |

**Cero vulnerabilidades confirmadas.** El sitio es estático, no tiene cuentas, sesiones ni escrituras:
casi todas las fronteras que la skill persigue no existen aquí. Lo que sí había eran huecos de
endurecimiento, que es otra categoría —y la propia skill pide no disfrazarlos de hallazgo.

---

## 3. Huecos de endurecimiento corregidos

| Hueco | Evidencia | Acción |
|---|---|---|
| **El despliegue no declaraba ni una cabecera de seguridad** | `vercel.json` sólo tenía `Cache-Control: no-store` para los Parquet: sin `nosniff`, sin política de referrer, sin `frame-ancestors`, sin `Permissions-Policy`, sin COOP | **Corregido**: seis cabeceras y una CSP mínima en las **dos** copias de `vercel.json` (raíz y `docs/`), con compuerta en `audit_interfaz.py` |
| **El motor vendorizado no tenía huella** | `docs/vendor/duckdb/` ejecuta desde el propio origen **18.061.915 bytes** de `.wasm` y 265.771 del worker. Sin hash registrado, un reemplazo silencioso es invisible: el sitio sigue funcionando y nadie mira los bytes | **Corregido**: `manifiesto.json` con versión, tamaño y SHA-256 de los tres archivos, `scripts/audit_vendor_duckdb.py` y paso nuevo en CI |

**La CSP es deliberadamente mínima**: `frame-ancestors 'none'; object-src 'none'; base-uri 'self'`.
Son tres directivas que no pueden romper el render y cubren clickjacking e inyección de base/objetos.
Una CSP completa de `script-src` tiene que permitir los manejadores `onclick` inline, dos CDN de
respaldo, `blob:` para el worker de prueba y `wasm-unsafe-eval`; sin un navegador donde validarla, una
política mal escrita dejaría la terminal muerta en producción. Queda como paso siguiente, con la
política escrita en esta nota, no aplicada a ciegas.

---

## 4. Riesgos aceptados, con su razón

| Riesgo | Por qué no se corrigió |
|---|---|
| **Respaldo por CDN del motor** | `duckdb_client.js` importa `cdn.jsdelivr.net/.../+esm` o `esm.sh/...` sólo si la copia local falla. Esos endpoints **construyen el bundle en la petición**, así que ni fijando la versión son inmutables, y un `import()` dinámico no admite `integrity`. Se mantiene porque el camino normal es el archivo local (ya con huella) y porque el respaldo cubre el caso de que la copia local no esté; se documenta en vez de fingir que está resuelto |
| **Actions fijadas por etiqueta mayor** (`actions/checkout@v4`, etc.) | Una etiqueta se puede mover y ejecutaría con el `GITHUB_TOKEN` del job. Son acciones oficiales y el costo de fijar 20 SHA con su mantenimiento supera el riesgo actual; queda anotado como el siguiente escalón si el repositorio gana colaboradores externos |
| **Cabeceras sólo en Vercel** | GitHub Pages no permite cabeceras propias. Las seis cabeceras aplican al despliegue de Vercel; el día que Pages sea el host principal, no habrá CSP ni `nosniff`. Es una limitación del host, no del repositorio |
| **Google Fonts** | Es un origen de terceros que recibe la IP del visitante y sirve CSS. No hay fuga de datos del sitio; self-hostear las fuentes es una mejora de privacidad y de latencia, fuera del alcance de esta revisión |

---

## 5. Encaje y recomendación

**No instalarla.** Igual que las tres anteriores, su unidad de valor es el flujo de trabajo del agente,
no una compuerta: no trae nada que se pueda correr contra este repositorio y fallar en CI. Pero a
diferencia de Hallmark y ECC, su checklist sí encontró cosas que las compuertas existentes no miraban:
cabeceras del despliegue e integridad del binario vendorizado. Se toma como **checklist manual**, y lo
que encontró ya está en CI para que no vuelva.

---

## 6. Cambios aplicados

| Archivo | Cambio |
|---|---|
| `vercel.json` y `docs/vercel.json` | `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options: DENY`, CSP mínima, `Permissions-Policy` y `Cross-Origin-Opener-Policy`; se conserva la regla de `no-store` de los Parquet |
| `docs/vendor/duckdb/manifiesto.json` | Versión 1.28.0, tamaño y SHA-256 de los tres archivos del motor |
| `scripts/audit_vendor_duckdb.py` | Verifica huellas, archivos no declarados y que `DUCKDB_VERSION` coincida; `--actualizar` reescribe el manifiesto de forma consciente |
| `docs/vendor/duckdb/README.md` | Procedimiento de actualización con el manifiesto |
| `scripts/audit_interfaz.py` | Sección 11: las dos copias de `vercel.json` idénticas, seis cabeceras y las tres directivas de la CSP. Además, el conteo de archivos con etiqueta de caché dejó de estar escrito a mano |
| `.github/workflows/web_audit.yml` | Paso «El motor DuckDB vendorizado es el que se revisó (huellas)» |
| `docs/js/creditos.js` | `rel="noopener noreferrer"` en el enlace que faltaba |

Etiqueta de activos: `fl-202610-2450-cabeceras`.

---

## 7. Verificación

| Comprobación | Resultado |
|---|---|
| `python3 scripts/audit_interfaz.py` | exit 0 · sección 11 en `[OK]` |
| `python3 scripts/audit_vendor_duckdb.py` | `Motor DuckDB 1.28.0: 3 archivos con la huella esperada` |
| **Prueba negativa del manifiesto** (hash alterado a `000…`) | `FALLA: duckdb-browser.mjs: SHA-256 … no coincide` · exit 1 |
| **Prueba negativa de cabeceras** (sin `X-Frame-Options`) | `RESULTADO: 2 PROBLEMA(S)` · exit 1 |
| `node scripts/audit_xss_celdas.js` | todas las comprobaciones OK |
| `node scripts/audit_duckdb_client.js` · `audit_arranque_motor.js` · `audit_sql_guard.js` | exit 0 en las tres |
| `node scripts/audit_interfaz_dom.js` | **82/82** |
| Validadores de la skill (`node --test`) | 65/65 |

---

## 8. Reproducir

```bash
git clone --depth 1 https://github.com/cloudflare/security-audit-skill.git /tmp/secaudit
cd /tmp/secaudit/skills/security-audit && node --test validate-findings.test.cjs \
  validate-coverage-ledger.test.cjs                      # 65 pruebas de sus validadores

python3 scripts/audit_vendor_duckdb.py                   # huellas del motor
python3 scripts/audit_interfaz.py                        # incluye la sección de cabeceras
grep -rn 'innerHTML' docs/js/*.js | grep -v '\.min\.'    # sumideros revisados a mano
```
