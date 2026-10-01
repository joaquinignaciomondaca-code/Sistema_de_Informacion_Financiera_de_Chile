# Balance y estado de resultados de fondos mutuos (FFMM): cómo obtenerlos del XML de la CMF

**Fecha:** 2026-10-01
**Estado:** INVESTIGACIÓN terminada, **sin implementar**. Hoy el sitio no publica balance ni resultados de fondos
mutuos (solo carteras mensuales, registro y maestro).
**Pregunta:** ¿se pueden obtener el balance y el estado de resultados de los FFMM por XBRL, XML u otro formato
estructurado, y con qué calidad?

---

## 1. Respuesta corta

| Pregunta | Respuesta |
| :--- | :--- |
| ¿XBRL? | **No existe para fondos.** Las taxonomías XBRL de la CMF (2021–2026) son solo `CL-CI`, `CL-HB`, `CL-HS`, `CL-CC`, `CL-EI` y `CL-BS`. |
| ¿XML? | **Sí.** Cada fondo envía un «XML IFRS» propio de la CMF (archivo `FMEF…`, Circular 1.997 de 2010) con balance, resultados, cambios en el activo neto por serie y flujo de efectivo. |
| ¿Descarga masiva? | **No se encontró.** No hay TXT ni API por período como en AGF o factoring: hay una ficha por fondo y año, y un XML por ficha. No existe una página de novedades de envío IFRS para fondos (la de sociedades anónimas sí). |
| ¿Periodicidad? | **Anual** (cierre de diciembre). La propia ficha lo dice: «a partir de 2011, según circular N° 1997, los estados financieros se reportan anualmente». El primer envío es FY2010 («pro forma»). |
| ¿Se puede desde Actions? | **Sí, medido.** 278 de 278 fichas y 277 de 277 XML respondieron HTTP 200 a un `GET` plano, sin sesión ni token (una de las fichas era una página de desafío JS, ver 5.2). |
| ¿Es fiable? | **Sí, medido.** Las 9 identidades contables cuadran en el 100 % de los 277 archivos legibles y el total de activos coincide con la tabla HTML de la CMF en los 266 casos comparables. |
| ¿Cuánto cuesta? | ≈ 7.900 fondo-años → ≈ 15.800 peticiones → **≈ 70 min** con 4 hilos y ≈ 244 MB descargados (no se versionan). |

**Qué no existe de forma pública:** balance o resultados **trimestrales o mensuales** de FFMM. El archivo
`FONDOS05` (activos, pasivos y patrimonio, diario) de la NCG 532 es un reporte regulatorio a la CMF y no se
encontró evidencia de que se publique. El informe «Estado de Situación Financiera» del portal de
estadísticas de FFMM figura **«(en revisión)» y sin enlace**.

---

## 2. Fuentes

| Fuente | Qué es | Dirección / dato clave |
| :--- | :--- | :--- |
| Ficha del fondo, pestaña «Información Financiera» | Página por fondo y año con el enlace al XML, las tablas HTML y 3 PDF | `institucional/mercados/entidad.php?mercado=V&rut={RUN}&grupo=&tipoentidad=RGFMU&row=&vig=VI&control=svs&pestania=3&mm=12&aa={AAAA}&tipo_norma=IFRS` |
| XML IFRS | El dato estructurado | `institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo=FMEF….xml&&rut={RUN}&&periodo={AAAA}12&&path=/web/ifrs_xml/fmifr/xml/&&desc_archivo=Estados_financieros_` |
| PDF por ficha | Notas (`FMNO`), dictamen (`FMDA`), declaración (`FMDR`) | Mismo script, `path=/web/ifrs_xml/fmifr/notas/`; los 277 archivos de la muestra los tenían |
| Ficha técnica Circular 1.997/2010 | Norma del formato: un XML para los estados, PDF para notas; cifras en **miles de la moneda funcional**, sin decimales | `sitio/seil/software-manual/fmifr/FichaTecnicaFMIFR.pdf` |
| Modelo Excel, generador, XML de ejemplo y XSD | Catálogo oficial de cuentas y esquema de validación | Página «software gratuito» de fondos (`portal/principal/613/w3-article-16370.html`). El modelo es de 2011/2012 y **está desfasado** (ver 5.3) |
| «Publicación EEFF» (`pestania=62`) | Enlaces a los PDF publicados en el sitio de cada administradora | Solo PDF; no aporta datos estructurados |
| Estadísticas de FFMM (`sitio/estadisticas/valores_fondosmutuos.php`) | Patrimonio, rentabilidad, partícipes, carteras, comisiones | Sin balance ni resultados. El «Estado de Situación Financiera» está «en revisión», sin enlace |
| NCG 532 y NCG 554 (MSI de Fondos) | 7 archivos regulatorios de las administradoras; `FONDOS05` = activos, pasivos y patrimonio, **diario** | Vigencia diferida al 2026-06-01. Se envía a la CMF; sin evidencia de publicación abierta |
| Fondos de inversión | Mismo patrón con otro archivo (`FIEF`, ruta `fiifr`), **trimestral** (Circular 1.998) | Fuera de este alcance; no se midió |

