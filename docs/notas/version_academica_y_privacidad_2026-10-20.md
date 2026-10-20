# Versión académica citable, reproducibilidad y privacidad (2026-10-20)

Nota de implementación. Cierra cinco cambios acordados para convertir el sitio en
una plataforma académicamente citable **sin rediseñarlo**: la portada, la
jerarquía de industrias, las URL de los Parquet y las vistas SQL quedan
exactamente igual.

Resumen de lo que se tocó:

| # | Cambio | Dónde |
|---|---|---|
| 1 | Versión académica congelada + cómo citar | `docs/js/cita.js`, bloques en Información y Descargas, `scripts/construir_snapshot_academico.py` |
| 2 | Fuentes, licencia y limitaciones | sección nueva en Información (`docs/index.html`) |
| 3 | Protección de identificadores | `pipelines/auto/privacidad.py`, `scripts/enmascarar_identificadores.py`, publicadores de `fi` y `seguros` |
| 4 | Reproducibilidad descargable | `scripts/construir_reproducibilidad.py` → `docs/reproducibilidad/` |
| 5 | 25 del núcleo vs 59 visibles | etiquetas en la portada, Descargas y alcance |
| + | Monitor normativo fuera de la navegación | pestaña retirada, código conservado |

---

## 1. Versión académica: la página se mueve, el objeto citable no

El sitio cambia con cada publicación, así que la base se cita por una versión
congelada: **SIF-Chile Core Holdings v1.0**: los 25 conjuntos del núcleo
(seguros, fondos mutuos y fondos de inversión), congelados con fecha de corte
**2026-08**, 11.063.323 registros, 242,4 MB en Parquet.

- `docs/js/cita.js` es la única fuente de los datos de citación (versión, corte,
  DOI, autoría, licencias, enlaces). Pinta dos bloques: uno largo en Información
  y uno compacto en Descargas. Ambos ofrecen la cita en APA 7 y BibTeX, con
  botón de copiar.
- **Regla del módulo:** si un dato no existe (DOI, ORCID, filiación, correo), el
  bloque lo declara *pendiente*. Nunca inventa un identificador: un DOI falso es
  peor que un DOI pendiente.
- `scripts/construir_snapshot_academico.py` arma la carpeta del snapshot con
  `README.md`, `CITATION.cff`, `CHANGELOG.md`, `LICENSE.txt`, los Parquet del
  núcleo y la documentación, más un `inventario_snapshot.csv` con el SHA-256 de
  cada archivo de ese snapshot. Con `--zip` deja además el archivo comprimido.

Pendiente, y se completa en un solo lugar (`docs/js/cita.js`): DOI y URL del
snapshot, filiación, ORCID y correo de contacto.

## 2. Fuentes, licencia y limitaciones

Sección nueva en Información, con tres columnas: **fuentes** (los datos son de
la CMF, el Banco Central, SPensiones y SUSESO; el SIF aporta extracción,
normalización, validación y documentación), **licencia y respaldo** (código MIT;
datos de sus fuentes oficiales; proyecto independiente sin aval de la CMF ni del
Banco Central) y **limitaciones** (cobertura 2001–2026 como máximo entre tablas,
no homogénea; unidades y criterios de la fuente sin convertir; sin carteras de
AFP; identificadores protegidos).

Ojo: había una contradicción heredada en el repositorio — `LICENSE` dice MIT y el
README decía «todos los derechos reservados». Quedó resuelta: MIT para el código
y una nota explícita de que los datos pertenecen a sus fuentes oficiales.

## 3. Identificadores protegidos

Módulo nuevo: `pipelines/auto/privacidad.py`. No es anonimización con garantía
formal (k-anonimato, privacidad diferencial): es reducción deliberada del riesgo
de reidentificación, manteniendo la utilidad analítica y la referencia a la
fuente CMF.

### `fi.cartera_nacional.rut_emisor`

Se suprime el RUT cuando probablemente corresponde a una persona natural, y se
agrega `emisor_tipo` para dejar auditado el criterio en cada fila.

Criterio, reproducible:

1. el cuerpo numérico del RUT es **menor a 50.000.000** (rango que el SII
   asigna mayoritariamente a personas naturales), **y**
2. el RUT **no** aparece en los registros de entidades que el propio sistema
   publica (3.280 RUT: fondos de inversión, fondos mutuos, aseguradoras y listas
   de entidades).

La segunda condición es la importante. Sin ella la regla habría suprimido el 83 %
de los RUT, porque los **fondos** tienen RUN cortos (7007, 8253, 9273…) que
parecen de persona y no lo son. Con ella, el resultado sobre lo publicado:

