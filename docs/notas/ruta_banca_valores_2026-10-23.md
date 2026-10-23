# Banca: valores normalizados y maestro validado — 2026-10-23

**Qué se vio.** Dos cosas en la sección «Banca y estados financieros CMF»:

1. La ficha **Lista de Entidades** dice «40 códigos · Falta validar» y el grupo
   entero se pinta en ámbar (`status: "por_auditar"`).
2. En **Estado de Resultados CMF · R1** no se ven valores: la columna del importe
   es un arreglo de texto (`importes_fuente_raw`), así que el Visor muestra
   `001345990724750` —el código del archivo CMF con ceros a la izquierda— en vez
   de un monto.

## Diagnóstico

### Los importes no están normalizados

`bancos.resultados` y `bancos.balance` publican **sólo** los dos arreglos del
extractor:

| Columna | Tipo | Qué ve el usuario |
|---|---|---|
| `importes_fuente_raw` | `VARCHAR[]` | `001345990724750` (15 dígitos, ceros a la izquierda) |
| `importes_fuente_decimal` | `VARCHAR[]` | `1345990724750` (texto, sin unidad) |

No hay ninguna columna numérica: no se puede ver un monto legible ni sumarlo con
`SUM()`. Además el archivo fuente cambió de formato a mitad de la serie y el
publicado mezcla los dos:

| Periodos | Formato del importe | Ejemplo |
|---|---|---|
| 2022-01 → 2024-05 | 15 dígitos con coma decimal (18 caracteres) | `26458735676131,00` |
| 2024-06 → 2026-08 | 15 dígitos enteros | `025258284006864` |

Ambos son pesos; el `.00` es relleno. Pero leer la columna cruda obliga a
recordar en qué mitad de la serie está cada fila.

Los dos significados están resueltos y documentados en
`bancos/ESQUEMA_CMF_B1_B2_R1.md` («Importes»): en R1 el importe es el
**acumulado del ejercicio** (enero → mes informado); en B1/B2 los cuatro
importes son las monedas (no reajustable, reajustable por IPC, reajustable por
tipo de cambio y extranjera) y **su suma es el total de la cuenta**.

### El maestro tiene RUT que la CMF no reconoce

`bancos/AUDITORIA_MAESTRO_IDENTIDADES.md` dejó el maestro marcado «pendiente de
validación» tras cotejar 4 de 40 RUT. Al cotejar los 41 contra el registro
BANCO de la CMF (`consulta.php`, vigentes y no vigentes) aparece la causa: **9
RUT no existen en ninguna de las dos listas** y siguen un patrón que no es de la
CMF (`59048000-2`, `59060000-8`, `59070000-2`, `59015000-2`…), mientras el
registro oficial usa números irregulares.

| Código | Maestro (hoy) | Registro CMF | Nombre en el registro |
|---|---|---|---|
| 017 | 59015000-2 | **97003000-K** | BANCO DO BRASIL S.A. |
| 043 | 59048000-2 | **59002030-3** | BANCO DE LA NACION ARGENTINA |
| 045 | 59060000-8 | **59002220-9** | THE BANK OF TOKYO-MITSUBISHI UFJ, LTD |
| 046 | 97054000-8 | **97919000-K** | BANCO SUDAMERICANO (ANTES THE ROYAL BANK OF SCOTLAND (CHILE)) |
| 052 | 97058000-K | **96929050-2** | DEUTSCHE BANK CHILE |
| 054 | 97060000-0 | **97949000-3** | RABOBANK CHILE (EX HNS BANCO) |
| 056 | 97066000-3 | **97952000-K** | BANCO PENTA |
| 057 | 97068000-4 | **99565970-0** | BANCO PARIS |
| 058 | 59070000-2 | **59141000-8** | DNB NOR BANK ASA |

Los 18 bancos vigentes y 3 de los cerrados (504, 507, 049) sí coinciden.

## Pasos

- [x] **B1 · Importe normalizado en el extractor.** `importe_clp` (`BIGINT`, pesos:
      el importe de R1; la suma de los cuatro componentes en B1/B2) y
      `formato_monto_fuente` (`entero_15` / `decimal_coma`) en
      `bancos/scripts/extract_cmf_bank_lines.py`, de modo que las particiones
      nuevas ya nazcan legibles.
