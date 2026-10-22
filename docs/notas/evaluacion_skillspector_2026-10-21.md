# Evaluación de SkillSpector — 2026-10-21

**Encargo:** revisar <https://github.com/NVIDIA/SkillSpector> y decidir si sirve para este proyecto.
**Método:** se clonó el repositorio (`--depth 1`), se leyeron `README.md`, `pyproject.toml` y
`uv.lock`, se **instaló de verdad** con las versiones exactas del lock y se ejecutó su batería
contra las skills que ya evaluamos (security-audit, hallmark, ui-ux-pro-max, la skill
`accessibility` de ECC) más un auto-escaneo. Todo en `/tmp` aislado: el repositorio y el HOME
real no se tocaron. Las salidas `--no-llm` (etapa semántica sin claves de proveedor).

---

## 1. Qué es

| Pieza | Qué hace | Qué necesita |
|---|---|---|
| `skillspector scan` | Escanea una skill (directorio, `SKILL.md`, repo Git, URL o zip) antes de instalarla: **71 patrones** en 17 categorías (inyección de prompts, exfiltración, escalada, supply chain, abuso de agencia, envenenamiento de memoria, AST peligroso, taint tracking, YARA, MCP…) | Python ≥3.12 |
| Análisis de dos etapas | Estático + evaluación semántica por LLM opcional (`--no-llm` la desactiva) | API key de un proveedor para la etapa LLM |
| Salidas | Terminal, JSON, Markdown y **SARIF** (para CI/IDE); puntuación 0–100 con recomendación `SAFE`…`DO_NOT_INSTALL` | — |
| Compuertas de CI | `--fail-on-findings` (exit 1 si hay hallazgos) y `--min-coverage N` (exit 1 si la cobertura baja del umbral) | — |
| Consultas CVE | SC4 pregunta a OSV.dev en vivo, con fallback offline declarado | Salida a internet para la consulta en vivo |

Apache 2.0, parte del pipeline **NVIDIA Verified Skills**. Es un **escáner de skills de
terceros**, no del código de este sitio.

---

## 2. Instalación medida

No hay Python 3.12 en este entorno y las rutas normales están cerradas (python.org no resuelve;
los assets de releases de GitHub redirigen a un host bloqueado; `uv python install` falla en el
handshake). Se compiló lo necesario desde el código, todo en `/tmp`:

1. zlib 1.3.1 + OpenSSL 3.5.9 desde `codeload.github.com` → `/tmp/hometools/deps`.
2. **CPython 3.12.15** desde `codeload.github.com/python/cpython` → `/tmp/hometools/py312`.
3. Wheel de SkillSpector **2.12.0** construido desde el clon + **159 paquetes** (121 MB)
   descargados con las versiones exactas de su `uv.lock` → venv de **505 MB**, 163 paquetes.

Dos trampas medidas en el camino, documentadas para no repetirlas: un CPython compilado con
`--without-doc-strings` pierde las firmas de Argument Clinic y langgraph se cae al construir su
grafo (`no signature found for builtin add` — defecto del entorno compilado, no de la skill);
y con las versiones *más nuevas* de PyPI en vez del lock, el mismo grafo también arranca
probado sin problemas con el lock completo. La instalación pesa lo que pesa un entorno
langgraph+boto3+openai: medio gigabyte.

---

## 3. Qué midió sobre las skills reales

| Skill escaneada | Tiempo | Hallazgos | Cobertura | Veredicto del escáner |
|---|---|---|---|---|
| `security-audit` (Cloudflare) | 30 s | 14 (10 HIGH · 3 MEDIUM · 1 LOW) | 75 % | 100 · CRITICAL · `DO_NOT_INSTALL` |
| `hallmark` (Nutlope) | 90 s | 15 (8 HIGH · 7 MEDIUM) | 98,1 % | 100 · CRITICAL · `DO_NOT_INSTALL` |
| `ui-ux-pro-max` (nextlevelbuilder) | 604 s | 298 (5 CRITICAL · 40 HIGH · 253 MEDIUM) | **0 %** | 100 · CRITICAL · `DO_NOT_INSTALL` |
| ECC `accessibility` | 3 s | 0 (SARIF sin resultados) | — | limpio |
| `skill-inspector` (auto-escaneo) | 3 s | 0 | 100 % | **0 · LOW · `SAFE`** |

El auto-escaneo es la pieza que calibra el resto: el motor **sabe** decir `SAFE` cuando una
skill está limpia y se analiza completa. Los otros tres veredictos no son un defecto del motor;
son el resultado de mirar de cerca.