Hechos del enlace: el nombre del XML (`FMEF2026811894_20260330_110924_8011.xml`) lleva un correlativo, la
**fecha y hora de envío** (2026-03-30 11:09:24) y el RUN, así que no se puede adivinar: hay que leerlo de la
ficha. La CMF autoriza reenvíos por correo, y la ficha siempre muestra el último archivo. Un período sin envío
responde con el texto fijo *«No existe información de la entidad para el periodo señalado.»*. La ficha
funciona con `vig=VI` **también para fondos ya extintos**.

---

## 3. Estructura del XML

Raíz `<IFRS>` con `Identificacion`, `DatosPeriodo`, `Contextos` y una lista plana de
`<Cuenta CodigoCuenta="…" Context="PeriodoActual|PeriodoAnterior" Nota="…" Serie="…">valor</Cuenta>`.

* Cada archivo trae **dos ejercicios** (`PeriodoActual` y `PeriodoAnterior`). `Nota` solo va en el actual.
* `Serie` aparece en el estado de cambios del activo neto; el balance y los resultados no llevan serie.
* `DatosPeriodo` declara moneda, mes y año, auditor, `NumUltimaNotaInformada` y cinco banderas (qué estados
  vienen: situación financiera, resultados, cambios en el activo neto, flujo directo, flujo indirecto).
* Todos los importes son enteros en **miles de la moneda funcional**. Los gastos van con signo negativo.

**Balance (16 cuentas)**: `EfectivoYEfectivoEquivalente`, `ActivosFinancierosAValorRazonableConEfectoEnResultados`,
`ActivosFinancierosAValorRazonableConEfectoEnResultadosEntregadosEnGarantia`, `ActivosFinancierosACostoAmortizado`,
`CuentasPorCobrarAIntermediarios`, `OtrasCuentasPorCobrar`, `OtrosActivos`, **`TotalActivo`**,
`PasivosFinancierosAValorRazonableConEfectoEnResultados`, `CuentasPorAPagarIntermediarios`, `RescatesPorPagar`,
`RemuneracionesSociedadAdministradora`, `OtrosDocumentosYCuentasPorPagar`, `OtrosPasivos`, **`TotalPasivo`**,
**`ActivoNetoAtribuibleALosParticipes`**.

**Estado de resultados (19 cuentas)**: `InteresesYReajustes`, `IngresosPorDividendos`,
`DiferenciasDeCambioNetasSobreActivosFinancierosACostoAmortizado`, `DiferenciasDeCambioNetasSobreEfectivoYEfectivoEquivalente`,
`CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados`,
`ResultadoEnVentaDeInstrumentosFinancieros`, **`OtrosEri`**, **`TotalIngresosPerdidasNetosDeLaOperacion`**,
`ComisionDeAdministracion`, `HonorariosPorCustodiaYAdministracion`, `CostosDeTransaccion`, `OtrosGastosDeOperacion`,
**`TotalGastosDeOperacion`**, `UtilidadPerdidaDeLaOperacionAntesDeImpuesto`, `ImpuestosALasGananciasPorInversionesEnElExterior`,
`UtilidadPerdidaDeLaOperacionDespuesDeImpuesto`, `AumentoDisminucionDeActivoNeto…AntesDeDistribucionDeBeneficios`,
`DistribucionDeBeneficios`, `AumentoDisminucionDeActivoNeto…DespuesDeDistribucionDeBeneficios`.

