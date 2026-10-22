# Decisiones pendientes de la API v1 (D1–D4)

Estado: **propuesta**, no decisión. Cada una trae la recomendación, el motivo y
lo que cuesta cambiarla después. La Fase 0 no se puede cerrar sin esto porque
fija nombres y URLs que el descriptor ya usa de forma provisional.

---

## D1 · URL canónica (tarea 0.1)

**Recomendación: GitHub Pages es la canónica; Vercel queda como espejo del
visor, sin anunciarse como API.**

```
https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/
```

Motivos, en orden de peso:

1. **Es la que ya usa el README**, y por tanto la que la gente tiene guardada.
2. **CORS abierto.** Pages responde `Access-Control-Allow-Origin: *`, que es lo
   que permite que una app de otro dominio lea catálogo y Parquet. Vercel puede
   configurarlo, pero hay que mantenerlo.
3. **Coste cero y sin cuota propia.** El límite blando de Pages (100 GB/mes) ya
   está calculado: unas 223 descargas completas del núcleo al mes, y las
   lecturas por `Range` de DuckDB gastan mucho menos.
4. Vercel ya cumple otro papel (el visor con cabeceras de seguridad propias);
   no hace falta que además sea la cara de la API.

**Qué pasa con la otra:** se documenta como espejo del visor y se le añade un
`link rel="canonical"` apuntando a Pages. No se redirige: romper el visor de
Vercel por una decisión de nombres sería peor.

**Coste de cambiarlo después:** bajo. Mientras el descriptor declare `base_url`
y sea generado, mover el sitio es regenerar y un redirect. Lo caro sería que
alguien hubiera fijado la URL de Vercel en su código.

---

## D2 · Identificador canónico (tarea 0.2)

**Recomendación: `name` = el `view_name` actual. Un solo identificador en v1,
con los 15 alias heredados publicados en `sif.aliases[]`.**

- El cliente escribe `FROM seguros_renta_fija`; el descriptor dice
  `"name": "seguros_renta_fija"`. Nada que traducir.
- `seguros_maestro` y los otros 14 nombres viejos siguen funcionando en la web
  porque `LEGACY_VIEW_ALIASES` los resuelve, pero **no** son nombres de recurso:
  van como alias para que nadie los use en código nuevo.
- Los 2 objetos que comparten dataset (`bancos_balance`, `bancos_resultados`)
  ya son identificadores propios, con el mismo `manifest_id` y distinto filtro.

**Lo que se gana:** el identificador del descriptor, el de la vista SQL y el de
la consulta son la misma cadena. Cero ambigüedad.

**Lo que se pierde:** el nombre visible (`afp.lista_administradoras`) no es el
identificador. Se queda en `title`, que es donde corresponde.

**Coste de cambiarlo después:** alto si se hace sin campo intermedio. Por eso
v1 fija `sif.sql_view` y `sif.aliases[]` desde el principio: permite separar
`name` del nombre SQL más adelante sin cambiar el formato.

---

## D3 · Versionado del contrato (tarea 0.3)

**Recomendación: `/api/v1/` en la ruta y semver en `version`, con esta regla:**

| Cambio | Versión | Ejemplo |
|---|---|---|
| **mayor** | se rompe un cliente | quitar o renombrar un recurso o una columna; cambiar el tipo de una columna |
| **menor** | se puede ignorar | añadir un recurso, una columna al final, o un campo `sif.*` |
| **parche** | sólo datos | corregir valores sin tocar esquema; cambia `data_release`, no `version` |

Lectura importante: **un dato nuevo no sube la versión del contrato.** El
contrato describe la forma; `data_release` describe el contenido. Confundirlos
obligaría a decir «v1.2.3» cada mes sin que nada estructural haya cambiado.

---

## D4 · `api_version` ≠ `data_release` ≠ `sha256` (tarea 0.4)

**Recomendación: seis campos separados, cada uno con un responsable claro.**

| Campo | Qué es | Quién lo escribe | Ejemplo |
|---|---|---|---|
| `api_version` | versión del contrato (semver de D3) | se sube a mano al cambiar la forma | `1.0.0` |
| `data_release` | huella del contenido publicado | se calcula del SHA-256 conjunto | `2026-10-21.dd49f53bf82b` |
| `sha256` | hash de cada partición | se calcula del archivo | `72a1015a…` |
| `published_at` | cuándo se publicó ese dato | `ultima_actualizacion` del manifiesto | `2026-10-21` |
| `source_period` | qué período cubre | `corte` del manifiesto | `2022-01 a 2026-08` |
| `extracted_at` | cuándo se bajó de la fuente | `metadatos.fecha_extraccion` | `2026-10-21` |

Regla de oro: **el hash identifica, no recupera.** Git conserva cada edición y
Pages sirve la última; no hay archivo histórico público. Eso es la tarea 0.5 y
se puede resumir en una frase publicable: *«cada release queda registrado y
verificable por su hash; el sitio publica siempre la última versión».*

---

## Lo que no está en discusión

- **0.6 licencia**: hecho (`DATA_LICENSE.md`). Las 4 fuentes quedan en
  `pendiente` hasta verificar el permiso de redistribución; ningún recurso
  declara una licencia no comprobada.
- **0.7 alcance**: «best effort, sin SLA»; la API **no** ofrece `/query` ni JSON
  por fila. Es un contrato estático más los Parquet. Esa frase tiene que estar
  escrita antes de anunciar nada.