---

## 4. Lo que encontró de verdad y lo que no

**Señal útil — `ui-ux-pro-max`.** Los 5 CRITICAL son código real de red que corre cuando
ejecutas sus scripts: `urllib.request.urlopen(...)` en `scripts/logo/generate.py` y
`scripts/refresh-google-fonts.py` (descarga de logos y fuentes a APIs externas). Junto con
**100** menciones de `npx` (paquetes que se ejecutan vía npm) y 96 referencias a orígenes
externos, eso es exactamente la pregunta que hay que hacerse antes de instalar una skill:
*qué hace esto cuando lo corro*. Con cobertura **0 %** (sus analizadores no pudieron inspeccionar
ninguno de los 631 componentes completos), la puntuación dice «desconocido con llamadas de red»
más que «demostradamente malicioso».

**Falsos positivos por palabras clave — `security-audit` y `hallmark`.** Los patrones disparan
sobre el **texto documental** de las skills: «override system» y «access secrets» en las reglas
de un skill de diseño; `credentials.json` y `/etc/passwd` en la lista de chequeo y en los tests
del validador de Cloudflare (que prueban justo que esas rutas se **rechazan**); «without asking»
en la prosa de los verbos de rediseño. Documentación de seguridad que *describe* ataques leída
como código que los *ejecuta*. Algunos hallazgos son honestos de parte del propio escáner: los
AE1 `static_parse_limit` declaran que un archivo grande (`VALIDATION-AND-REPORTING.md`) superó el
límite de su parser — la herramienta avisa que no vio todo.

**Calibración del veredicto.** Cualquier HIGH o cobertura parcial empuja la puntuación a
100/`DO_NOT_INSTALL`. Es una compuerta, no un diagnóstico: sirve para decidir «mira esto antes
de instalar», y el veredicto final lo pone quien hace el triaje.

**Compuertas de CI, probadas.** `--fail-on-findings` → exit 1 con hallazgos (hallmark) y exit 0
limpio (skill-inspector); `--min-coverage 99` → exit 1 sobre una cobertura real de 98,1 %.
SARIF 2.1.0 bien formado.

---

## 5. Encaje en este proyecto

El sitio no publica skills de agentes, así que SkillSpector **no entra al CI de la web**: para el
código de `docs/` ya está impeccable, y para auditar el sitio, security-audit-skill. El lugar de
SkillSpector es el paso que hicimos cuatro veces en estas notas: **escanear la skill antes de
instalarla**. En ese hueco aporta lo que los otros dos no miran — el contenido de una skill de
tercero (scripts con red, patrones de inyección, superficie de ejecución) — y hoy habría
adelantado, antes del clon, el hallazgo de que ui-ux-pro-max trae código que hace llamadas de
red.

**Recomendación: usarlo, pero como compuerta con triaje, no como veredicto.** Antes de
`skills add` de cualquier skill ajena: `skillspector scan <repo> --no-llm` y leer los hallazgos,
sobre todo los de red y ejecución, tolerando falsos positivos en documentación. Si algún día
este repo empaqueta una skill propia, recién ahí tiene sentido en CI con `--fail-on-findings`.

---

## 6. Lo que no se pudo medir

- **Etapa semántica por LLM** (la segunda etapa de dos): sin claves de proveedor, sólo se probó
  `--no-llm`. Puede que la semántica descarte los falsos positivos de palabras clave — o que no.
- **Consultas OSV.dev en vivo**: sin salida a ese host; aplica su fallback offline declarado.
- **Ruta Docker** del README: no probada (se instaló desde el código fuente).

---

## 7. Cambios en el repositorio

Ninguno en el sitio ni en la automatización: sólo esta nota. La instalación completa quedó en
`/tmp` (venv de 505 MB, reports JSON/SARIF en `/tmp/ss-reports/`).

---

## 8. Reproducir

```bash
# con Python 3.12 disponible:
python3.12 -m venv /tmp/venv-skillspector
/tmp/venv-skillspector/bin/pip install git+https://github.com/NVIDIA/SkillSpector.git  # o el wheel del clon

export HOME=/tmp/hometools   # aislamiento
/tmp/venv-skillspector/bin/skillspector scan <skill> --no-llm --format terminal
/tmp/venv-skillspector/bin/skillspector scan <skill> --no-llm --format json --output reporte.json
/tmp/venv-skillspector/bin/skillspector scan <skill> --no-llm --fail-on-findings   # compuerta CI
```