Identidades usadas como control (tolerancia ±2 mil, porque cada cuenta se redondea al informarla):
`TotalActivo = Σ activos`; `TotalPasivo = Σ pasivos`; **`TotalActivo − TotalPasivo = ActivoNetoAtribuible`**;
`Σ ingresos = TotalIngresos`; `Σ gastos = TotalGastos`; `TotalIngresos + TotalGastos = Utilidad antes de impuesto`;
`Utilidad antes + Impuestos = Utilidad después`; `Utilidad después = Aumento antes de distribución`;
`Aumento antes + Distribución = Aumento después`.

Ojo: en un fondo mutuo el «patrimonio» es el **activo neto atribuible a los partícipes**, que la norma presenta
fuera del pasivo. Por eso la cuadratura es `activo − pasivo = activo neto`.

---

## 4. Medición real desde Actions

Sonda de solo lectura, ejecutada el 2026-10-01 en el runner con 4 hilos y 0,1 s de pausa por petición.
**Muestra fija de 278 fondo-años:** 16 fondos con todos sus cierres de diciembre 2010–2025 (14 al azar con
semilla `20261001`, 7 vigentes y 7 extintos, más los controles 8011 y 8001) y 90 fondos vigentes al azar en 2025.
Corridas `36818229127` y `36818566836`; el script quedó en el commit `6803207` del PR #20 y se retiró de la
rama en `9413961` (el README pide investigar en una rama y no dejar workflows sin publicación en `main`).

| Medida | Resultado |
| :--- | :--- |
| Peticiones | 555 en 145 s (3,8 por segundo) |
| Fichas con HTTP 200 | 278 / 278 |
| Fichas con XML → XML leído | 277 / 278 (la restante, una página de desafío JS: ver 5.2) |
| Cobertura por año (2010–2025) | todos los candidatos tenían XML; ninguna respuesta «No existe información» |
| Tiempos | ficha p50 1,38 s, p95 1,73 s · XML p50 0,62 s, p95 0,80 s |
| Tamaño del XML | mín 11,3 kB · mediana 29,6 kB · máx 61,2 kB (8,55 MB las 277) |
| Series por fondo | mín 1 · mediana 6 · máx 20 |
| PDF de notas, dictamen y declaración | 277 / 277 |
| Valores no numéricos / no enteros | 0 / 0 |
| Mes distinto de 12 · año o RUN distinto del pedido · activo total 0 | 0 · 0 · 0 |
| **Cuentas de balance y resultados (16 + 19 = 35 códigos)** | **presentes en 277 / 277 archivos**, sin una ausente |
| **9 identidades contables, ejercicio actual** | **277 / 277 cada una, 0 fallas** |
| 9 identidades, ejercicio anterior | 266 / 266, 0 fallas (11 archivos no traen anterior) |
| Total activo XML = tabla HTML de la CMF | 266 / 266 (actual) y 266 / 266 (anterior); 11 no comparables por formato |
| Controles leídos a mano (8011 FY2025, 8001 FY2012) | 8 / 8 valores iguales |
| Moneda | `$$` = pesos: 229 · `PROM` = **dólares** (la ficha dice «miles de Dolar»): 48 |
| Flujo de efectivo | directo 268 · indirecto 9 |
| Ejercicio anterior de N frente a actual de N−1 | 674 iguales · **6 difieren (0,9 %)** |

Limitaciones: la muestra no es un censo (los candidatos salen de fondos activos hasta diciembre según el
maestro de carteras), no mide fondos de inversión y no prueba el comportamiento de la CMF bajo una carga
sostenida de ~16.000 peticiones.

---

## 5. Trampas que un extractor debe manejar

### 5.1 La declaración de codificación no es fiable
Declaran UTF-8: 124 archivos · ISO-8859-1: 97 · ninguna: 55 · **inventada: 1** (`encoding="iso-8011-K"`, el RUN del
fondo pegado en la declaración; Expat lanza `LookupError`, no `ParseError`). Tres familias de generadores:
sin comentario (163), «CTI Service» (50, todos declaran UTF-8) y «DBNeT GX» (≈ 64, varias versiones).
**27 de 277 archivos (9,7 %) no se leen con la declaración**: el cuerpo es latin-1 aunque diga UTF-8 o nada.
Regla: descartar la declaración y decodificar por contenido (UTF-8 estricto; si falla, latin-1).

