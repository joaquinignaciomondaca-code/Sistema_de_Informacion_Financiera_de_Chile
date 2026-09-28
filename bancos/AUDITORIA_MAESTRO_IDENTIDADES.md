# Revisión parcial de identidades del maestro bancario

**Fecha:** 2026-09-27

**Alcance:** revisión rápida de consistencia y cotejo oficial de cuatro RUT; no equivale a validar el maestro completo.

## Resultado

- 40 filas y 40 códigos institucionales distintos.
- Los 40 RUT pasan el dígito verificador; esto solo comprueba formato, no identidad.
- Se detectaron cuatro RUT incorrectos al contrastar código/nombre con antecedentes CMF y se corrigieron tanto en `bancos/scripts/pipeline_stream_bancos.py` como en `docs/outputs/bancos/bancos_maestro.json`:

| Código | Identidad | RUT corregido |
| --- | --- | --- |
| 009 | Banco Internacional | 97.011.000-3 |
| 012 | Banco del Estado de Chile | 97.030.000-7 |
| 504 | Banco Bilbao Vizcaya Argentaria, Chile (BBVA) | 97.032.000-8 |
| 507 | Banco del Desarrollo | 97.051.000-1 |

Fuentes oficiales consultadas:

- CMF, Banco Internacional: <https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97011000&grupo=0&tipoentidad=BANCO&vig=VI&control=svs&pestania=38>
- CMF, Banco del Estado de Chile: <https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97030000&grupo=0&tipoentidad=BANCO&row=AAAwy2ACTAAABzgAAl&vig=VI&control=svs&pestania=110>
- CMF, BBVA Chile: <https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=97032000&grupo=0&tipoentidad=BANCO&vig=VI&control=svs&pestania=38>
- CMF, antecedentes que identifican el RUT 97.051.000-1 con Banco del Desarrollo: <https://www.cmfchile.cl/portal/principal/623/articles-103770_recurso_1.pdf>

## Pendiente

Esta revisión no cotejó los RUT, razón social, tipo, estado ni vigencia de las otras 36 filas de forma individual, ni revisó exhaustivamente los datos históricos y agregados. Por eso el maestro debe seguir marcado **pendiente de validación** hasta completar el cotejo de los 40 registros contra las nóminas y cronologías oficiales CMF.
