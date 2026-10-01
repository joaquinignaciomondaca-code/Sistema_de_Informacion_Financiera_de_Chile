# Revisión de cobertura de fondos de inversión — 2026-06

**Conclusión:** no falta una categoría completa. Se publican rescatables y no rescatables, y el contraste de **768 casos** no recuperó estados de junio intercambiando FIRES/FINRE. Sí hay **tres fondos del registro actual fuera de la copia local del padrón** y una **serie histórica todavía pendiente**. No se agregaron importes sin fuente ni se fabricaron estados vacíos.

**Base del conteo:** los 1.679 RUN de la publicación inicial usan la copia del padrón cuyo proceso de carteras declara actualización `2026-09-28T17:20:36+00:00`; el contraste CMF de esta revisión encontró 1.682 RUN únicos. Las URL y fechas de consulta están en el JSON adjunto. La vigencia de la tabla siguiente es la de esa copia local, no una certificación de vigencia legal a junio ni un padrón actualizado hoy.

## Rescatables y no rescatables

Los datos publicados incluyen **FIRES (rescatables)** y **FINRE (no rescatables)**.
El padrón incluye fondos vigentes y no vigentes. Estar registrado no implica tener un envío en cada cierre.

| Tipo | Vigencia actual | Padrón | Con EEFF | Sin información del cierre | Excluidos | Pendientes |
|---|---|---:|---:|---:|---:|---:|
| FINRE | Vigente | 826 | 760 | 63 | 3 | 0 |
| FINRE | No Vigente | 516 | 6 | 510 | 0 | 0 |
| FIRES | Vigente | 165 | 139 | 23 | 3 | 0 |
| FIRES | No Vigente | 172 | 3 | 169 | 0 | 0 |

**Vigencia actual, no histórica:** esta tabla no afirma cuáles estaban activos al cierre.
Solo está cargado el cierre indicado; falta completar la serie histórica. No se deben fabricar filas de cero para fondos sin envío.

## Contraste directo con la CMF

- Alcance: todas las ausencias del censo y altas; **768** fondos.
- Revisión completa: **sí**.
- Fondos con consultas pendientes en su vigencia correcta: **0**.
- Consultas auxiliares (vigencia incorrecta) pendientes: **0**; se conservan como tales, no como ausencias.
- Ausencias/altas con enlace FIEF en el otro tipo: **0**.
- Ausencias/altas con enlace en su tipo: **0**.
- Enlaces recuperables al cambiar VI por NV: **0**.
- Identificaciones cuyo tipo difiere del padrón: **0**.

Registro CMF cotejado: **1682** RUN únicos en **1683** filas; **3** altas fuera del padrón local y **0** cambios de tipo.

**Ambigüedad de vigencia en el registro oficial:** 9251. Cada RUN se cuenta una sola vez, sin asignarle una vigencia arbitraria.

### Fondos fuera de la copia local del padrón

- **10926 (FINRE) — AMERIS DOVER STREET XII FONDO DE INVERSIÓN**. Inicio declarado: no informado. La incorporación al padrón no supone publicar cifras sin un XML validado.
- **10927 (FINRE) — NEORENTAS DIECINUEVE FONDO DE INVERSIÓN**. Inicio declarado: no informado. La incorporación al padrón no supone publicar cifras sin un XML validado.
- **10928 (FINRE) — FONDO DE INVERSIÓN PRINCIPAL BC XII**. Inicio declarado: no informado. La incorporación al padrón no supone publicar cifras sin un XML validado.

**Resultado del contraste:** en el alcance revisado no se recuperan fondos por intercambiar rescatable/no rescatable. No se está omitiendo una de las dos categorías.

### Fechas y situación declaradas de los faltantes vigentes

| Situación declarada | Fondos |
|---|---:|
| en_liquidacion_sin_eeff_del_cierre | 7 |
| fecha_inicio_no_informada | 48 |
| inicio_posterior_al_cierre | 31 |

