# Fuentes XML/XBRL por industria (auditoría y oportunidades)

> **Estado al 2026-10-01.** Esta nota es un registro del 2026-09-27 y varias cosas que menciona ya
> no existen: el 2026-09-28 se eliminaron la sonda `scripts/probe_xml_sources.py`, los workflows
> `probe_xml_sources.yml` y `factoring_leasing_sample.yml` y el laboratorio XML/XBRL (ver «Sin
> sondas ni laboratorios» en `pipelines/auto/README.md`); `corredoras_bolsa_caratula_eeff_historico`
> ya no se publica (corredores y agentes publican balance y resultados desde el Excel FECU:
> `corredoras_bolsa/scripts/actualizar_eeff.py`); y factoring/leasing publica la serie IFRS completa
> desde el TXT de la CMF (`factoring_leasing/scripts/`), con la muestra de dos filas ya retirada de
> la web. Las secciones 1 a 4 se conservan solo como evidencia del cotejo de entonces.
>
> **Fondos mutuos (2026-10-01):** la medición real del XML `FMEF` desde Actions está en
> `ffmm_estados_financieros_xml_2026-10-01.md`. La fila «Fondos mutuos … hoy se lee HTML/PDF» de la tabla 3 y la
> prioridad n.º 1 de la sección 5 son históricas: desde el 2026-10-01 el sitio publica el balance y el estado de resultados
> anuales de los fondos mutuos (`ffmm_balance`, `ffmm_resultados`), leídos del XML de cada fondo.

Fecha de revisión: 2026-09-27
Alcance: verificar **qué industrias del sitio pueden alimentarse de XML/XBRL oficiales** en lugar de PDF,
HTML o planillas, y dejar registro del cotejo hecho para Corredoras de Bolsa.

> Nota: los enlaces con parámetro `auth=` de CMF son **efímeros** (token por sesión). No se guardan en
> el repositorio; el extractor debe obtenerlos de la ficha en cada corrida.

## 1. Auditoría puntual — Corredoras de Bolsa (COBOL, XML IFRS)

Origen confirmado: ficha CMF `entidad.php?...&tipoentidad=COBOL&pestania=3`, que publica el archivo
`ifrs_xml_verarchivo.php?archivo=IVEF<timestamp>_<rut>.xml&&periodo=AAAAMM&&path=/web/ifrs_xml/ivifr/xml/`
más la tabla HTML del estado de situación financiera ("Expresado en miles de Pesos").

Cotejo de muestra contra CMF (miles de CLP, Total Activos):

| Corredora | Período | CMF (ficha) | Publicado (`corredoras_bolsa_caratula_eeff_historico`) | Resultado |
| :--- | :--- | ---: | ---: | :--- |
| BANCHILE CORREDORES DE BOLSA S.A. (96.571.220-8) | 2024-12 | 807.006.393 | 807.006.393 | Coincide |
| BANCHILE CORREDORES DE BOLSA S.A. (96.571.220-8) | 2023-12 | 894.203.128 | 894.203.128 | Coincide |

Conclusiones de la muestra:
* La ruta XML de carátulas **reproduce exactamente** el valor de la ficha oficial; la unidad es **miles de pesos**.
* Las columnas derivadas (`total_pasivos_m_clp`, `patrimonio_neto_m_clp`, `cuadre_balance`) cuadran 621/621 en el
  archivo publicado, pero el cuadre interno **no** certifica por sí solo el contenido.
* Muestra pequeña (2 filas / 1 entidad / 2 períodos): no reemplaza un cotejo fila a fila del universo completo.

Riesgos detectados en el código de extracción (pendientes de corrección, no corregidos aún):
1. El tipo de cambio de respaldo cae a `900` si falta el dato macro, inflando el valor `_usd`.
2. Los fallos de lectura numérica se convierten silenciosamente en `0.0`.
3. El dígito verificador se recalcula en lugar de contrastarse con el recibido.
4. Se descartan excepciones por corredora/período con `except: pass`, sin bitácora de faltantes.

## 2. Estado de los pactos REPO de corredoras

Retirados de publicación: los cuatro archivos (Parquet y JSON) y sus accesos en el explorador
lateral, el visor de datos, el diccionario y el cliente SQL. **Corrección (auditoría 2026-09-27):**
`data_manifest.json` y `erd_graph.js` nunca referenciaban esas tablas, así que no hubo nada que
quitar allí; una versión anterior de este texto lo afirmaba de más. El pipeline queda con
`PUBLICAR_PACTOS_REPOS = False`, de modo que **sigue extrayendo y publicando solo las carátulas XML**.
Motivo: los niveles 2 y 3 se derivan de texto de PDF con heurísticas (contrapartes, plazos, colaterales),
sin cotejo por fila contra el documento fuente, y con `valor_mercado_m_clp = monto_pactado_m_clp`.

## 3. Fuentes XML/XBRL por industria

Código de la última columna: **Verificado** = comprobado en la ficha CMF; **Referenciado** = documentado por
CMF pero sin probar la descarga; **No aplica** = no existe ese formato en esa fuente.

