# Traspaso para la auditoría de eficiencia y funcionalidades

**Fecha:** 2026-09-29
**Para:** la sesión que audite rendimiento y funcionalidades.
**Por qué existe:** la sesión anterior trabajó sobre el README y, de paso, encontró
defectos reales en el producto. Se listan aquí para no redescubrirlos y para que la
auditoría empiece por lo que ya se sabe que está roto.

---

## Defectos ya confirmados (no hace falta buscarlos, hay que arreglarlos)

| # | Defecto | Evidencia | Dónde |
|---|---|---|---|
| 1 | El RUT no está homologado **entre** industrias: conviven 3 formatos. Un `JOIN` entre sectores devuelve **0 filas en silencio** | 31 columnas inventariadas | [`rut_formatos_2026-09-29.md`](rut_formatos_2026-09-29.md) |
| 2 | En `corredoras_bolsa`, `maestro.rut = balance.rut` da **0**; por `rut_dv` da 24. Falla **dentro** de una industria | verificado | ídem |
| 3 | `agf_lista_entidades.fondos_inversion_administrados` = **0 en los 72 registros** | la consulta sugerida «Ranking de AGF…» devuelve tabla vacía | extractor de AGF |
| 4 | `fi_bienes_raices` está **vacía**: su manifiesto apunta a `_vacio.parquet` (2.589 B, 0 filas) | la consulta sugerida «Bienes raíces por comuna» devuelve vacío | `outputs/fi/bienes_raices/` |
| 5 | El catálogo de descargas **no cuenta** `bancos_balance` ni `bancos_resultados` (`filasReales: false`), y publica 8.942.793 filas cuando el total real es **10.870.757** | 1.927.964 filas sin contar | `scripts/build_download_catalog.py` |
| 6 | `data_manifest.json` declara **49** tablas; el producto registra **52** | desalineado | `data_manifest.json` |
| 7 | 10 workflows apuntan a la rama muerta `arena/01a0e952-monitor-financiero-chile` | | `.github/workflows/` |
| 8 | Sin `LICENSE`, aunque el README declara licencia | | raíz |
| 9 | `scratch/` y `FSB_Patrimonio_Separado (4).xlsx` están versionados | | raíz |

Herramienta nueva para vigilar 3 y 4:

```bash
python3 scripts/audit_consultas_sugeridas.py          # informe
python3 scripts/audit_consultas_sugeridas.py --check  # falla si hay rotas
```

Registra las 52 vistas igual que el navegador y ejecuta las 116 consultas sugeridas.
Estado actual: **116 OK · 0 vacías · 0 errores** (la vista `fi_bienes_raices` está documentada como «Sin datos» y su consulta va en `VACIAS_ESPERADAS`; la otra vacía era el defecto de formato RUT, ver `docs/notas/rut_formatos_2026-09-29.md`).

---

## Eficiencia: por dónde empezar

### 1. Arranque en frío — el problema número uno

Medido: **~23 s en frío** contra **3,5 ms en caliente** para la misma consulta
(65 filas sobre `seguros_lista_entidades`). El usuario que llega por primera vez espera
23 segundos mirando una pantalla; el que ya tiene el motor cargado obtiene respuestas
instantáneas. Toda la percepción de calidad del producto está en ese primer minuto.

Componentes a medir por separado, que hoy están mezclados:

- descarga del bundle WASM (~18 MB),
- instanciación de DuckDB,
- registro de las 52 vistas semánticas al arrancar.

Preguntas que merecen respuesta:

- ¿Hace falta registrar las 52 vistas al inicio, o pueden crearse **la primera vez que
  se nombran**? Es el candidato más prometedor: la mayoría de visitas tocan una o dos.
- ¿Están bien las cabeceras de caché de GitHub Pages para el `.wasm`? Si no se cachea,
  cada visita paga los 18 MB.
- ¿Se puede mostrar la interfaz utilizable **antes** de que termine la carga, en vez de
  bloquear? Un esqueleto con las tablas y el catálogo ya sirve.
- ¿Hay una variante más pequeña del bundle para el camino habitual?

### 2. Poda de particiones — probablemente la mayor palanca sobre el dato

Varias vistas son muchos ficheros (`ffmm_cartera_nacional`, `seguros_renta_fija`,
`bancos_*` con 55 particiones mensuales). La pregunta es si una consulta con
`WHERE periodo = (SELECT max(periodo) FROM …)` **descarga solo la partición necesaria o
las descarga todas**. Con HTTP range requests DuckDB puede podar, pero la subconsulta
`max(periodo)` puede forzar la lectura completa.

Cómo medirlo: pestaña de red del navegador, bytes transferidos por consulta. Si se están
bajando todas las particiones, conviene exponer el período como columna de partición o
materializar un índice de períodos por tabla.

### 3. Tamaño y forma de los Parquet

262 MB publicados. Revisar compresión (zstd frente a snappy), tamaño de *row group* y
uso de diccionarios. Un *row group* demasiado grande impide podar; demasiado pequeño
multiplica las peticiones.

### 4. Robustez del motor en el cliente

El respaldo por CDN cubre el caso general, pero **no hay bundle `mvp` local** para
navegadores sin WASM exception handling. Conviene decidir si se soporta o si se detecta
y se avisa con claridad en vez de fallar.

---

## Funcionalidades: qué probar

- **Las 116 consultas sugeridas** ya tienen arnés; mantenerlo en verde.
- **Recorrido completo de las 7 pestañas** con el producto servido de verdad
  (`python3 -m http.server` sobre `docs/`), no solo con auditorías estáticas.
- **Exportaciones**: CSV, Excel y Parquet sobre un resultado grande y sobre uno vacío.
- **Comportamiento con datos ausentes**: el README promete que la web dice
  «no disponible» y nunca inventa un número. Conviene comprobarlo a propósito.
- **`fi_bienes_raices` vacía**: decidir entre rellenarla, ocultarla de la interfaz o
  marcarla explícitamente como sin datos. Hoy ofrece una consulta que no devuelve nada.

---

## Contexto que ahorra tiempo

- Las vistas se declaran en `docs/js/duckdb_client.js` (`SEMANTIC_VIEWS`), con
  `file:` o `manifest:` y un `where:` opcional. Los alias antiguos están en
  `LEGACY_VIEW_ALIASES` y **los regenera** `scripts/normalizar_vocabulario.py`: no
  editarlos a mano.
- Las consultas sugeridas viven en `docs/js/sidebar.js` como pares `{ label, query }`.
- Auditorías que deben quedar en verde:
  `audit_navigation.py`, `audit_interfaz.py`, `normalizar_vocabulario.py --check`,
  `build_download_catalog.py --check`, `audit_normativa_web.js`,
  `audit_automatizacion.py` y el nuevo `audit_consultas_sugeridas.py`.
- `audit_secretos.py` no corre en un clon *shallow*; `audit_interfaz_dom.js` necesita
  `jsdom`.
- **No hay navegador headless disponible** en el entorno de agente y no se puede
  instalar: la descarga del binario de Chromium falla. Las medidas de rendimiento en
  navegador las tiene que tomar una persona.
- `duckdb` para Python no está en el entorno por defecto; se instaló en un venv aparte
  para poder calcular resultados reales.

---

## Un aviso sobre el método

La primera versión del arnés de consultas informó de **7** consultas vacías. Cinco eran
falsos positivos: el desescapado de cadenas JS rompía los literales con tildes dentro del
SQL. El número correcto es **2**.

Conviene desconfiar del primer número que dé cualquier auditoría nueva y comprobar a mano
un par de casos antes de declararlos defectos.
