# Prueba de instalación de las cinco herramientas — 2026-10-21

**Encargo:** instalar y probar todo lo que se venía evaluando en notas.
**Método:** cada instalación se hizo con `HOME` aislado en `/tmp/hometools` (incluidos
`XDG_CONFIG_HOME`, `XDG_DATA_HOME` y la caché de npm), sin tocar `~/.claude` real ni el
repositorio. Versiones fijadas: `impeccable@4.7.0`, `ecc-universal@2.2.3`, `skills@latest`.
Se midió tiempo, tamaño y archivos antes y después, y se ejecutó lo que cada paquete trae
como ejecutable. Lo que sólo es texto no se puede correr: se dice.

---

## 1. Qué pasó con cada una

| Herramienta | Instalación | Huella | Qué se ejecutó de verdad | Resultado |
|---|---|---|---|---|
| **impeccable** | No hace falta: `npx` puntual, como en CI | ~0 (caché temporal) | `detect --no-config --json docs/` | **0 hallazgos** sobre el árbol actual |
| **ui-ux-pro-max** | No hace falta: el clon ya trae `search.py` sin dependencias | — | 6 consultas en 3 dominios | Sólo responde en inglés; en español da 0 resultados |
| **hallmark** | `skills add` → copia a `~/.claude/skills/hallmark` | 107 archivos, 960 KB | Nada: no hay ejecutable | Es markdown; su «audit» lo aplica un LLM |
| **security-audit-skill** | `skills add` → copia a `~/.claude/skills/security-audit` | 20 archivos, 352 KB | `node --test` de sus dos validadores | **65/65** pruebas en verde desde la copia instalada |
| **ECC** | `ecc install --target claude --profile minimal` | **4,7 MB y 530 archivos** en `~/.claude` | `doctor`, `status`, `list-installed`, `consult`, `uninstall` | Instala y desinstala en ≈1 s; deja 68 agentes, 94 comandos y 50 skills |

---

## 2. ECC, con números

El perfil **`minimal`** —el más chico de los siete— resolvió **400 operaciones de copia** en el
plan y las ejecutó en **≈1 segundo**. El resultado en el `HOME` aislado:

| Medida | Antes | Después de `minimal` |
|---|---|---|
| Archivos en `~/.claude` | 127 (las dos skills) | **530** |
| Tamaño | 1,3 MB | **4,7 MB** |
| Contenido | 2 skills | 68 agentes, 94 comandos, 50 skills, 122 archivos de reglas, 4 scripts |

Además de los agentes y reglas, escribe `settings.json` (una sola clave,
`includeCoAuthoredBy`), `mcp-configs/mcp-servers.json` (10 KB de plantillas), `plugin.json`,
`marketplace.json` y un estado propio en `ecc/`. `doctor`, `status` y `list-installed` funcionan
sin un harness instalado y devuelven JSON con el estado del despliegue.

`consult "accessibility audit"` acierta al recomendar la skill de accesibilidad y, con la misma
confianza, ofrece *prediction markets* por coincidencia difusa: el recomendador no distingue
«parecido» de «útil».

**Desinstalar funciona:** `uninstall` también tarda ≈1 segundo y deja **129 archivos** —quitó lo
suyo y respetó las dos skills que estaban antes—, más su propio estado. Instalación y remoción
son reversibles; el costo es el espacio y el tiempo de revisar 400 archivos ajenos, no un daño
permanente.

---

## 3. ui-ux-pro-max: el límite es el idioma

El buscador existe y funciona, pero su base está en inglés y no traduce la consulta:

| Consulta | Resultado |
|---|---|
| «tabla de datos densidad y jerarquía» (ux) | **0 resultados**; sugiere `dev, table, tables` |
| «interfaz de datos densa» (typography) | **0 resultados**; sugiere `interfaces, inter` |
| «serie de tiempo financiera» (chart) | **0 resultados**; sugiere `series, financial, finance` |
| «dashboard data table density» (ux) | 2 resultados: desborde de tablas en móvil, acciones masivas |
| «dense financial interface» (typography) | 1 resultado: IBM Plex Sans para datos financieros |
| «financial time series» (chart) | 2 resultados: candlestick y línea, con notas de accesibilidad |

Es útil como biblioteca de referencia —y honesto cuando no encuentra—, pero para un proyecto
cuya interfaz está en español hay que consultarlo en inglés.

---

## 4. Lo que esta prueba cambia en el veredicto

Nada. Confirma con números lo que decían las notas:

- **Sólo dos de las cinco traen algo ejecutable**: impeccable (un detector determinista) y los
  validadores de la skill de Cloudflare (que validan *registros de auditoría*, no código fuente).
- **Dos son contenido puro** (hallmark y ui-ux-pro-max): su valor es el texto, y el texto ya se
  leyó.
- **ECC es un entorno completo**: 400 archivos para el perfil mínimo, 68 agentes, configuración
  MCP y un estado propio. Instalarlo en el repositorio habría metido ese peso en el flujo de
  trabajo a cambio de una skill de accesibilidad que ya se aplicó a mano.

La compuerta que sí protege el sitio sigue siendo la misma: el detector de impeccable fijado en
CI, más las auditorías deterministas del repositorio.

---

## 5. Limpieza y reproducción

Todo quedó en `/tmp/hometools` (81 MB, incluida la caché de npm). El repositorio no cambió y
`~/.claude` real no existe: no se instaló nada en el entorno del usuario.

```bash
# skills
env HOME=/tmp/hometools npx -y skills@latest add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit -g -y -a claude-code
env HOME=/tmp/hometools npx -y skills@latest add https://github.com/Nutlope/hallmark -g -y -a claude-code

# ECC: plan, instalación mínima, estado y reversa
env HOME=/tmp/hometools npx -y ecc-universal@2.2.3 install --target claude --profile minimal --dry-run --json
env HOME=/tmp/hometools npx -y ecc-universal@2.2.3 install --target claude --profile minimal --json
env HOME=/tmp/hometools npx -y ecc-universal@2.2.3 doctor --target claude --json
env HOME=/tmp/hometools npx -y ecc-universal@2.2.3 uninstall --target claude --json

# detector
npx -y impeccable@4.7.0 detect --no-config --json docs/
```