Una fecha de inicio vacía significa **no informada**, no prueba que el fondo nunca haya operado. Estar en liquidación o haber terminado operaciones no prueba por sí solo una exención de reportar.

### Detalle de faltantes vigentes

| RUN | Tipo | Fondo | Inicio declarado | Término declarado | Situación |
|---|---|---|---|---|---|
| 9373 | FIRES | FONDO DE INVERSIÓN SARTOR TACTICO EN LIQUIDACIÓN | 2016-09-06 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 9392 | FIRES | FONDO DE INVERSIÓN SARTOR LEASING EN LIQUIDACIÓN | 2016-10-17 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 9553 | FIRES | FONDO DE INVERSIÓN SARTOR PROYECCIÓN EN LIQUIDACIÓN | 2017-12-01 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 9628 | FIRES | FONDO DE INVERSIÓN SARTOR TACTICO INTERNACIONAL EN LIQUIDACIÓN | 2018-08-07 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 9882 | FIRES | FONDO DE INVERSIÓN SARTOR TÁCTICO PERÚ (EN LIQUIDACIÓN) | 2020-11-09 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 10275 | FIRES | VINCI COMPASS EQUILIBRIO FONDO DE INVERSIÓN | 2026-09-25 | No informada | inicio_posterior_al_cierre |
| 10286 | FIRES | FONDO DE INVERSIÓN SARTOR CAPITAL EFECTIVO EN LIQUIDACIÓN | 2022-08-01 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 10469 | FIRES | FONDO DE INVERSIÓN SARTOR FACTURAS USD (EN LIQUIDACIÓN) | 2023-06-19 | No informada | en_liquidacion_sin_eeff_del_cierre |
| 10702 | FINRE | FONDO DE INVERSIÓN FALCOM GTCR SGF II | No informada | No informada | fecha_inicio_no_informada |
| 10706 | FINRE | AMERIS NORDIC EVO II FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10708 | FINRE | FONDO DE INVERSIÓN LINK – DEUDA PRIVADA RENTAS ERNC II | 2026-10-01 | No informada | inicio_posterior_al_cierre |
| 10716 | FINRE | PICTON - EQT BPEA IX FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10731 | FINRE | VINCI COMPASS BCP ASIA III PRIVATE EQUITY FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10752 | FINRE | VOLCOMCAPITAL INFRAESTRUCTURA V FONDO DE INVERSIÓN | 2026-09-09 | No informada | inicio_posterior_al_cierre |
| 10761 | FINRE | PICTON - GREAT HILL PARTNERS IX FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10782 | FIRES | VINCI COMPASS RENDIMIENTO CONSERVADOR FONDO DE INVERSIÓN | 2026-09-25 | No informada | inicio_posterior_al_cierre |
| 10791 | FINRE | VINCI COMPASS CINVEN SF2 PRIVATE EQUITY FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10795 | FINRE | FONDO DE INVERSIÓN FALCOM PORTFOLIO ADVISORS PRIVATE DEBT IV | No informada | No informada | fecha_inicio_no_informada |
| 10797 | FINRE | BICE STEPSTONE VI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10803 | FINRE | VOLCOMCAPITAL INFRAESTRUCTURA VI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10804 | FINRE | VINCI COMPASS SP X PRIVATE EQUITY FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10808 | FINRE | VINCI COMPASS LCP XI PRIVATE EQUITY FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10812 | FINRE | AMERIS AATECH DEUDA HIPOTECARIA FONDO DE INVERSIÓN | 2026-07-20 | No informada | inicio_posterior_al_cierre |
| 10817 | FINRE | VOLCOMCAPITAL CATALYST III FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10818 | FINRE | VOLCOMCAPITAL HPS SIP VI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10822 | FINRE | BICE HINES DIRECT INVESTMENTS FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10828 | FINRE | VINCI COMPASS QE VI INFRASTRUCTURE FONDO DE INVERSIÓN. | No informada | No informada | fecha_inicio_no_informada |
| 10831 | FINRE | AMERIS PRIVATE EQUITY NORDIC XII FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10832 | FIRES | FONDO DE INVERSIÓN CREDICORP CAPITAL CARTERA SELECTA | No informada | No informada | fecha_inicio_no_informada |
| 10833 | FINRE | MONEDA GSI RENTAS TRANSICIÓN ENERGÉTICA IV - DATA CENTERS ESPAÑA FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10838 | FINRE | BTG PACTUAL RENTA INDUSTRIAL DLS I FONDO DE INVERSIÓN | 2026-07-29 | No informada | inicio_posterior_al_cierre |
| 10840 | FINRE | FONDO DE INVERSIÓN LINK – INFLEXION BUYOUT VII | No informada | No informada | fecha_inicio_no_informada |
| 10848 | FINRE | PICTON - EQT XI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10849 | FINRE | VOLCOMCAPITAL MID MARKET III FONDO DE INVERSION | No informada | No informada | fecha_inicio_no_informada |
| 10852 | FINRE | BICE STEPSTONE SSOF VI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10853 | FINRE | CHILE RENEWABLES I FONDO DE INVERSIÓN | 2026-08-28 | No informada | inicio_posterior_al_cierre |
| 10854 | FINRE | VOLCOMCAPITAL CREDIT VI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10856 | FINRE | TAURUS CASPICHE FONDO DE INVERSIÓN | 2026-07-13 | No informada | inicio_posterior_al_cierre |
| 10857 | FINRE | MONEDA PATRIA COINVESTMENT II FONDO DE INVERSIÓN | 2026-07-10 | No informada | inicio_posterior_al_cierre |
| 10859 | FINRE | FONDO DE INVERSIÓN PRUDENTIAL CHILE LOGÍSTICO I | 2026-08-17 | No informada | inicio_posterior_al_cierre |
| 10860 | FINRE | PICTON - TJC RESOLUTE VII FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10864 | FIRES | FONDO DE INVERSION ETF SINGULAR BRAZIL EQUITIES | 2026-08-19 | No informada | inicio_posterior_al_cierre |
| 10867 | FINRE | FONDO DE INVERSION LINK - EURO RETORNO PREFERENTE II | 2026-08-11 | No informada | inicio_posterior_al_cierre |
| 10869 | FINRE | FONDO DE INVERSIÓN PRINCIPAL ADVENT GPE XI | No informada | No informada | fecha_inicio_no_informada |
| 10872 | FINRE | BTG PACTUAL FINANCIAMIENTO INMOBILIARIO PREFERENTE II FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10873 | FINRE | ARRAYÁN-LINK RENTA ACTIVA FONDO DE INVERSIÓN | 2026-07-13 | No informada | inicio_posterior_al_cierre |
| 10874 | FINRE | VINCI COMPASS CRÉDITO CHILE FONDO DE INVERSIÓN | 2026-07-01 | No informada | inicio_posterior_al_cierre |
| 10875 | FINRE | FONDO DE INVERSIÓN FALCOM WPP PRIVATE EQUITY XI | 2026-08-31 | No informada | inicio_posterior_al_cierre |
| 10876 | FINRE | FONDO DE INVERSIÓN CREDICORP CAPITAL TRITON SMALLER MID-CAP FUND I | No informada | No informada | fecha_inicio_no_informada |
| 10878 | FIRES | FONDO DE INVERSIÓN LARRAINVIAL LATAM EQUITIES | 2026-08-06 | No informada | inicio_posterior_al_cierre |
| 10879 | FINRE | FONDO DE INVERSIÓN FYNSA GALGO III | 2026-08-27 | No informada | inicio_posterior_al_cierre |
| 10880 | FIRES | FONDO DE INVERSIÓN SINGULAR FARELLONES CHILEAN EQUITIES | 2026-08-27 | No informada | inicio_posterior_al_cierre |
| 10881 | FINRE | FONDO DE INVERSIÓN FYNSA DEUDA AUTOMOTRIZ PERÚ | No informada | No informada | fecha_inicio_no_informada |
| 10883 | FINRE | VOLCOMCAPITAL SEMILÍQUIDO PE FONDO DE INVERSIÓN | 2026-09-23 | No informada | inicio_posterior_al_cierre |
| 10884 | FINRE | PICTON - FRANCISCO PARTNERS VIII FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10885 | FINRE | FONDO DE INVERSIÓN ACTIVA DEUDA AUTOMOTRIZ GLOBAL IV | 2026-08-24 | No informada | inicio_posterior_al_cierre |
| 10886 | FINRE | FONDO DE INVERSIÓN FALCOM GTCR PRIVATE EQUITY XV | No informada | No informada | fecha_inicio_no_informada |
| 10887 | FINRE | ATLANTA HEALTH INVESTMENTS FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10889 | FINRE | FONDO DE INVERSIÓN PRINCIPAL REVERENCE CAPITAL PARTNERS PE IV | No informada | No informada | fecha_inicio_no_informada |
| 10891 | FINRE | PERÚ INMOBILIARIO III FONDO DE INVERSIÓN | 2026-09-16 | No informada | inicio_posterior_al_cierre |
| 10893 | FIRES | BTG PACTUAL ETF ASIA SEMICONDUCTORS FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10894 | FINRE | AMERIS SCHRODERS PE SEMI-LÍQUIDO FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10895 | FIRES | FONDO DE INVERSIÓN ETF SINGULAR HIGH YIELD | 2026-08-17 | No informada | inicio_posterior_al_cierre |
| 10896 | FIRES | FONDO DE INVERSIÓN ETF SINGULAR JAPAN | 2026-10-01 | No informada | inicio_posterior_al_cierre |
| 10897 | FIRES | FONDO DE INVERSIÓN ETF SINGULAR EMERGING MARKETS | 2026-08-17 | No informada | inicio_posterior_al_cierre |
| 10898 | FIRES | FONDO DE INVERSIÓN ETF SINGULAR BITCOIN | 2026-08-17 | No informada | inicio_posterior_al_cierre |
| 10900 | FIRES | FONDO DE INVERSIÓN ETF SINGULAR EUROPE | 2026-08-17 | No informada | inicio_posterior_al_cierre |
| 10905 | FINRE | TOESCA INFRAESTRUCTURA SS FONDO DE INVERSIÓN | 2026-08-24 | No informada | inicio_posterior_al_cierre |
| 10907 | FINRE | BICE INFRAESTRUCTURA GLOBAL FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10908 | FINRE | FONDO DE INVERSIÓN HMC ALPHA VENTURES I | 2026-09-04 | No informada | inicio_posterior_al_cierre |
| 10909 | FINRE | PICTON - TPG TWIN BROOK DL VI FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10910 | FIRES | BTG PACTUAL ETF GLOBAL EMERGING MARKETS EQUITIES FONDO DE INVERSIÓN | 2026-08-24 | No informada | inicio_posterior_al_cierre |
| 10911 | FIRES | BTG PACTUAL ETF EUROPEAN EQUITIES FONDO DE INVERSIÓN | 2026-08-24 | No informada | inicio_posterior_al_cierre |
| 10912 | FINRE | FONDO DE INVERSION RENTAS LAB ORIGEN | No informada | No informada | fecha_inicio_no_informada |
| 10913 | FINRE | FONDO DE INVERSIÓN CDV PACÍFICO II | No informada | No informada | fecha_inicio_no_informada |
| 10914 | FINRE | PICTON - KKR ASIA V FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10915 | FINRE | VINCI COMPASS LS 13 FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10916 | FINRE | FONDO DE INVERSIÓN GNP VII CLP | 2026-08-25 | No informada | inicio_posterior_al_cierre |
| 10918 | FINRE | FONDO DE INVERSION SINGULAR BIF VI INFRASTRUCTURE | No informada | No informada | fecha_inicio_no_informada |
| 10919 | FIRES | BTG PACTUAL ETF US HIGH YIELD FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10920 | FINRE | BICE VENDOR FINANCE I FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10921 | FINRE | ALZA DESARROLLO III FONDO DE INVERSION | No informada | No informada | fecha_inicio_no_informada |
| 10922 | FIRES | BTG PACTUAL RENDIMIENTO TOTAL FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10923 | FINRE | AMERIS AIP IX FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |
| 10924 | FINRE | FONDO DE INVERSIÓN BCI HIPOTECARIO IV | No informada | No informada | fecha_inicio_no_informada |
| 10925 | FINRE | MONEDA PATRIA LATAM PRIVATE CREDIT II FONDO DE INVERSIÓN | No informada | No informada | fecha_inicio_no_informada |