### 5.2 Respuestas transitorias de la CMF
En ≈ 1.100 peticiones (dos corridas completas) aparecieron dos respuestas anómalas: **una página de desafío
JavaScript** (JS ofuscado, sin la tabla ni el enlace) en lugar de la ficha, y **una respuesta de 2,7 kB del
endpoint XML** (la mediana es 29,6 kB) que no era XML bien formado (`invalid token`); por el error y el tamaño, casi
seguro otra página intermedia y no un archivo truncado. Las dos fueron transitorias: esas mismas fichas se leyeron
bien en la otra corrida. Hay que validar el contenido (marcador de la ficha, XML completo que cierra `</IFRS>`),
reintentar con espera y **no tratar nunca un desafío como «sin información»**: sería un falso hueco silencioso.

### 5.3 El catálogo oficial de cuentas está desfasado
El modelo Excel de 2011 llama `Otros` a la línea «Otros» del estado de resultados; en los archivos reales es
**`OtrosEri`**. Además hay códigos con **espacio final** (`SaldoFinalDeEfectivoYEfectivoEquivalente `, 8 archivos),
códigos vacíos (3 elementos) y, en los 9 archivos con flujo indirecto, nombres distintos en el flujo y en el estado
de cambios (`RescateDeCuotasEnCirculacion` frente a `RescatesDeCuotasEnCirculacion`). Para balance y resultados los 35
códigos son idénticos en todos los generadores y años; para los demás estados hay variantes. Conviene limpiar con
`strip()` y no depender del modelo.

### 5.4 Moneda
`PROM` es dólares: 48 archivos (uno o dos de los 16 fondos con historia completa, año a año, y **21 de 98 fondos
en 2025**, ≈ 21 %).
Nunca sumar pesos con dólares sin una columna de moneda.

### 5.5 Reexpresiones
6 de 680 comparaciones entre el ejercicio anterior de un archivo y el actual del año previo difieren: cuatro son
redondeos de ±1 a ±20 mil y **dos son materiales, ambas del fondo 8305** (la utilidad antes de impuesto de FY2022 pasó
de 9.056.729 a 1.671.624 miles, y la de FY2013 de −3.483.746 a −3.203.636). El valor primario debe ser el `PeriodoActual` de cada año, y la comparación con el
anterior del año siguiente sirve para detectar reediciones **sin pedir nada más** a la CMF.

### 5.6 Primer envío
Los 11 archivos sin ejercicio anterior son coherentes con la ficha técnica: el primer envío (FY2010, «pro forma»:
NCh e IFRS a la vez) informa un saldo inicial al 01/01/2010 en lugar de ejercicio anterior. Antes de 2010 solo existe
FECU en norma chilena, sin este XML.

---

## 6. Esqueleto de lectura

Probado en local con XML **sintéticos** construidos con los valores reales del fondo 8011 (FY2025): latin-1
declarado, UTF-8 declarado con cuerpo latin-1, UTF-8 real sin declaración, declaración inventada, código con
espacio final y archivo truncado (falla con `ParseError`). La sonda midió los 277 archivos reales con una lógica
equivalente para los importes (respetaba la declaración y, si fallaba, releía en latin-1); este esqueleto es la
versión recomendada y aún no se ha corrido sobre los archivos reales.

```python
import re
import xml.etree.ElementTree as ET

def leer_xml(raw: bytes) -> ET.Element:
    """Descarta la declaración (UTF-8 falso, ausente o inventada) y decodifica por contenido."""
    cuerpo = re.sub(rb"^\s*<\?xml[^>]*\?>", b"", raw)
    try:
        txt = cuerpo.decode("utf-8")
    except UnicodeDecodeError:
        txt = cuerpo.decode("latin-1")
    return ET.fromstring(txt)          # un XML truncado falla de forma ruidosa (ParseError)

def cuentas(raiz: ET.Element, contexto: str = "PeriodoActual") -> dict[str, int]:
    out = {}
    for c in raiz.iterfind("Cuenta"):
        if c.get("Serie") or c.get("Context") != contexto:
            continue
        out[(c.get("CodigoCuenta") or "").strip()] = int(c.text)   # strip: hay códigos con espacio final
    return out

def cuadra_esf(c: dict[str, int], tol: int = 2) -> bool:
    return abs(c["TotalActivo"] - c["TotalPasivo"] - c["ActivoNetoAtribuibleALosParticipes"]) <= tol
```

