# Estándar de nombres del explorador y del diccionario

Regla única para que el explorador, el visor de datos, el diccionario y el diagrama
ERD se lean igual en todos los sectores.

## 1. Nombre de tabla (árbol, visor, diccionario, ERD)

Formato: `sector.tabla_en_minúsculas_con_guion_bajo`

* `sector` es el prefijo corto y estable del sector: `vida`, `generales`, `agf`,
  `ffmm`, `fi`, `afp`, `bancos`, `macro`, `factoring_leasing`, `corredoras`,
  `securitizadoras`, `patrimonios`, `cooperativas`, `ccaf`, `sistemas_pago`,
  `retail_financiero`, `fintech`.
* `tabla` describe el contenido en español, sin abreviaturas internas del pipeline
  (`b7_`, `censo`, `eeff` suelto) ni años repetidos.
* El nombre visible **no es** el identificador SQL de la vista. Los identificadores
  (`duckdb_client.js`) se mantienen estables para no romper consultas, exportaciones
  ni enlaces guardados.

Sufijos por tipo de contenido:

| Contenido | Sufijo / forma | Ejemplo |
| :--- | :--- | :--- |
| Lista maestra de entidades | `lista_entidades` (o `lista_administradoras`, `lista_instituciones`) | `bancos.lista_instituciones` |
| Universo/registro de fondos | `universo_fondos`, `registro_unico` | `fi.universo_fondos` |
| Cartera de inversiones | `cartera_<clase>` | `vida.cartera_bonos` |
| Derivados | `derivados_<tipo>` | `vida.derivados_swaps` |
| Pactos y repos | `repos_<detalle>` o `pactos_repos` | `fi.repos_contratos` |
| Balances y resultados | `balance_<detalle>`, `estado_resultados` | `bancos.estado_resultados` |
| Notas de EEFF | `nota_<materia>` | `patrimonios.nota_morosidad` |

## 2. Etiqueta de tarjeta (`label`)

* Español, mayúscula inicial, sin paréntesis decorativos ni años al final sueltos.
* Separador `·` cuando hay dos ideas: `Operaciones REPO · Muestra en revisión`.
* Sin sinónimos entre sectores: si es una cartera se llama "Cartera de Inversión"
  en todos.

## 3. Insignias (`badge`) y contador de filas (`rows`)

* Formato numérico español: punto para miles, coma para decimales.
  `417.303`, `11,59 M`, `275`.
* Desde 1.000.000 se abrevia con espacio: `11,59 M`, `9,09 M`.
* Unidad según la tabla: `Entidades`, `Fondos`, `Contratos`, `Pactos`,
  `Balances`, `Registros` (por defecto).
* La insignia de una tarjeta es la suma exacta de las filas de sus tablas, salvo:
  * tarjetas de "Lista de Entidades" → número de entidades del maestro;
  * tarjetas en revisión → `⚠ Falta auditar`.
* Los conteos se calculan desde los Parquet publicados, no se escriben a mano.

## 4. Datos en revisión

Cuando una tabla todavía no fue conciliada contra el documento oficial:

* `status: "por_auditar"` en el sidebar → insignia ámbar `⚠ Falta auditar`.
* Campo `advertencia` en el diccionario → recuadro ámbar con el alcance de lo que
  falta verificar.
* Los chips de esa tarjeta deben medir cobertura y campos incompletos, nunca
  publicar totales, rankings ni cifras de mercado.