## Exclusiones conocidas

- **9101 (FIRES)**: CMF rechaza explícitamente la descarga: ACCION NO PERMITIDA 16.
- **9203 (FIRES)**: CMF rechaza explícitamente la descarga: ACCION NO PERMITIDA 16.
- **9787 (FINRE)**: CMF rechaza explícitamente la descarga: ACCION NO PERMITIDA 16.
- **9943 (FINRE)**: CMF rechaza explícitamente la descarga: ACCION NO PERMITIDA 16.
- **10641 (FINRE)**: CMF rechaza explícitamente la descarga: ACCION NO PERMITIDA 16.
- **10790 (FIRES)**: balance: moneda/escala de ficha no coincide con COP.

## Trazabilidad y límites

- Esta revisión no modifica estados financieros, no convierte moneda, no rellena ceros y no descarga XML rechazados.
- El JSON adjunto conserva las URL, fecha y SHA-256 de cada respuesta revisada. Los originales quedan en staging/artifact, fuera de los datos publicados.
- `sin_ficha` en la categoría alternativa no equivale a `sin_informacion` del cierre. Desafíos, cortes y errores quedan pendientes.
- La vida observada de carteras no se usa como prueba de vida legal ni para omitir fondos de las consultas.
- Prioridad pendiente: completar el histórico, mantener actualizado el padrón y resolver las exclusiones y las ausencias con inicio anterior al cierre sin inventar cifras.

