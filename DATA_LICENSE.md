# Licencia de los datos

Este repositorio mezcla dos cosas que **no** comparten licencia: el código que
los produce y los datos que publica. La licencia MIT del repositorio cubre el
código, los scripts y la documentación; **no** cubre los datos de terceros que
se redistribuyen aquí.

## Código

MIT. Ver [`LICENSE`](../LICENSE).

## Datos

Los datos son de organismos públicos chilenos que los publican para su consulta.
Este proyecto los descarga, los normaliza y los republica en Parquet **sin
alterar sus valores**, citando la fuente en cada recurso. La verificación del
permiso de redistribución de cada fuente está **pendiente** y se declara como
tal en el descriptor: ningún recurso de `docs/api/v1/datapackage.json` afirma
una licencia que no se haya comprobado.

| Fuente | Qué publica aquí | URL | Condiciones | Estado |
|---|---|---|---|---|
| **CMF** — Comisión para el Mercado Financiero | Bancos (B1/B2/R1), seguros (Circular 1835), fondos mutuos y de inversión, AGF, corredoras, securitizadoras, CCAF, factoring y leasing, patrimonios separados, cooperativas, fintech, sistemas de pago | https://www.cmfchile.cl | Datos abiertos de un regulador; se citan la norma y la fuente en cada recurso. Falta confirmar por escrito el permiso de redistribución íntegra. | `pendiente` |
| **BCCh** — Banco Central de Chile | Series macro: dólar, cobre, tasas, curvas de bonos, deuda pública, expectativas de inflación | https://si3.bcentral.cl | API REST SIETE de acceso público; sus términos de uso no se han revisado en detalle. | `pendiente` |
| **SPensiones** — Superintendencia de Pensiones | Lista de administradoras y valor cuota de los fondos | https://www.spensiones.cl | Datos públicos del regulador; permiso de republicación sin verificar. | `pendiente` |
| **SUSESO** — Superintendencia de Seguridad Social | Cajas de compensación (vía los estados financieros que recibe la CMF) | https://www.suseso.cl | Ídem anterior. | `pendiente` |

### Qué significa `pendiente`

Que este proyecto **no** puede afirmar todavía que tenga derecho a redistribuir
el dato, aunque lo haga amparado en que la fuente lo publica abiertamente y en
que se cita el origen. Quien lo use para algo distinto de consulta o
investigación debe verificar la licencia en la fuente original.

Mientras el estado sea `pendiente`:

- el descriptor por recurso declara `licenses: [{ "name": "Uso condicionado por la fuente", "path": "../DATA_LICENSE.md" }]`;
- **no** se aplica la MIT a los datos;
- el campo `sif.licencia_estado` de cada recurso dice `pendiente`.

Si una fuente confirma el permiso, se cambia su fila a `verificada` con la
referencia del documento, y el descriptor lo refleja al regenerarse.

## Datos derivados

Las proyecciones y tablas `_relevantes` que genera este repositorio (por ejemplo
`seguros_renta_fija_relevante`) son obra derivada de las anteriores: heredan su
condición y no añaden ninguna licencia nueva.
