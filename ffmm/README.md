# Fondos mutuos (CMF)

Dos flujos independientes, los dos automáticos y los dos en `docs/outputs/ffmm/`:

| Flujo | Qué publica | Script · workflow | Cuándo |
|---|---|---|---|
| Carteras (Circular 1333) | cartera nacional y extranjera, futuros y forwards, opciones, lista de fondos | `scripts/actualizar_carteras.py` · `ffmm_carteras.yml` | días 8, 18 y 28 |
| **Estados financieros anuales** (Circular 1997) | **balance** y **estado de resultados** de cada fondo, línea por línea | `scripts/actualizar_eeff.py` (+ `scripts/eeff_xml.py`) · `ffmm_eeff.yml` | días 4, 14 y 24 |

## Estados financieros anuales

**Fuente.** Cada fondo envía a la CMF un XML IFRS (`FMEF…`) por cierre de diciembre, que la ficha del fondo
(`entidad.php … pestania=3&mm=12&aa=AAAA`) enlaza. No hay XBRL para fondos ni descarga masiva: una ficha y un XML por
fondo y año. Los importes vienen en **miles de la moneda del fondo** (pesos, dólares o euros) y cada archivo trae el ejercicio
y el anterior.

**Qué procesa.** Todos los fondos, vigentes y extintos, y todos los cierres desde 2010 (primer envío IFRS). Los
candidatos salen del maestro de carteras (los diciembres dentro de la vida activa de cada fondo) y, para los fondos del
registro que nunca reportaron cartera, de todos los años.

**Tablas** (formato largo, un Parquet por año, 19 columnas cada una):

| Tabla | Líneas por fondo y cierre | Contenido |
|---|---:|---|
| `ffmm_balance` | 16 | efectivo, activos financieros, cuentas por cobrar, total activo, pasivos, total pasivo, **activo neto atribuible a los partícipes** |
| `ffmm_resultados` | 19 | ingresos y pérdidas de la operación, gastos, utilidad antes y después de impuesto, aumento del activo neto |

Columnas: `periodo`, `run_fondo`, `run_fondo_dv`, `nombre_fondo`, `rut_agf`, `razon_social_agf`, `moneda`, `moneda_cmf`,
`seccion`, `tipo_linea`, `orden`, `codigo_cuenta`, `cuenta`, `nota`, `valor_miles_mf`, `valor_anterior_miles_mf`,
`fuente_archivo`, `enviado_cmf`, `sha256_archivo`. `orden` es el número de línea del estado como lo presenta la CMF y
es fijo por cuenta (la 8 del balance es siempre el total activo); el XML trae las cuentas en orden alfabético, así que
sale de un catálogo (`eeff_xml.CATALOGO`). `tipo_linea` distingue los `detalle` de los `total`: no se suman juntos.
`moneda` es `CLP`, `USD` o `EUR` (`$$`, `PROM` y `EUR` en la CMF): no se suman monedas distintas.

**Estado de cada fondo y cierre** (`docs/outputs/ffmm/ffmm_eeff_control.json` lleva los huecos y las reediciones):

| Estado | Significado |
|---|---|
| `ok` | XML leído con las 35 cuentas del ejercicio: se publica |
| `sin_informacion` | la ficha dice «No existe información de la entidad para el periodo señalado» |
| `ilegible` | XML inutilizable (otro fondo o cierre, moneda desconocida, cuentas faltantes, mal formado) o que tras 3 corridas no llegó completo: se excluye y queda listado |
| `pendiente` | sin resolver todavía: no se intentó o la CMF no respondió |

Un desafío de la CMF, un corte o un XML a medias **nunca** se toman por «sin información»: la serie no se publica con
huecos silenciosos.

**Incremental.** Los cierres cerrados (más de 150 días) no se vuelven a pedir, salvo una vuelta de refresco: cada
corrida revisa la ficha de los dos últimos cierres y de 1/36 del resto (toda la historia una vez al año). Si cambió
el nombre del XML, la CMF autorizó un reenvío: se baja de nuevo y queda en `reediciones`. Un cierre abierto se publica
con lo que haya y se relee en cada corrida. El progreso vive en `.local-data/ffmm_eeff` (caché de Actions) y, ya
publicado, en los Parquet y en el control: si la caché se pierde, se reconstruye desde lo publicado.

**Compuertas.** La serie se publica solo si todos los cierres cerrados están resueltos; se detiene, sin publicar nada,
si descuadran en bloque (≥ 3 y más del 5 %, `pipelines/auto/cuadratura.py`), si casi ningún balance trae los tres
totales o si más del 2 % de los XML son ilegibles. Un fondo aislado que no cuadra se publica con su aviso en el control.
`scripts/auditar_eeff_ifrs.py` repasa en cada push y PR toda la historia publicada.

**Probar.** Sin red, con XML sintéticos con los importes reales de un fondo:

```
python -m unittest -v ffmm.tests.test_eeff_xml ffmm.tests.test_actualizar_eeff pipelines.auto.tests.test_cuadratura
```

**Correr** (necesita llegar a `cmfchile.cl`; desde algunos entornos de desarrollo la conexión TLS se corta y solo
funciona en Actions):

```
python ffmm/scripts/actualizar_eeff.py --desde 2024 --limite 50      # prueba acotada
python ffmm/scripts/actualizar_eeff.py                               # lo que corre el workflow
```

**Rarezas del XML real** (medidas en 278 fondo-años; detalle en `docs/notas/ffmm_estados_financieros_xml_2026-10-01.md`):
la declaración de codificación no es fiable (UTF-8 falso, ausente o inventada: `iso-8011-K`); la línea «Otros» de
resultados es `OtrosEri` y no `Otros` como dice el modelo oficial de 2011; hay códigos con espacio final y la CMF
sirve a veces una página de desafío JavaScript en lugar de la ficha.
