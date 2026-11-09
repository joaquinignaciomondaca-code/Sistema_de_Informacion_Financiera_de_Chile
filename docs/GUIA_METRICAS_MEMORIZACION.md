# Guía de memorización — Métricas publicadas del SIF (para Joaquín)

> **Fuente de verdad:** `docs/metricas_publicadas.json` (generado por `scripts/build_metricas_publicadas.py`).
> Todo número que cites en defensa, revisión o entrevista debe salir de ese archivo y de su `data_release`. Si el archivo cambia, tu discurso cambia. No memorices el número aislado: memoriza la **relación** y la **definición**.

Último `data_release` auditado: `2026-11-08.f82c99370da0` · 19 928 091 filas por objeto · 488 205 089 bytes · 732 particiones.

---

## 1. El mantra de 30 segundos (recítalo tal cual)

> “El SIF publica **90 objetos lógicos** en `api/v2/catalog.json`, que vienen de **89 tablas ETL** en `data_manifest.json`. Una tabla —`bancos_cmf_lineas`— se materializa como **dos objetos filtrados** (`bancos_balance` y `bancos_resultados`), por eso hay un objeto más. El catálogo de descargas expone esos 90 como **74 visibles + 15 fuera de foco + 1 oculto**, más **4 Parquet auxiliares** de DuckDB que no son objetos. Mido **19,9 M filas por objeto** (con doble conteo si una ruta se comparte) y **23,6 M filas físicas** si sumo las copias auxiliares; la diferencia no es cobertura nueva.”

Si te interrumpen, di solo: **“90 objetos = 89 tablas + 1 tabla dividida en dos vistas; 74+15+1 en descargas; 19,9 M lógicas, 23,6 M físicas.”**

---

## 2. Glosario mínimo (7 definiciones que no puedes confundir)

| Término | Dónde vive | Qué cuenta | Trampa |
|---|---|---|---|
| **Objeto API** | `catalog.json` | Recurso con ID propio, consultable por SQL. Puede ser vista filtrada o alias. | No es lo mismo que tabla ETL. |
| **Tabla ETL** | `data_manifest.json` | Unidad que extrae un pipeline. | 89 entradas; no equivale a objeto. |
| **Elemento de descarga** | `download_catalog.js` | Opción que ve el usuario en la pestaña Descargas. Una variante se cuenta pero se muestra junto a su base. | 90 elementos; 74 visibles + 15 archivo/registro + 1 oculto. |
| **Filas por objeto** | `metricas_publicadas.json` | Suma de `rows` reportado por cada objeto. Si dos objetos comparten la misma ruta Parquet, se cuenta dos veces. | No son registros únicos globales. |
| **Filas únicas de esquemas** | `esquemas.json` | Cada ruta Parquet física una sola vez. | Sigue sin deduplicar valores idénticos. |
| **Filas almacenadas (runtime)** | contrato + auxiliares | 23 625 326 filas físicas (732 del contrato + 4 auxiliares). Incluye copias. | No es cobertura. |
| **Bytes** | `metricas_publicadas.json` | Suma de tamaños de particiones del contrato. No es el tamaño de `docs/` entero. | 488 MB del contrato; 532 MB si sumas auxiliares. |

**Repetición activa:** tapa la columna “Qué cuenta” y recítala 3 veces.

---

## 3. Los cuatro números que te van a pedir (y cómo justificarlos)

### 90 vs 89 — ¿por qué no cuadran?
- `relacion_inventario_api.explicacion`: “`bancos_cmf_lineas` se publica como dos objetos lógicos, `bancos_balance` y `bancos_resultados`, con archivos filtrados distintos; los alias cambian nombres, no crean objetos adicionales.”
- Memotecnia: **“BANCOS es el único que se parte: B1/B2/R1 → 2 vistas.”**
- Puentes: `puentes_reconciliacion`: **73 directos, 15 alias, 2 origen_compartido** (las dos vistas de bancos). 73+15+2 = 90.

### 74 / 15 / 1 — ¿qué es visible?
- **74 visibles** = 40 núcleo (seguros+ffmm+fi) + 10 instituciones (bancos, AGF, corredoras) + 24 contexto (macro). 99,5 % de las filas.
- **15 fuera de foco** = 11 archivo (factoring, securitizadoras, patrimonios, CCAF) + 4 registro (pensiones, cooperativas, sistemas_pago, fintech). Siguen publicados, solo no destacados.
- **1 oculto** = `fi_bienes_raices` (0 filas; ningún FI informó bienes raíces entre 2020-03 y 2026-06).
- **1 variante** = `corredoras_bolsa_lista_entidades_registro` (misma lista con ficha CMF).

