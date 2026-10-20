# Recorte visual de industrias (2026-10-20)

## Decisión

El sistema publica 15 industrias, 75 conjuntos y 13,5 millones de filas, pero el valor
está muy concentrado: seguros, fondos mutuos y fondos de inversión suman el 82 % de las
filas, y con bancos, AGF, corredoras y la macro se llega al 99,3 %. Como por ahora no se
extraerán datos nuevos, la web pasa a destacar sólo lo que aporta y deja el resto a mano,
pero fuera del camino.

**El recorte es visual.** No se borró ningún Parquet, manifiesto, vista SQL, identificador
de tabla ni URL de descarga: los enlaces `#sql=` compartidos, las consultas guardadas y
las rutas `outputs/...` siguen funcionando. Todo lo archivado sigue consultable en el
terminal SQL y descargable en *Descargas*.

## Niveles (bandera por sector)

La bandera vive en `docs/vocabulario.json`, clave `alcance.sectores`. Cifras del catálogo
generado el 2026-10-20 (sin la tabla oculta `fi.bienes_raices`):

| Nivel | Sectores | Conjuntos | Filas | % filas |
|---|---|---:|---:|---:|
| **Núcleo · inversión institucional** | Seguros, Fondos Mutuos, Fondos de Inversión | 25 | 11.063.323 | 82,0 % |
| **Instituciones y estados financieros** | Bancos, AGF, Corredoras de Bolsa | 10 | 2.278.665 | 16,9 % |
| **Contexto macroeconómico** | Macroeconomía y Tasas (BCCh) | 24 | 41.413 | 0,3 % |
| **Archivo congelado** | Factoring y Leasing, Securitización (securitizadoras + patrimonios separados), Cajas de Compensación | 11 | 99.967 | 0,7 % |
| **Registro complementario de entidades** | AFP, Cooperativas, Sistemas de Pago, Fintech | 4 | 296 | 0,0 % |

Visible (núcleo + instituciones + contexto): 59 conjuntos y 13.383.401 filas (99,3 %).
Archivo + registro: 15 conjuntos y 100.263 filas (0,7 %).

El plan original hablaba de «26 conjuntos principales»: son 25 porque `fi.bienes_raices`
(0 filas) se oculta.

## Qué cambió en la web

- **Portada (Información).** Las cifras pasan de «15 industrias / 75 tablas» a
  «3 sectores de inversión institucional · 25 conjuntos principales · 11,1 millones de
  registros · cobertura máxima 2001–2026». Tres tarjetas grandes (Seguros, Fondos mutuos,
  Fondos de inversión) con conjuntos, registros y cobertura; una franja compacta con
  Bancos, AGF y Corredoras; un bloque de contexto con la macro en cuatro bloques; un
  enlace discreto a «Archivo y registros complementarios» y una sección «Alcance de esta
  edición» que dice explícitamente que **esta edición no incluye carteras AFP**. Las
  cifras se leen del catálogo (`docs/js/portada.js`), así que siguen solas a los datos.
  Las tablas pequeñas de FI (opciones, pactos) no se promueven en la portada.
- **Explorador.** Ordenado por nivel, con encabezados y cifras por nivel. Archivo y
  registro van al final, en un bloque plegado con el aviso de alcance. La búsqueda los
  encuentra y abre el bloque. AGF sale de «Administración de fondos» a su propio grupo
  (nivel instituciones); el grupo de fondos queda como «Fondos mutuos y de inversión».
  Los nombres de familia ya no se cortan con «…».
- **Mapa relacional.** Filtros agrupados por nivel; los del archivo quedan detrás del
  botón «Archivo y registros». «Vista principal» (antes «Todos») muestra núcleo,
  instituciones y contexto, completos y sin el archivo; «Mapa completo» incluye todo.
  Securitizadoras y patrimonios separados se filtran juntos (con sus enlaces) y el
  registro complementario se ve como una sola página. Se reordenó la posición de los
  nodos por nivel y se eliminó un nodo duplicado de `ccaf.lista_entidades`.
