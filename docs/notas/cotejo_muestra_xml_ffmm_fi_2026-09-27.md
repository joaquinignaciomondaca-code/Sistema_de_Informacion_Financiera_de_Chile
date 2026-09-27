# Cotejo de muestra y Parquet de revisión — FFMM y FI

Fecha: 2026-09-27. Código: `pipelines/xml_eeff/audit_sample.py`.
Actions [36332905593](https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile/actions/runs/36332905593): **success**, dos XML descargados, dos fichas CMF HTML descargadas y cuatro valores cotejados por fondo. El workflow crea `eeff_muestra_cmf.parquet` (2 filas) y `cotejo_muestra.json` **solo como artifact** `cotejo-xml-cmf-muestra`. Como la descarga Azure Blob falla desde este sandbox, reconstruí el Parquet local de las anotaciones base64 del *mismo run*: `.local-data/xml_eeff_muestra/eeff_muestra_cmf.parquet` (15.128 bytes, lectura posterior comprobada). Este archivo está ignorado por Git, no se publica en la web.

| Fondo (RUN) | Corte | Moneda y unidad **según la ficha CMF** | Activo | Pasivo **según taxonomía** | Patrimonio / activo neto | Resultado | Dictamen de esta fila |
|---|---|---|---:|---:|---:|---:|---|
| FFMM 8490 | 2014-12 | miles de pesos | 2.957.448 | 5.947 (excluye activo neto) | 2.951.501 | 3.470 (utilidad después de impuesto) | coinciden XML y HTML |
| FIRES 7064 | 2021-12 | miles de dólares | 24.887 | 24.887 (**incluye** patrimonio) | 24.826 | -122 | coinciden XML y HTML |

Para FIRES el pasivo sin patrimonio es 61 (= 24.887 − 24.826); **no** usar `TotalPasivo` como obligaciones de 24.887 ni convertir `PROM` a CLP. El XML indica `PROM` y `$$` respectivamente; la ficha CMF es la evidencia usada para describir la unidad monetaria, no una inferencia desde `PROM`.

**Identidad:** RUN y DV declarados en el XML coinciden con el registro. Sin embargo, el *nombre histórico* difiere del nombre en el universo actual: FFMM 8490 `Fondo Mutuo Cruz del Sur Selectivo` frente a `FONDO MUTUO SECURITY SELECTIVO`; FIRES 7064 `FONDO DE INVERSION DEUDA LATAM HIGH YIELD` frente a `FONDO DE INVERSIÓN LARRAINVIAL DEUDA LATAM HIGH YIELD`. Se conservan ambos, sin afirmar que sean intercambiables para otros años; la ficha CMF de identificación actual para [FFMM 8490](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=8490&tipoentidad=RGFMU&vig=VI&control=svs&pestania=1) confirma el nombre actual y el RUN. Las cifras de las dos fichas del corte respectivo sí coinciden con las del XML.

Fichas de los períodos: [FFMM 8490, 2014-12](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=8490&tipoentidad=RGFMU&vig=VI&control=svs&pestania=3&mm=12&aa=2014&tipo=I&tipo_norma=IFRS) y [FIRES 7064, 2021-12](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=7064&tipoentidad=FIRES&vig=VI&control=svs&pestania=29&mm=12&aa=2021&tipo=I&tipo_norma=IFRS).

**Conclusión proporcional:** aprobadas **estas dos filas para revisión de método**, no los universos de 1.543 FFMM / 1.677 FI ni las filas del pipeline masivo. Todavía faltan muestra contemporánea de fondos vigentes, varios períodos, comprobación de moneda/escala por archivo y manejo de XML reparados o DV discordante antes de publicar Parquets masivos en `docs/outputs`.