| Industria | Fuente / módulo | Formato confirmado | Estado |
| :--- | :--- | :--- | :--- |
| Corredoras de bolsa (`COBOL`) | `pestania=3` Información Financiera | **XML IFRS** (`ifrs_xml_verarchivo.php?archivo=IVEF…`, ruta `/web/ifrs_xml/ivifr/xml/`) | Verificado y en uso |
| Fondos mutuos (`RGFMU`) | `pestania=3` con `tipo_norma=IFRS` | **XML IFRS** (`archivo=FMEF…`, ruta `/web/ifrs_xml/fmifr/xml/`) | Verificado (hoy se lee HTML/PDF) |
| Fondos de inversión rescatables (`FIRES`) | `pestania=29` Información Financiera (IFRS) | **XML IFRS** (`archivo=FIEF…`, ruta `/web/ifrs_xml/fiifr/xml/`) | Verificado (hoy se lee PDF de `pestania=62`) |
| Emisores de valores (`RVEMI`, incluye retail financiero y CCAF inscritas) | `pestania=3` con `tipo=I|C&tipo_norma=IFRS` | **XBRL + PDF** ("Estados financieros (XBRL)") | Verificado |
| Factoring (muestra: Factoring Security S.A., `RVEMI`) | `pestania=3`, balance individual 2022-06 | **XBRL + PDF + tabla HTML CMF**; también existe archivo masivo estructurado delimitado por `;` en `estadisticas/ver_archivo.php` (no es XML) | **Cotejo aprobado para una muestra de 2 filas**; publicado en la web con advertencia de alcance |
| Leasing (muestra: Unidad Leasing Habitacional S.A., `RGEIN`) | `pestania=3`, balance individual 2022-09 | **XBRL + PDF + tabla HTML CMF**; mismo archivo masivo estructurado delimitado por `;` | **Cotejo aprobado para una muestra de 2 filas**; publicado en la web con advertencia de alcance |
| AGF (`RGAGF`) | `pestania=3` con `tipo_norma=IFRS` | **XBRL + PDF**; CMF advierte "contenido de los archivos XBRL está en revisión" | Verificado |
| Cajas de compensación (CCAF) | Listado CMF de envíos IFRS (`novedades_envio_sa_ifrs.php`) | **XBRL** | Verificado y en uso |
| Compañías de seguros (vida y generales) | Módulos CMF "IFRS Mercado de Seguros" / "XBRL Mercado de Seguros" (taxonomías CL-HS, CL-BS) | **XBRL + PDF** | Referenciado (falta probar la descarga por entidad) |
| Fondos de inversión no rescatables (`FINRE`) | `pestania=29` Información Financiera | Mismo módulo IFRS; XML por confirmar con un fondo de período antiguo | Parcial (hoy se lee PDF de `pestania=62`) |
| Cooperativas de ahorro y crédito | Portal CMF de estadísticas `626` (serie mensual) | Planilla/serie, no IFRS XML identificado | No aplica por ahora |
| Bancos | Módulo bancos: PDF de EEFF + reportes mensuales/ZIP (no IFRS XML) | PDF/ZIP | No aplica |
| Sistemas de pago / FinTech | Ficha de identificación CMF | Sin módulo de EEFF | No aplica |
| AFP (pensiones) | Superintendencia de Pensiones: XML de carteras y cuadros | **XML propios de la SP** | Verificado y en uso |
| Macro | BCCh BDE (series) y SII (tipo de cambio) | JSON/planilla, no XML IFRS | No aplica |

Taxonomías XBRL vigentes publicadas por CMF: `CL-CI` (emisores de valores), `CL-HB` (holding bancos),
`CL-HS` (holding seguros), `CL-CC` (cajas de compensación), `CL-EI` (entidades informantes),
`CL-BS` (holding bancos y seguros).

### 3.1 Esquema del XML de fondos mutuos (`FMEF`, verificado)

```xml
<IFRS>
  <Identificacion>
    <RUTFondoInforma>8490</RUTFondoInforma><DVFondoInforma>5</DVFondoInforma>
    <NombreEntidadInforma>Fondo Mutuo Cruz del Sur Selectivo</NombreEntidadInforma>
    <RUTAdministradora>96639280</RUTAdministradora>
  </Identificacion>
  <DatosPeriodo><MonedaPresentacionEstadosFinancieros>$$</MonedaPresentacionEstadosFinancieros>
    <PeriodoPresentacionEstadosFinancieros><Mes>12</Mes><Anio>2014</Anio></PeriodoPresentacionEstadosFinancieros>
    <NombreAuditoresExternos>Deloitte</NombreAuditoresExternos>
    <EstadoFlujoEfectivoMetodoDirecto>S</EstadoFlujoEfectivoMetodoDirecto>
  </DatosPeriodo>
  <Contextos><PeriodoActual>…</PeriodoActual><PeriodoAnterior>…</PeriodoAnterior></Contextos>
  <Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual" Nota="…">2957448</Cuenta>
</IFRS>
```