- [x] **B2 · Relleno de lo publicado.** `bancos/scripts/normalizar_importes.py`
      agrega las dos columnas a las 56 particiones existentes **sin volver a
      descargar la CMF**: la información ya está en `importes_fuente_decimal`.
      Idempotente, escribe en temporal y verifica el número de filas.
- [x] **B3 · Contrato, diccionario y consultas.** Se declaran las columnas en
      `docs/reproducibilidad/diccionario.csv`, se regenera la cadena del contrato
      y las fichas de la sección dejan de decir «sin sumar importes»: ahora hay
      consultas de utilidad e ingresos por banco.
- [x] **B4 · Cotejo de identidades.** `bancos/scripts/validar_identidades.py`
      compara el maestro contra el registro BANCO de la CMF (vigentes y no
      vigentes). Escribe `docs/outputs/bancos/identidades_cmf.json` con el
      resultado por fila, la URL y la fecha del cotejo, y falla si un RUT del
      maestro no aparece en el registro.
- [x] **B5 · Corrección de los 9 RUT.** Se corrigen en el maestro y se propagan a
      las particiones publicadas con `bancos/scripts/completar_entidades.py`.
- [x] **B6 · La ficha deja de decir «Falta validar».** El resultado del cotejo se
      resume en la propia ficha: cuántas identidades están cotejadas y cuáles no
      son cotejables (agregados sectoriales, filiales en el exterior y una
      entidad histórica absorbida), con el enlace al JSON. Además, el Visor
      formatea `importe_clp` como pesos y los chips de la sección abren con la
      utilidad del ejercicio y el total de activos por banco, en vez de una
      muestra de texto crudo.
- [x] **B7 · Compuertas.** Las de siempre (contrato, claves, web, móvil) más
      `validar_identidades.py --check`, que corre sin red sobre el JSON publicado.

## Lo que no se toca

- El grano de la tabla (una fila por período, institución, modelo y cuenta) y las
  columnas del extractor: sólo se **agregan** dos.
- `importes_fuente_raw` / `importes_fuente_decimal`: son la representación fiel
  del archivo y se conservan tal cual.
- Los agregados sectoriales (900, 950, 960, 970, 980, 998 y 999): siguen
  publicados y marcados como tales. Sumarlos junto con los bancos duplica el
  sistema, y el diccionario ya lo advierte.

## Resultado (2026-10-23)

Lo ejecutado, con las cifras que quedaron en los archivos publicados:

| Paso | Evidencia |
|---|---|
| B1 | `extract_cmf_bank_lines.py` calcula `importe_clp` y `formato_monto_fuente` con `Decimal`. |
| B2 | **56 particiones, 1.962.992 filas, 0 importes incorrectos, 0 con centavos**; segunda corrida `reescritas: 0`. `--check` en verde (5 s). |
| B3 | Las dos columnas están en `docs/reproducibilidad/diccionario.csv|json`, en `docs/api/esquemas.json` y en el contrato; `views.sql` y `duckdb_client.js` no necesitaron cambios. |
| B4 | **30 cotejadas · 7 agregados sectoriales · 4 declaradas · 0 fuera del registro**. |
| B5 | **9 RUT** corregidos en el maestro y su Parquet; `completar_entidades.py` no reescribió ninguna partición (`filas_sin_entidad: 0`). |
| B6 | «41 instituciones · 20 vigentes» y «41 códigos · Cotejado con CMF»; el grupo deja de estar en ámbar. |
| B7 | Compuerta «Banca: identidades cotejadas e importes normalizados» en `web_audit.yml` (tres `--check`, sin red). |

**Un defecto encontrado al cerrar.** Al escribir el chip que muestra el RUT
completo apareció que las 9 filas corregidas tenían `rut_dv` **con puntos**
(`97.003.000-K`) frente a las otras 32 sin puntos (`97004000-5`). Se corrigió
`con_dv()` en `corregir_identidades.py` y el `--check` ahora falla si reaparece
un punto o si `rut_dv` deja de ser `rut` más el dígito verificador. Las
particiones no cambian por esto: el campo `rut` siempre fue el cuerpo.

**Respuesta a la pregunta «¿está mal o se lee mal?».** Las dos cosas estaban
mezcladas: el dato era correcto (los importes del archivo son pesos, con el
significado ya documentado), pero la capa publicada no ofrecía ninguna columna
numérica, así que el Visor mostraba el campo crudo de 15 dígitos. Ahora hay una
columna numérica, un marcador del formato de origen y consultas sugeridas que
muestran los montos al frente.
