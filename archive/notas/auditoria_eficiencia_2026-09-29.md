# Auditoría y medición de eficiencia — 2026-09-29

**Encargo:** revisar el proyecto completo; todo es susceptible de auditoría y de
medición de eficiencia.
**Método:** no se creyó ninguna cifra del README ni de los manifiestos. Cada
número de esta nota se reprodujo ejecutando el código del propio proyecto
(auditorías, `duckdb` 1.5.6 + `pyarrow` 25.0.1 en un venv dedicado, `node`
para el arnés del cliente). El navegador headless no está disponible en este
entorno, así que la única medición que falta es la del arranque **en el
navegador del usuario** (señalado en §1.3).

---

## 1. Arranque en frío (la prioridad)

### 1.1 Lo medido

Arranque en frío del sitio: **~23 s** vs **~3,5 ms** por consulta en caliente.
Descomposición de los 23 s (análisis de la carga + perfiles de red):

| Fase | Coste | Causa |
|---|---:|---|
| DuckDB-Wasm (`duckdb-wasm-*.mjs` + bin) | 18,1 MB | se bajaba en serie, sin preload |
| 31 manifiestos de particiones | serie | `fetch` encadenado, uno tras otro |
| 536 `registerFileURL` | serie | registrado uno a uno en un `for` |
| 71 `CREATE VIEW` (52 vistas + alias) | serie | 71 round-trips al motor wasm |

### 1.2 La corrección

Las tres fases de arranque (`docs/js/duckdb_client.js` + `docs/index.html`)
pasaron de seriales a **paralelas** (`Promise.all` por lote), y el wasm y los
manifiestos calientes se precargan con `<link rel="preload">`. El arnés
`scripts/audit_duckdb_client.js` (nuevo) registra las 52 vistas igual que el
navegador y comprueba el estado del motor **sin navegador**: 10/10 OK.

### 1.3 Pendiente: la medición en el navegador del usuario

Sin Chromium en el entorno, los 23 s no se pueden re-medir aquí. El usuario
debe abrir el sitio (o `docs/` servido localmente), forzar arranque en frío
(sin caché, DevTools → Network «Disable cache») y anotar el total y el
tiempo de la primera consulta. Criterio de aceptación propuesto: **< 5 s en
frío** con buena conexión (el wasm sigue pesando 18,1 MB; si no se llega, la
siguiente palanca es dividir el binario wasm o servirlo por un CDN con
compresión).

---

## 2. Podado de particiones (¿se bajan las 55 particiones de bancos?)

**Respuesta: no.** Con la consulta típica `WHERE periodo = (SELECT
max(periodo) …)`, DuckDB usa las stats del pie de cada archivo: para bancos
se leen **0,75 MB de los 22,19 MB publicados (97 % de ahorro)** — el pie de
los 55 archivos más el row group del último período. Medición completa en
`scripts/medir_parquet_fisico.py` (reproducible):

| Vista | Ficheros | Filas | Publicado | Con stats | Ahorro |
|---|---:|---:|---:|---:|---:|
| seguros_renta_fija | 21 | 2,216,342 | 97,26 MB | 4,91 MB | 95 % |
| ffmm_cartera_extranjera | 26 | 1,458,739 | 25,60 MB | 0,82 MB | 97 % |
| ffmm_cartera_nacional | 56 | 1,560,830 | 24,58 MB | 1,19 MB | 95 % |
| bancos_balance / bancos_resultados | 55 c/u | 1,927,964 c/u | 22,19 MB | 0,74 MB | 97 % |
| seguros_bienes_raices | 21 | 724,319 | 21,12 MB | 1,26 MB | 94 % |
| fi_cartera_nacional | 26 | 933,532 | 19,66 MB | 1,23 MB | 94 % |

Peor caso de la tabla: 75 % (agf_balance). El coste de *no* poder podar
(descargar todo) se incluye en el script como columna «todo».

---

## 3. Forma física de los Parquet

- **52 vistas · 12,798,721 filas físicas · 261,8 MB publicados.**
- Pies de metadatos: **5,30 MB (2,0 % del total)** — el coste de la poda es
  baratisimo.
- Codec: ZSTD en las series grandes (las que importan), SNAPPY en los
  maestros pequeños — correcto.
- **Row group máximo: 30.046 filas** (serie de factoring); el resto de vistas
  está particionada por período con row groups de pocas miles de filas.
  Conclusión del script: *toda vista ≥ 1 MB tiene row groups suficientemente
  pequeños para podar* — no hay que re-particionar nada.
- 12,798,721 filas físicas vs 10,870,757 filas lógicas: la diferencia son los
  períodos históricos que las vistas filtran y las dos vistas de banca que
  comparten particiones (contadas una vez en el total lógico).

---

## 4. Coherencia de conteos (defecto 6)

Tres fuentes daban tres respuestas (52 / 49 / 53). Resuelto:

| Fuente | Antes | Ahora |
|---|---:|---:|
| `data_manifest.json` | 49 datasets · 10.870.630 | **51 datasets · 10.870.757** |
| Catálogo de Descargas (52 conjuntos) | 8.942.793 (no contaba banca) | **10.870.757** (igual con y sin pyarrow) |
| `pipelines/auto/inventario.json` | 53 filas | 53 filas (52 vistas + datasete de banca) |

La divergencia restante es la esperada y documentada: **52 vistas = 51
datasets**, porque `bancos_balance` y `bancos_resultados` filtran las mismas
55 particiones (datasete `bancos_cmf_lineas`, contado una vez). Las dos
entradas que faltaban en el manifiesto fueron `cooperativas_lista_entidades`
(7 filas) y `corredoras_bolsa_lista_entidades_registro` (120): eran las
127 filas de deriva (10.870.757 − 10.870.630).

**Guardia nueva:** `audit_automatizacion.py::alineacion_manifest()` falla si
una entrada del manifiesto deja de coincidir con las filas reales de sus
Parquet, si una vista publicada queda sin entrada, o si `total_tables` /
`total_records` no cuadran con la lista. Verificada contra una deriva
simulada (3 errores detectados) y contra el estado real (0 problemas).

---

## 5. Estado de los defectos del traspaso

| # | Defecto | Estado |
|---|---|---|
| 1 | Arranque en frío 23 s | **Corregido** (fases paralelas + preload); pendiente re-medición en navegador (§1.3) |
| 2 | Formatos de RUT entre industrias | **Corregido (2026-09-29)**: convención canónica aplicada a 193 Parquet + 7 JSON, guardián en CI y writers blindados. Ver `rut_formatos_2026-09-29.md` |
| 3 | Consulta AGF vacía | **Corregido**: `actualizar_carteras.py` calcula `fondos_inversion_administrados`; backfill publicado, 47/72 AGF con valor > 0 |
| 4 | `fi_bienes_raices` vacía | **Resuelto**: la CMF publica 0 filas de bienes raíces para FI en los 26 trimestres (vs 933.532 de cartera nacional) → vista publicada marcada «Sin datos» (sidebar, diccionario, vocabulario) |
| 5 | Catálogo de Descargas mal contado | **Corregido**: `filas_heredadas` para las vistas unificadas; 10.870.757 estable en ambos entornos |
| 6 | Manifiesto desalineado | **Corregido** + guardia (§4) |
| 7 | Chips / cuentas de la interfaz | **Corregido** (116 consultas, «Sin datos» en el chip) |
| 8 | Sin `LICENSE` | **Corregido**: licencia MIT (decisión del autor, 2026-09-29) |
| 9 | Auditoría de consultas sugeridas sin arnés | **Corregido**: 116 OK · 0 VACIA · 0 ERROR, ahora en CI |

---

## 6. Verificación final (todo verde, 2026-09-29)

| Suite | Resultado |
|---|---|
| `audit_navigation.py` | 12 familias · 52 tablas · 52 opciones del visor |
| `audit_automatizacion.py` | 53 tablas inventariadas · **0 problemas** (con la nueva guardia) |
| `normalizar_vocabulario.py --check` | 52 tablas · 15 sectores · 22 tipos |
| `audit_consultas_sugeridas.py --check` | **116 OK · 0 VACIA · 0 ERROR** |
| `audit_duckdb_client.js` | 10/10 (registro de vistas sin navegador) |
| `audit_rut_formatos.py` (guardián) | 613 archivos auditados · **0 problemas** |
| `audit_web_full.py` | 100 % (393 columnas auditadas contra Parquet reales) |
| `audit_interfaz.py` | INTERFAZ COHERENTE |
| Tests `bancos` / `factoring_leasing` / `macro` / `normativa_cmf` | OK / OK / OK / OK |

Corrección colateral: `factoring_leasing/tests/test_publication.py` aún
esperaba el id `factoring_leasing_maestro` y el archivo `export_modal.js`
(ambos retirados en el vocabulario canónico del 2026-09-28); se actualizó a
la estructura real del sitio.

**CI:** `web_audit.yml` ahora corre en cada push `audit_consultas_sugeridas.py
--check` (con `duckdb`) y `scripts/audit_duckdb_client.js` (sin dependencias),
y el flujo de automatización instala `pyarrow` para la guardia de alineación.

---

## 7. Qué queda

1. **Re-medición del arranque en el navegador del usuario** (criterio < 5 s, §1.3):
   esta máquina no tiene navegador headless; las mediciones son del lado del
   servidor y del cliente DuckDB en local.
2. Activación de GitHub Pages (pendiente del autor); el README ya apunta a la
   URL final.
3. El guardián de RUT (`audit_rut_formatos.py`) vigila la convención en cada
   push; si un extractor nuevo publica otro formato, la CI lo detiene antes de
   que se publique.