Ventajas frente a la ruta actual (HTML + PDF de notas): cuentas con código estable, nota asociada
por cuenta, período actual y anterior en el mismo archivo, moneda de presentación declarada,
auditores externos y contador de notas informadas. Mismo patrón de lectura que ya usa Corredoras.

## 4. Sonda automática (`scripts/probe_xml_sources.py`)

Para no depender de revisar esto a mano, el repositorio incluye una sonda de solo lectura:

* `python scripts/probe_xml_sources.py` recorre las industrias, abre la ficha CMF de cada muestra,
  detecta el enlace XML/XBRL, descarga el archivo cuando existe y valida: raíz del XML, número de
  cuentas, presencia de `TotalActivos`/`TotalActivo` y la unidad declarada ("miles de Pesos"/"miles de Dolar").
* Salida: `.local-data/xml_probe/xml_sources_<fecha>.{json,md}` (carpeta ignorada por git). No escribe
  Parquet del sitio, no publica y no hace commit.
* `--fail-on-missing` sirve para CI cuando queramos alertar si una fuente estructurada desaparece.
* Workflow `.github/workflows/probe_xml_sources.yml`: corre a diario (y a mano con `workflow_dispatch`),
  sube el informe como artifact y deja el resumen en el log. No necesita credenciales.

Nota de este entorno: la sonda no pudo alcanzar `www.cmfchile.cl` desde el sandbox (TLS cerrado por el
proxy local); sus resultados quedan como `error_ficha` localmente y se obtienen reales al correr en Actions.

## 5. Prioridad sugerida de incorporación

1. **Fondos mutuos**: cambiar la lectura de HTML/PDF por el XML `FMEF` ya verificado (mayor volumen y menos riesgo).
2. **Fondos de inversión**: usar el XML `FIEF` de `pestania=29` en lugar del PDF de `pestania=62`.
3. **AGF**: incorporar XBRL (con cotejo contra el PDF, por la advertencia de CMF).
4. **Seguros**: identificar `tipoentidad` de la ficha y probar el XBRL de los módulos CL-HS/CL-BS.
5. **Cooperativas**: confirmar si existe envío IFRS/XBRL (como CCAF) antes de reemplazar la serie.

Ninguna de estas incorporaciones publica datos hasta pasar el mismo cotejo de muestra aplicado en Corredoras.

## Factoring y Leasing: evaluación acotada (2026-09-27)

Las fichas [Factoring Security, 2022-06](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=96655860&tipoentidad=RVEMI&vig=VI&control=svs&pestania=3&mm=06&aa=2022&tipo=I&tipo_norma=IFRS) y [Unidad Leasing Habitacional, 2022-09](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=96809970&tipoentidad=RGEIN&vig=VI&control=svs&pestania=3&mm=09&aa=2022&tipo=I&tipo_norma=IFRS) exhiben XBRL, PDF y un balance visible (miles de CLP). CMF advierte que los XBRL están en revisión; no se ha validado el contenido de los ZIP/XBRL contra los PDF. El archivo `ver_archivo.php?inicio=AAAAMM&termino=AAAAMM` da filas `periodo;rut;nombre;I|C;moneda;cuenta;valor;taxonomia;estado`; es **texto delimitado, no XML**. Deben cotejarse entidad, nombre, período, balance individual, unidad, cuatro cuentas y cuadre antes de publicar, sin asumir que los 28 miembros del catálogo tengan EEFF disponibles ni homologar nombre registral sin prueba. El sandbox no accede directamente a CMF (TLS EOF); el workflow `factoring_leasing_sample.yml` ejecuta la sonda en Actions y guarda informe en cuarentena. Ambos casos fueron aprobados y se publican como muestra de dos filas; el resto del sector sigue fuera. Ver docs/notas/cotejo_muestra_factoring_leasing_2026-09-27.md. Los scripts históricos siguen bloqueados.

## Factoring y Leasing: resultado del cotejo (2026-09-27)

Para Factoring Security S.A. (2022-06, individual) y Unidad Leasing Habitacional S.A. (2022-09, individual) el archivo estructurado de CMF y la tabla HTML de la ficha coinciden en activos, pasivos, patrimonio y efectivo, en miles de pesos y con activos = pasivos + patrimonio. Solo esas dos filas, con advertencia visible de alcance, entraron al sitio (`factoring_leasing.eeff_muestra_cmf`). No hay aprobación para el resto del sector, otros períodos, consolidados ni XBRL/PDF. La lista de 28 entidades sigue publicada aparte y sin certificación registral. Detalle en `docs/notas/cotejo_muestra_factoring_leasing_2026-09-27.md`.

**Ampliación solicitada:** además del balance de dos filas, se cotejaron dos cuentas del estado de resultado acumulado contra el archivo estructurado y la ficha CMF en la corrida 36337715177. Se publican en una segunda tabla separada `factoring_leasing.resultados_muestra_cmf` (dos filas). No es el estado de resultado completo.