## Cambios de código y trabajo pendiente

- **Corregido:** la extracción de EEFF toma `VI`/`NV` del padrón en vez de consultar siempre `VI`. Cambios de tipo o vigencia invalidan la caché pertinente; no se reutiliza el cotejo de una ficha distinta.
- **Añadido:** revisor reproducible y workflow de solo lectura para los dos tipos, las cuatro listas, fechas de operación, altas y ambigüedades. Los originales comprimidos de las listas permiten reproducir el solapamiento del RUN 9251 y comprobar hashes sin red.
- **Verificado:** 97 pruebas FI y 440 pruebas unitarias del repositorio aprobadas; 35.570 identidades de los datos publicados, sin fallas. Las cantidades publicadas siguen siendo 908 fondos, 66.864 filas de balance y 97.860 de resultados.
- **Pendiente:** sincronizar los RUN 10926, 10927 y 10928 en el maestro/censo local, completar la historia disponible y resolver las seis exclusiones de fuente. Las tres altas están identificadas en el diagnóstico, **no se presentan como ya incorporadas a los datos del sitio**.
- No se interpretan los 48 inicios no informados como evidencia suficiente de que nunca hubo operaciones. Para estos fondos solo se confirmó que sus fichas, en ambos tipos, no enlazan FIEF para el cierre solicitado.

El flujo temporal utilizado para recuperar evidencia desde Actions se retiró. La revisión no introdujo permisos de publicación de datos ni modificó los Parquet financieros.
