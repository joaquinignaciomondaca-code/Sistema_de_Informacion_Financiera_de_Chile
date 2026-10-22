# Contrato de la API pública (v1, en construcción)

Lo que hay aquí es el **contrato estático** de la API: dos archivos generados
desde los datos publicados, versionados junto al código y verificados en cada
CI. No son documentación escrita a mano, así que no pueden desviarse de lo que
el usuario descarga.

| Archivo | Qué responde |
|---|---|
| `reconciliacion.csv` | Qué objeto consume el cliente, con qué datos se sirve y en qué estado está (publicado, derivado o vacío). |
| `esquemas.json` | Qué columnas y qué tipos tiene cada objeto, con el significado del diccionario editorial cuando existe. |

Se regeneran con:

```bash
python3 scripts/build_reconciliacion.py   # docs/api/reconciliacion.csv
python3 scripts/build_esquemas.py         # docs/api/esquemas.json
```

Y el CI falla si quedan desactualizados (`--check` en ambos) o si algo del
contrato deja de cumplirse.

## `reconciliacion.csv`

Cruza los tres niveles que hasta ahora nadie había cruzado —objeto del
contrato, fila de `data_manifest.json` y dataset físico— porque no son 1:1:
hay objetos que son alias del nombre heredado y un dataset (`bancos_cmf_lineas`)
que se publica como dos objetos.

| Columna | Significado |
|---|---|
| `objeto` | Nombre de la vista que escribe el cliente (`FROM bancos_balance`). |
| `nombre_visible` | Nombre de catálogo que muestra la web. |
| `manifest_id` | Fila de `data_manifest.json` que lo respalda; vacío si no hay dato. |
| `puente` | Cómo se emparejó: `directo`, `alias` (nombre heredado) u `origen_compartido` (un dataset, dos vistas). |
| `nivel` | `nucleo`, `secundario`, `archivo` o `registro`. |
| `estado` | `publicado`, `derivado` (proyección de otro objeto) o `vacio` (sin particiones). |
| `motivo` | Por qué está vacío o de dónde deriva. |
| `deriva_de` | Objeto del que es proyección, si aplica. |
| `particiones`, `filas`, `bytes` | Tamaño real publicado. |
| `corte`, `ultima_actualizacion` | Cobertura temporal y fecha del último dato. |

Estado actual: **90 objetos** = 79 publicados + 7 derivados + 4 vacíos, sobre
las 89 filas del manifiesto. El puente se reparte en 73 directos, 15 alias y 2
de origen compartido.

## `esquemas.json`

```jsonc
{
  "contrato": "sif-api/esquemas",
  "version": "v1",
  "resumen": { "objetos": 90, "con_esquema": 86, "filas_unicas": 19777492, ... },
  "objetos": {
    "bancos_balance": {
      "manifest_id": "bancos_cmf_lineas",
      "nombre_visible": "bancos.cmf_lineas_b1_b2_r1",
      "sector": "bancos",
      "estado": "publicado",
      "particiones": 56,
      "filas": 722931,          // lo que devuelve la vista ya filtrada
      "filas_dataset": 1962992, // filas de los archivos, compartidos con bancos_resultados
      "archivo": "outputs/bancos/cmf_b1_b2_r1/2022-01/lineas.parquet",
      "filtro": "familia_archivo_fuente IN ('B1', 'B2')",
      "columnas": [
        { "nombre": "periodo", "tipo": "VARCHAR", "rol": "Fecha",
          "significado": "Periodo mensual del archivo CMF en formato YYYY-MM.",
          "criterio_contable": "No aplica" }
      ]
    }
  }
}
```

Reglas que el CI verifica:

1. **El tipo es el del Parquet**, en nombres de DuckDB (`VARCHAR`, `BIGINT`,
   `DOUBLE`, `DATE`…), que es lo que devuelve `DESCRIBE` sobre la vista. El
   diccionario editorial añade `rol`, `significado` y `criterio_contable`, y
   **nunca** cambia el tipo: si discrepa, manda el Parquet y el CI falla hasta
   que se corrija el diccionario.
2. **Todas las particiones de un objeto comparten esquema.** Si una tabla
   cambiara de forma según el corte, el script falla en vez de publicar dos
   verdades.
3. **Las 89 tablas del manifiesto tienen objeto** y los 90 objetos están en la
   reconciliación.
4. **Una columna vacía se declara.** Si una columna no tiene ningún valor en
   ninguna partición, se publica con el tipo que promete el diccionario (o
   `VARCHAR`) y dos marcas explícitas: `"tipo_fisico": "null"` y
   `"sin_valores": true`. Hoy son 5 columnas de origen vacío, no un error de
   tipos.
5. **`filas` cuenta lo que ve el cliente.** Cuando dos objetos comparten un
   dataset (`bancos_balance` y `bancos_resultados`), `filas` aplica el filtro
   de la vista y `filas_dataset` deja el total del archivo: 722.931 + 1.240.061
   = 1.962.992, las filas del dataset.
6. **Los 4 objetos sin dato no desaparecen**: se publican con `estado: "vacio"`,
   `columnas: []` y `motivo_sin_esquema`.

Estado actual: 86 objetos con esquema, 1.509 columnas (7 sin documentar en el
diccionario, 5 sin valores en origen), 19.777.492 filas únicas.

## Lo que todavía no es

- No hay **URL canónica** decidida (tarea 0.1 de la ruta): los archivos viven
  en el repo y en el sitio, pero la API aún no anuncia una dirección estable.
- No hay **OpenAPI**, **SDK** ni **ejemplos** (fases 1 a 1d). Este contrato es
  la materia prima de esos pasos: sin tipos reales no hay cliente que valga.
