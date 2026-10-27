# Sensibilidad de consultas SQL sugeridas a filas exactamente repetidas

**Fecha:** 2026-10-26
**Alcance:** consultas sugeridas en el explorador y chips por defecto de SQL; comparación local con los Parquet que consumen las vistas SQL.
**Conclusión acotada:** se localizaron consultas cuyo resultado cambia en un contrafactual que elimina filas completas idénticas. Es una medición de sensibilidad, no una clasificación de causa, validez o error de los datos. No se modificó ninguna consulta ni fila.

## Método reproducible

```bash
.venv/bin/python scripts/test_audit_consultas_sensibles_repeticiones.py
.venv/bin/python scripts/audit_consultas_sensibles_repeticiones.py --check
.venv/bin/python scripts/audit_consultas_sugeridas.py --check
```

El auditor lee las **152** sugerencias del explorador y los **7** chips SQL del terminal. Registra las mismas vistas declaradas en `pipelines/api/vistas.py` y en `docs/js/duckdb_client.js`; para cada una compara la vista publicada con una copia de análisis que aplica `SELECT DISTINCT *` a la fuente Parquet de SQL, conservando filtros y rutas SQL/compactas. Compara las salidas por multiconjunto de filas y normaliza los `float` a 12 cifras significativas para no contar como impacto el ruido mínimo de orden de suma. Esa tolerancia puede ocultar cambios menores que esa precisión.

El número de filas repetidas que el informe muestra entre paréntesis corresponde a la **vista completa**, no necesariamente al subconjunto de período de la consulta. Las consultas se evalúan con sus filtros reales, pero este total no es un conteo de repetidas dentro del filtro.

## Resultado local

- Las 159 consultas ejecutaron sin filas vacías ni errores en `audit_consultas_sugeridas.py --check`.
- **28 de 159** entradas referencian vistas cuyo contenido completo tiene al menos alguna fila exactamente repetida. De esas, **13** mantienen la misma salida y **15** cambian al aplicar el contrafactual: **14 consultas SQL distintas**, porque una consulta aparece tanto en el explorador como en los chips del terminal.
- Los 15 cambios están distribuidos entre seguros (3 entradas), FFMM (9, incluida la misma consulta presentada dos veces en la interfaz) y fondos de inversión (3). Son 14 consultas distintas. No se infiere de ello que las filas deban eliminarse: la interpretación de esas repeticiones sigue dependiendo de evidencia fuente y unidad semántica.

| Sugerencia que cambia | Vista SQL con repetición exacta | Filas de salida publicadas → contrafactual |
|---|---|---:|
| Bienes raíces por ciudad, último mes (M$) | `seguros_bienes_raices` | 10 → 10 |
| Inversiones en el extranjero por país, último mes (M$) | `seguros_extranjeros` | 10 → 10 |
| B.14 Garantías por posición y tipo (M$) | `seguros_garantias_derivados` | 50 → 50 |
| Cartera nacional por tipo de instrumento, último mes | `ffmm_cartera_nacional` | 15 → 15 |
| Mayores emisores nacionales, último mes | `ffmm_cartera_nacional` | 10 → 10 |
| Instrumentos con compromiso o en garantía, último mes | `ffmm_cartera_nacional` | 4 → 4 |
| Cartera extranjera por país emisor, último mes | `ffmm_cartera_extranjera` | 15 → 15 |
| Fondos con inversión extranjera por mes | `ffmm_cartera_extranjera` | 24 → 24 |
| Forwards y futuros por activo objeto, último mes | `ffmm_futuros` | 15 → 15 |
| Contratos vigentes por mes | `ffmm_futuros` | 24 → 24 |
| Cartera nacional por tipo de instrumento, último trimestre | `fi_cartera_nacional` | 30 → 30 |
| Mayores emisores nacionales, último trimestre | `fi_cartera_nacional` | 20 → 20 |
| Fondos mutuos: cartera nacional por tipo (entrada duplicada del terminal) | `ffmm_cartera_nacional` | 15 → 15 |
| Cartera extranjera FFMM por país (último período) | `ffmm_cartera_extranjera_ultima_particion` | 15 → 15 |
| Fondos de inversión: cartera nacional por tipo (último período) | `fi_cartera_nacional_ultimo_periodo` | 15 → 15 |

Un ejemplo reproducible de la diferencia es la categoría `ACC` en la sugerencia de cartera nacional FFMM para 2026-09. En la salida publicada, la consulta devuelve `posiciones=1.877`, `fondos=45` y `valorizacion_miles_mf=4.498.698.365`; en la variante que primero aplica `SELECT DISTINCT *`, devuelve `1.876`, `45` y `4.498.696.862`. Los nombres de las columnas se conservan tal como los devuelve la consulta; no se interpreta aquí la unidad semántica de «posición» ni se decide cuál salida representa operaciones válidas. Para repetir esa comparación en DuckDB, con la vista `ffmm_cartera_nacional` registrada:

```sql
-- Filas publicadas tal cual
SELECT tipo_instrumento, count(*) AS posiciones,
       count(DISTINCT run_fondo) AS fondos,
       sum(valorizacion_miles_mf) AS valorizacion_miles_mf
FROM ffmm_cartera_nacional
WHERE periodo = '2026-09' AND tipo_instrumento = 'ACC'
GROUP BY tipo_instrumento;

-- Variante hipotética: quitar filas completas idénticas antes de agregar
WITH distintas AS (
  SELECT DISTINCT * FROM ffmm_cartera_nacional
  WHERE periodo = '2026-09'
)
SELECT tipo_instrumento, count(*) AS posiciones,
       count(DISTINCT run_fondo) AS fondos,
       sum(valorizacion_miles_mf) AS valorizacion_miles_mf
FROM distintas
WHERE tipo_instrumento = 'ACC'
GROUP BY tipo_instrumento;
```

## Límites y decisión pendiente

- El contrafactual deduplica únicamente para medir sensibilidad; **no es una propuesta de corrección**. La identidad de fila no prueba que dos reportes sean el mismo evento, ni que sean eventos distintos.
- El análisis cubre las 159 consultas sugeridas, no SQL libre del usuario, todas las visualizaciones del sitio, descargas directas ni el hosting publicado. Tampoco confirma el resultado que sirve hoy el navegador.
- El total de repetidas por vista es de todo el período publicado; no equivale a filas afectadas dentro del filtro de cada consulta.
- `audit_consultas_sugeridas.py` sigue siendo la prueba de validez sintáctica y no vaciedad (159/159). Esta auditoría nueva localiza exposición potencial, pero no decide si se corrige, se limita con un aviso contextual o se mantiene.

Por ello, el control de riesgo material y la decisión de producto sobre ejemplos, visor, SQL y descargas permanecen abiertos. No se alteraron Parquet, filtros, consultas ni métricas de portada.
