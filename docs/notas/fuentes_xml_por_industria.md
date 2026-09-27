# Fuentes XML/XBRL por industria (auditoría y oportunidades)

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

Retirados de publicación (Parquet, JSON, explorador, diccionario, visor y ERD). El pipeline queda con
`PUBLICAR_PACTOS_REPOS = False`, de modo que **sigue extrayendo y publicando solo las carátulas XML**.
Motivo: los niveles 2 y 3 se derivan de texto de PDF con heurísticas (contrapartes, plazos, colaterales),
sin cotejo por fila contra el documento fuente, y con `valor_mercado_m_clp = monto_pactado_m_clp`.

## 3. Fuentes XML/XBRL por industria

Código de la última columna: **Verificado** = comprobado en la ficha CMF; **Referenciado** = documentado por
CMF pero sin probar la descarga; **No aplica** = no existe ese formato en esa fuente.

| Industria | Fuente / módulo | Formato confirmado | Estado |
| :--- | :--- | :--- | :--- |
| Corredoras de bolsa (`COBOL`) | `pestania=3` Información Financiera | **XML IFRS** (`ifrs_xml_verarchivo.php?archivo=IVEF…`) | Verificado y en uso |
| Fondos mutuos (`RGFMU`) | `pestania=3` con `tipo_norma=IFRS` | **XML IFRS** (`archivo=FMEF…`) | Verificado (hoy se lee HTML/PDF) |
| Emisores de valores (`RVEMI`, incluye retail financiero y CCAF inscritas) | `pestania=3` con `tipo=I|C&tipo_norma=IFRS` | **XBRL + PDF** ("Estados financieros (XBRL)") | Verificado |
| AGF (`RGAGF`) | `pestania=3` con `tipo_norma=IFRS` | **XBRL + PDF**; CMF advierte "contenido de los archivos XBRL está en revisión" | Verificado |
| Cajas de compensación (CCAF) | Listado CMF de envíos IFRS (`novedades_envio_sa_ifrs.php`) | **XBRL** | Verificado y en uso |
| Compañías de seguros (vida y generales) | Módulos CMF "IFRS Mercado de Seguros" / "XBRL Mercado de Seguros" (taxonomías CL-HS, CL-BS) | **XBRL + PDF** | Referenciado (falta probar la descarga por entidad) |
| Fondos de inversión (`FINRE`, `FIRES`) | `pestania=29` Información Financiera (y `59` Cartera, `62` Publicación EEFF) | Módulo IFRS existe; formato XML por confirmar con un fondo de período antiguo | Parcial (hoy se lee PDF de `pestania=62`) |
| Cooperativas de ahorro y crédito | Portal CMF de estadísticas `626` (serie mensual) | Planilla/serie, no IFRS XML identificado | No aplica por ahora |
| Bancos | Módulo bancos: PDF de EEFF + reportes mensuales/ZIP (no IFRS XML) | PDF/ZIP | No aplica |
| Sistemas de pago / FinTech | Ficha de identificación CMF | Sin módulo de EEFF | No aplica |
| AFP (pensiones) | Superintendencia de Pensiones: XML de carteras y cuadros | **XML propios de la SP** | Verificado y en uso |
| Macro | BCCh BDE (series) y SII (tipo de cambio) | JSON/planilla, no XML IFRS | No aplica |

Taxonomías XBRL vigentes publicadas por CMF: `CL-CI` (emisores de valores), `CL-HB` (holding bancos),
`CL-HS` (holding seguros), `CL-CC` (cajas de compensación), `CL-EI` (entidades informantes),
`CL-BS` (holding bancos y seguros).

## 4. Prioridad sugerida de incorporación

1. **Fondos mutuos**: cambiar la lectura de HTML/PDF por el XML `FMEF` ya verificado.
2. **AGF**: incorporar XBRL (con cotejo contra el PDF, por la advertencia de CMF).
3. **Fondos de inversión**: probar si `pestania=29` entrega XML para las series anuales.
4. **Seguros**: probar descarga XBRL por entidad y comparar con los PDF actuales.
5. **Cooperativas**: confirmar si existe envío IFRS/XBRL (como CCAF) antes de reemplazar la serie.

Ninguna de estas incorporaciones publica datos hasta pasar el mismo cotejo de muestra aplicado en Corredoras.