| | Filas | % |
|---|---:|---:|
| `persona_juridica` | 730.593 | 78,3 % |
| `persona_natural_probable` (RUT suprimido) | 202.835 | 21,7 % |
| `sin_rut_informado` (la fuente no lo traía) | 104 | 0,0 % |

Lo suprimido se concentra donde se espera: mutuos hipotecarios (`MH`) y otros
instrumentos de deuda (`OTDN`), es decir, donde el deudor es una persona.

Se prefirió el falso positivo (suprimir el RUT de una empresa chica) al falso
negativo (publicar el de una persona). El criterio es público y está probado en
`pipelines/auto/tests/test_privacidad.py`.

`fi.metodo_participacion` quedó fuera a propósito: ahí el emisor es una sociedad
filial o coligada —siempre una entidad— y la fila ya trae su nombre.

### `seguros.bienes_raices`

No se publican la dirección exacta ni el rol tributario del inmueble: juntos
permiten ubicar una propiedad y, con ella, a sus ocupantes. Se conservan
`comuna`, `ciudad` y un `property_id` estable (`BIEN-…`) que permite seguir el
mismo bien entre meses.

Detalle que importa: la columna de la dirección **se llama distinto según el
formato de la CMF** —`ubicacion` en el vigente desde 2024-12 y `direccion` en
los archivos anteriores (21 de los 22 publicados). Se retiran ambas.

Resultado: 22 archivos, 760.152 filas sin dirección ni rol, y 42.925
`property_id` distintos.

El seudónimo es determinista por omisión (reproducible por cualquiera), lo que
implica que un atacante con el listado de roles podría probar combinaciones. Para
la versión académica se recomienda fijar la variable de entorno
`SIF_PRIV_SALT` con un valor que no se publique: el id deja de ser reproducible
y deja de ser un punto débil.

**Decisión abierta:** `arrendatario` (nombre del arrendatario, muchas veces una
persona) y `nombre_del_tasador_1/2` siguen publicados tal como los informa la
CMF. El encargo original no los mencionaba y enmascararlos tiene costo
analítico; queda como decisión abierta.

## 4. Reproducibilidad fuera del JavaScript

`scripts/construir_reproducibilidad.py` genera `docs/reproducibilidad/`, que se
publica con el sitio y se enlaza desde Información y Descargas:

| Archivo | Contenido |
|---|---|
| `diccionario.csv` / `.json` | 1.284 columnas de 75 tablas: tipo, rol, significado y criterio contable, volcadas desde `docs/js/data_dictionary.js` (misma fuente que la web). |
| `inventario_fuentes.csv` | 748 archivos publicados con peso y SHA-256, para verificar una descarga. |
| `cobertura_por_periodo.csv` | Registros por tabla y periodo (1.924 filas), según los manifiestos. |
| `validacion_resumen.csv` | Una fila por tabla: fuente, norma, modalidad, rango cubierto, periodos, registros y archivo. |

Con `--check` falla si están desactualizados, así que puede entrar en CI.

## 5. 25 del núcleo vs 59 visibles

Dos cifras distintas se etiquetaban igual («conjuntos principales»). Ahora:

- Portada: **25 conjuntos del núcleo**.
- Descargas: **59 conjuntos en la vista principal**.
- Alcance: «59 conjuntos visibles en la vista principal: son los 25 del núcleo
  más instituciones (bancos, AGF y corredoras) y contexto (series del Banco
  Central)».

## Monitor normativo: fuera de la navegación

Se retiró la pestaña Normativa. Era otro producto: exigía revisión periódica y
sus resúmenes envejecen rápido; dejarlos a la vista habría mostrado una sección
abandonada en pocos meses. **No se borró el código**: `docs/js/normativa_monitor.js`
y `scripts/audit_normativa_web.js` siguen en el repositorio por si algún día
vuelve como proyecto aparte, y `scripts/audit_interfaz.py` cuida esa frontera
(que la pestaña no esté en la web, pero que el módulo siga en el repo).

Las pestañas quedan en seis: Información, Mapa relacional, Diccionario, Visor de
datos, Consultas SQL y Descargas (`Alt+1`…`Alt+6`).

## Cómo se verifica todo esto

```
.venv/bin/python -m unittest discover -s pipelines/auto/tests -p "test_privacidad.py"
python3 scripts/audit_interfaz.py
node scripts/audit_interfaz_dom.js              # 72 comprobaciones
.venv/bin/python scripts/enmascarar_identificadores.py            # informe (idempotente)
.venv/bin/python scripts/construir_reproducibilidad.py --check
.venv/bin/python scripts/construir_snapshot_academico.py --zip
```