### 19,9 M vs 23,6 M — ¿cuántas filas hay realmente?
- **19 928 091**: suma por objeto. Útil para comparar con `data_manifest.json` y descargas; tiene doble conteo de la ruta compartida de bancos.
- **19 928 091** también en `inventario_etl.filas` → alineado.
- **23 625 326**: suma física contrato (19 928 091) + 4 auxiliares (`sql_query/*.manifest.json`, 3 697 235 filas). Nota del archivo: “contiene filas repetidas entre recursos y no representa cobertura única.”
- **Frase para salir del paso:** “Si me preguntas cuántas filas puedes consultar, digo 19,9 M lógicas; si me preguntas cuánto ocupa en disco el runtime de DuckDB, digo 23,6 M físicas con copias.”

### 732 particiones / 86 con archivo / 85 con filas
- 90 objetos → 86 con archivo (4 sin archivo: vacíos), 85 con filas >0 (1 con archivo pero 0 filas: `fi_bienes_raices`), 4 vacíos.
- Por estado: 79 publicados + 7 derivados + 4 vacíos.

---

## 4. Desglose por sector (solo el núcleo + secundarios, que es lo que miran)

| Sector | Elementos | Filas | Bytes | Periodo | Nivel |
|---|---|---:|---:|---|---|
| seguros | 24 | 10 553 271 | 379 MB | 2016-11 → 2026-09 | núcleo |
| ffmm | 7 | 3 616 378 | 58 MB | 2001-01 → 2026-09 | núcleo |
| fi | 9 | 3 300 526 | 30 MB | 2012-03 → 2026-06 | núcleo |
| bancos | 3 | 1 998 061 | 15 MB | 2022-01 → 2026-09 | secundario |
| agf | 3 | 129 711 | 1,0 MB | 2010-06 → 2026-06 | secundario |
| corredoras | 4 | 188 228 | 1,2 MB | 2010-12 → 2026-09 | secundario |
| macro | 24 | 41 599 | 0,58 MB | 2014-01 → 2026-11 | contexto |

**Truco:** seguros solo ya pesa 379 MB / 488 MB = **77 % del peso**. Si te dicen “¿dónde está el volumen?” responde “seguros renta fija: 2,3 M filas en 22 Parquet mensuales.”

---

## 5. Errores que te hacen quedar mal (y cómo evitarlos)

1. **“Hay 89 objetos.”** No: 89 tablas, 90 objetos. Si dices 89, te preguntan por bancos_balance.
2. **“Hay 19,9 M registros únicos.”** No: son filas por objeto, con doble conteo de la ruta compartida de bancos y sin deduplicar valores. Di “filas por objeto, no registros únicos”.
3. **“Los auxiliares son parte de la cobertura.”** No: `auxiliares_sql.excluidos_de_totales_api_y_descargas: true`. Son copias compactas para consultas; se excluyen de los totales del contrato.
4. **“El periodo de macro llega a 2026-09 como el resto.”** No: macro llega a **2026-11** (BCCh diario); el núcleo llega a 2026-09 (cierre CMF mensual).
5. **“FI bienes raíces tiene filas.”** No: 0 filas, oculto de la navegación pero publicado como Parquet vacío con esquema.

---

## 6. Rutina de repaso (5 minutos al día hasta la defensa)

**Día 1–2:** Recita el mantra (sección 1) 5 veces en voz alta. Luego escribe de memoria 90 = 89 + 1 (bancos).
**Día 3–4:** Sin mirar, lista los 7 términos del glosario con su trampa.
**Día 5:** Te auto-preguntas:
- ¿Cuántos visibles y por qué? (74 = 40+10+24)
- ¿Cuántos fuera? (15) ¿Cuántos ocultos? (1 `fi_bienes_raices`)
- ¿Cuántas particiones? (732) ¿Cuántas con filas? (85)
- ¿Qué bytes citas? (488 MB contrato; 532 MB con auxiliares)
**Día 6:** Abre `docs/metricas_publicadas.json` y verifica tu recitado con `jq .fuentes.api_v2.filas` y `jq .lecturas_duckdb`.

**Check rápido en terminal:**
```bash
python3 -c "import json; d=json.load(open('docs/metricas_publicadas.json')); print(f\"objetos={d['fuentes']['api_v2']['objetos']} tablas={d['relacion_inventario_api']['tablas_etl']} visibles={d['fuentes']['descargas']['principal']['elementos']} ocultos={d['fuentes']['descargas']['ocultos']['elementos']}\")"
```

---

## 7. Frases de cierre para entrevista

- “Las métricas están reconciliadas en `metricas_publicadas.json`: `alineacion` con 6 booleanos en `true` y `data_release` con trazabilidad a Git.”
- “El README explica por qué `data_manifest.json`, `catalog.json` y `download_catalog.js` dan números distintos: son tres vistas del mismo inventario, con distinta unidad de conteo.”
- “Si la CMF republica un cierre, las filas por objeto cambian pero el contrato sigue cuadrado: la validación es por objeto, ruta, filas y bytes.”

*Última actualización de esta guía: 2026-11-09 · data_release 2026-11-08.f82c99370da0*