- **Diccionario.** Por defecto muestra el alcance principal, en orden editorial. Archivo y
  registro tienen sus filtros plegados y sus fichas llevan el aviso de alcance. Si una
  búsqueda sólo encuentra fichas archivadas, se ofrece buscar en todo el catálogo.
- **Visor.** Arranca en `seguros.lista_entidades` (antes `afp.lista_entidades`); el
  selector sigue el orden editorial, rotula «Archivo ·» / «Registro ·» y muestra el aviso
  de alcance sobre la grilla de una tabla archivada.
- **Descargas.** Secciones por nivel; archivo y registro plegados al final («59 de 74
  conjuntos · archivo plegado»). Securitizadoras y patrimonios separados forman un solo
  bloque, la lista registro de corredoras va bajo la lista principal y una nota explica
  por qué no se lista `fi.bienes_raices`.
- **Consultas SQL.** Las consultas sugeridas por defecto cubren el núcleo (seguros,
  fondos mutuos y fondos de inversión).

## Limpieza

- `fi.bienes_raices` se oculta mientras la fuente no publique datos (`alcance.tablas_ocultas`).
- Las dos listas de corredoras (las mismas 120 entidades) se ven como una sola entrada:
  la de registro aparece como variante de la principal (`alcance.variantes`).
- La macro pasa de nueve carpetas a cuatro bloques —tasas y curvas; tipo de cambio, UF y
  UTM; actividad y precios; expectativas— más el catálogo de series. Lo genera
  `scripts/build_macro_web.py` (`BLOQUES`); ninguna consulta sugerida se perdió.

Defectos encontrados en el camino y corregidos:

- Dos consultas sugeridas por defecto del terminal (derivados y pactos de seguros)
  usaban columnas que ya no existen y fallaban. `audit_consultas_sugeridas.py` ahora
  también ejecuta los chips de `docs/index.html`.
- En *Descargas*, la lista de archivos de cada conjunto se veía siempre desplegada
  (`.dl-files` anulaba el atributo `hidden`).
- Al abrir el sector AFP en el explorador, el mapa quedaba vacío (`afp_corporativo` no
  coincidía con el sector `pensiones` de sus nodos).

## Qué no cambió

- **Los workflows.** Factoring y leasing (`factoring_leasing_backfill.yml`), securitizadoras
  y CCAF (`ifrs_sectores.yml`) y las listas de entidades (`entidades.yml`) siguen
  programados. Por eso el aviso dice «esta industria no amplía su cobertura en la edición
  actual» y no «sin actualización programada». Si se quiere congelar de verdad, hay que
  quitar esos sectores de sus horarios.
- Los datos publicados, los manifiestos, las vistas SQL y sus alias.

## Cómo ajustar o revertir

Todo sale de `alcance` en `docs/vocabulario.json`:

- `sectores`: nivel de cada sector (`nucleo`, `secundario`, `contexto`, `archivo`, `registro`).
- `visibles`: niveles que se muestran en la navegación principal.
- `orden`: orden editorial de los sectores.
- `agrupaciones`: sectores que se muestran como una sola entrada (Securitización).
- `tablas_ocultas`: tablas fuera de la navegación, con su motivo.
- `variantes`: tablas que se muestran junto a su tabla principal.

Después de editarlo: `python3 scripts/build_download_catalog.py` (el catálogo lleva el
alcance y las cifras de cada nivel; los workflows de datos ya lo regeneran en cada
publicación). Sin catálogo, la web vuelve a la navegación completa.

## Verificación

`audit_navigation.py` (orden por nivel, archivo plegado, tabla oculta, variante y macro en
cuatro bloques), `audit_interfaz_dom.js` (63 comprobaciones en DOM real, incluidas la
portada, el explorador, el mapa, el diccionario, el visor y Descargas),
`audit_web_full.py`, `audit_interfaz.py`, `audit_consultas_sugeridas.py --check`
(146 consultas sugeridas del explorador + 7 del terminal = 153), `normalizar_vocabulario.py --check`, `build_download_catalog.py --check`
y las pruebas unitarias de FI, factoring y leasing y pipelines. `audit_rut_formatos.py`
ya fallaba antes de este cambio (`seguros/acciones/2026.parquet`, RUT `1-9`).