---

## 7. Diseño propuesto (mismo patrón que FL y corredoras)

1. **Módulo** `ffmm/scripts/actualizar_eeff.py` con pruebas en `ffmm/tests/`, usando como fixtures reales unos
   pocos XML pequeños y públicos: uno latin-1, uno con UTF-8 falso, uno en dólares y uno con la declaración inventada.
2. **Candidatos**: cierres de diciembre 2010–2025 dentro del rango activo de cada fondo en
   `maestro_fondos_mutuos` (≈ **7.898** fondo-años; 455 a 561 por año) más los fondos nuevos del registro. Incluir
   los extintos: son 1.094 de 1.543 y cubren el histórico.
3. **Flujo**: ficha → regex del enlace `archivo=(FMEF…\.xml)` → XML → validar (bien formado, completo) → extraer
   las 35 cuentas del ejercicio actual → comprobar las identidades → guardar partición por fondo-año con `sha256`,
   nombre de archivo y fecha de envío (sale del nombre).
4. **Tablas largas** (convención de `docs/NAMING.md`): balance y resultados anuales, con `periodo` (`AAAA-12`),
   `run_fondo`, `nombre_fondo`, `rut_agf`, `moneda` (CLP/USD) y `moneda_cmf` (`$$`/`PROM`), `orden` oficial,
   `codigo_cuenta`, `cuenta`, `valor` (miles de la moneda funcional), `nota`, `fuente_archivo`, `sha256_archivo`.
   ≈ 276 mil filas si solo se publica el ejercicio actual.
5. **Compuerta** como la de FL: no publicar si falla la cuadratura, si falta alguna de las 35 cuentas, si la
   cobertura por año (fondos con XML sobre candidatos) baja de un umbral, o si hay una moneda desconocida. Un
   desafío JS o un XML truncado cuentan como reintento, no como ausencia.
6. **Ejecución**: lotes reanudables con `actions/cache` (como FL), 3 a 4 hilos con jitter y reintento con espera.
   El respaldo inicial son ≈ 70 min repartidos en 2 o 3 corridas. Luego, un workflow **anual** (abril–junio; los
   envíos de FY2025 se hicieron a fines de marzo) y reedición vigilada comparando el `PeriodoAnterior` del año
   siguiente contra lo ya guardado, sin barrer las 7.900 fichas.
7. **Fase 2**: estado de cambios del activo neto por serie y flujo de efectivo (los 9 archivos con flujo indirecto
   usan otros códigos), y ejercicio anterior para registrar reexpresiones. **Fase 3**: fondos de inversión
   (`FIEF`, trimestral).

**Esfuerzo orientativo (fase 1):** 2 a 3 días de extractor, pruebas, workflow y documentación, más ½ a 1 día para
el catálogo y la web. **Riesgos:** (a) la CMF sirve desafíos JS, y no se probó el comportamiento bajo ~16.000
peticiones sostenidas; (b) el XSD oficial no se pudo bajar en esta sesión (el lector respondió HTTP 500 y `curl`
está bloqueado desde el entorno de desarrollo), así que las reglas salen de 277 archivos reales y conviene
validar contra el XSD cuando se implemente; (c) decisión de producto pendiente sobre las reexpresiones (valor
original o último) y sobre mostrar dólares sin convertir.

---

## 8. Qué no se pudo confirmar

* El contenido exacto del XSD `FMIFR_esquema.xsd`.
* Que `FONDOS05` o algún informe mensual de balance se publique en abierto.
* El comportamiento de la CMF bajo una carga sostenida.
* Fondos de inversión (misma familia, otro formato y trimestral): no se midió.
* La fila «Fondos mutuos … hoy se lee HTML/PDF» de `fuentes_xml_por_industria.md` es histórica: **hoy no se lee
  nada**, y su prioridad n.º 1 queda cubierta por esta nota.
