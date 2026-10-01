# Revisión de la extracción de balance y estado de resultados por industria

Fecha: 2026-10-01 · Alcance: la lógica que convierte las fuentes de la CMF en las tablas
`<sector>_balance` y `<sector>_resultados`, con foco en `pipelines/ifrs_sectores/actualizar.py`
(AGF, securitizadoras, CCAF), `factoring_leasing/scripts/backfill_ifrs.py` y
`corredoras_bolsa/scripts/actualizar_eeff.py`.

Método: lectura del código + reejecución de las validaciones **sobre los Parquet ya
publicados** (no sobre lo que el extractor dice que hizo). Todo número de este informe sale de
`docs/outputs/**` tal como está en el repositorio. No se pudo descargar la CMF desde este entorno
(TLS cerrado; ya documentado en `docs/notas/fuentes_xml_por_industria.md`).

---

## 1. Resumen ejecutivo

* Hay **cinco mecanismos distintos** para extraer balance y resultados, y **dos de ellos leen el
  mismo archivo** con convenciones incompatibles entre sí.
* La fuente compartida trae **368 sociedades por trimestre** (583 en los cierres de diciembre) y se
  publican **66**: el **82 % del archivo se descarta**.
* La compuerta contable «activos = pasivos + patrimonio» **protege solo el futuro**: de los 69
  trimestres publicados, únicamente el último (202606) registra `balances_verificados`. La historia
  completa la verifiqué a mano en esta revisión: **3.793 de 3.805 balances cuadran, 0 descuadres**
  (12 no son verificables). En factoring/leasing, **947 de 949, 0 descuadres**.
* **El estado de resultados no se valida en absoluto** en ninguna industria. Dos identidades
  gratis se cumplen en el 100 % de la historia publicada y hoy nadie las comprueba.
* La compuerta depende de una **lista blanca de glosas** y de que haya ≥ 20 balances verificables.
  Si la CMF renombra un total (ya pasa: «Activos, Total» en vez de «Total de activos»), la
  compuerta **se apaga en silencio** y el trimestre se publica sin control.
* `pipelines/ifrs_sectores/actualizar.py` (615 líneas, el extractor más usado) **no tiene pruebas
  unitarias**.

---

## 2. Mapa: cómo se extrae balance y resultados en cada industria

| # | Industria | Extractor | Fuente | Unidad | Cuadratura al publicar |
| :-- | :--- | :--- | :--- | :--- | :--- |
| 1 | AGF, securitizadoras, CCAF | `pipelines/ifrs_sectores/actualizar.py` | TXT IFRS `estadisticas_ifrs.php` (una descarga, todos los sectores) | pesos (`valor`) | **sí** (glosas literales, tolerancia 1.000) |
| 2 | Factoring y leasing | `factoring_leasing/scripts/backfill_ifrs.py` → `publish_backfill.py` | **el mismo TXT IFRS** | pesos (`valor_archivo`) | **no** (solo la muestra de 2 filas) |
| 3 | Corredoras y agentes de valores | `corredoras_bolsa/scripts/actualizar_eeff.py` | Excel FECU `intermediarios_ifrs1.php?xls=y` | **miles de pesos** (`valor_miles_clp`) | **sí** (códigos FECU 10/21/22) |
| 4 | Banca | `bancos/scripts/extract_cmf_bank_lines.py` | B1/B2/R1 (ancho fijo) | según informe | coteja total de activos vs Excel CMF |
| 5 | Patrimonios separados | `securitizadoras/scripts/05_publicar_balance_patrimonios.py` | PDF (curación híbrida) | miles de pesos | auditoría posterior |

Filas publicadas (balance + resultados): AGF **129.639**, securitizadoras **25.969**,
CCAF **13.549**, factoring/leasing **52.414**, corredoras **185.921**.

### 2.1 La fuente compartida (mecanismos 1 y 2)

```
periodo;rut;nombre;I|C;moneda;cuenta;valor;taxonomia;estado
```
Códigos de `estado` según la propia CMF: `ESF C/NC`, `ESF OL` (balance), `ERFG` (resultado por
función), `ERNG` (por naturaleza), `ERI` (resultado integral), `EFMD`/`EFMI` (flujo de efectivo,
**no se publica**). El reparto es por prefijo: `ESF*` → balance, `ER*` → resultados.

Detalle que importa: la CMF describe el archivo como *«las principales cuentas»* del estado de
situación y del resultado. Es decir, **no es el estado completo**, sino un subconjunto — la
publicación es fiel a la fuente, pero conviene que el diccionario lo diga.

---

## 3. Hallazgos

Ordenados por severidad. Cada uno indica dónde está el código y qué evidencia lo sostiene.

### F1 · Dos extractores sobre el mismo archivo, con convenciones distintas

`pipelines/ifrs_sectores/actualizar.py` y `factoring_leasing/scripts/backfill_ifrs.py` descargan
el **mismo** TXT y lo publican con criterios diferentes:

| | `ifrs_sectores` | `backfill_ifrs` |
| :--- | :--- | :--- |
| Selección de entidades | RUT en la lista **o** nombre que calza (regex) | solo los 32 RUT del catálogo |
| `tipo_balance` | `individual` / `consolidado` | `I` / `C` (literal de la CMF) |
| Orden de las cuentas | columna `orden` | **no existe** (`repeticion_contexto` en su lugar) |
| Métrica | `valor` + `valor_no_numerico` | `valor_archivo` + `valor_texto_original` + `valor_es_entero` |
| Cuadratura | sí | no |
| Recorte de historia | incremental por trimestre | barrido completo del índice |

Consecuencia: dos tablas del mismo origen no se pueden consultar con la misma sentencia
(`WHERE tipo_balance = 'individual'` funciona en AGF y devuelve cero filas en factoring), y el
estado de resultados de factoring no se puede ordenar como lo publica la CMF.

### F2 · Se publica el 18 % de la fuente

| Trimestre | Sociedades en el archivo | Publicadas (AGF+SEC+CCAF) | Descartadas |
| :--- | ---: | ---: | ---: |
| 2026-06 | 368 | 66 | 302 (82 %) |
| 2024-09 | 380 | 70 | 310 |
| 2015-12 | 580 | 57 | 523 |

El salto a ~580 sociedades en los cierres de diciembre son emisores que informan solo una vez al
año. Esas 300 sociedades por trimestre —emisores de valores, holdings, y posiblemente bancos
(`TAX HB`) y seguros (`TAX HS`)— viajan en el archivo que ya se descarga y hoy se tiran. El diseño
(sector = RUT en lista **o** patrón de nombre) hace que ampliar industrias sea principalmente
añadir listas y patrones… pero antes hay que resolver F3.

### F3 · La compuerta de cuadratura se puede apagar en silencio

`pipelines/auto/cuadratura.py` reconoce los totales por **lista blanca de glosas**:

```python
ACTIVOS    = {"total de activos", "total activos", "activos totales"}
PASIVOS    = {"total de pasivos", "total pasivos", "pasivos totales"}
PATRIMONIO = {"patrimonio total", "total patrimonio", "total de patrimonio"}
```

y solo detiene la publicación si:

```python
verificados >= 20 and len(malos) >= 3 and len(malos) > 0.05 * verificados
```

Dos consecuencias:

1. **Si la CMF renombra un total, `verificados` cae a ~0 y la compuerta deja de existir**: con
   menos de 20 balances verificables, `debe_detener` devuelve `False` y el trimestre se publica
   **sin ningún control**. No es hipótesis: en el archivo **ya** conviven dos convenciones. La
   securitizadora 96.847.360 (2009-12) informa `Activos, Total`, `Pasivos, Corrientes, Total`,
   `Pasivos, No Corrientes, Total` en lugar de `Total de activos` / `Total de pasivos`.
2. **Hoy hay 12 balances que nunca se verificaron** (10 AGF, 2 SEC), por eso mismo: informan
   `Total de activos` y `Patrimonio total` pero **no** `Total de pasivos` (traen
   `Total de patrimonio y pasivos`), o usan la nomenclatura antigua. Quedan publicados sin aviso:
   el manifiesto no distingue «verificado y cuadra» de «no se pudo verificar».

Cualquier ampliación a otra industria hereda este riesgo con glosas desconocidas.

### F4 · El estado de resultados no se valida

No hay ninguna comprobación sobre `ERFG`/`ERNG`/`ERI` en ningún extractor: ni que exista la línea
de resultado, ni que las subtotales cuadren. Sin embargo, dos identidades se cumplen en el 100 %
de la historia publicada y son casi gratis:

| Identidad | AGF | SEC | CCAF | Resultado |
| :--- | ---: | ---: | ---: | ---: |
| `ERI.Ganancia (pérdida)` = `ERFG/ERNG.Ganancia (pérdida)` | 2.934 | 644 | 222 | **3.800 / 3.800 coinciden** |
| `Ganancia bruta` = `Ingresos ordinarios` − `Costo de ventas` | 1.173 | 320 | n/d | **1.493 / 1.493 cuadran** |

La primera, además, certifica que la primera línea del `ERI` es un **duplicado** de la ganancia
del ejercicio (ver F7).

### F5 · La historia publicada nunca pasó por la compuerta

`docs/outputs/ifrs_sectores/manifest.json` solo registra `balances_verificados` en **1 de los 69
trimestres** (202606). Razón estructural: los trimestres cerrados no se releen (mismo SHA-256 ⇒
`continue`), así que la cuadratura **solo protege lo que se lea de ahora en adelante**.

Verificación hecha en esta revisión sobre los Parquet publicados, trimestre a trimestre:

| Sector | Balances | Verificables | No verificables | Descuadrados |
| :--- | ---: | ---: | ---: | ---: |
| AGF | 2.935 | 2.925 | 10 | **0** |
| Securitizadoras | 646 | 644 | 2 | **0** |
| CCAF | 224 | 224 | 0 | **0** |
| **Total** | **3.805** | **3.793** | **12** | **0** |

Empalma con lo que dice el docstring de `cuadratura.py` (3.793). La serie es sana; lo que falta es
que **un script lo compruebe** en vez de un humano con un notebook.

### F6 · El README promete una auditoría de factoring/leasing que no existe

> «Factoring y leasing y patrimonios separados se verifican en auditoría, después de publicar
> (hoy cuadran todos, con diferencias de hasta 1 mil pesos por redondeo)».

`factoring_leasing/scripts/audit_factoring_leasing.py` audita **la lista de entidades** (RUT, DV,
JSON vs Parquet) y su docstring lo dice: *«este auditor no coteja ni certifica esa serie»*. El
cuadre sí se ejecuta, pero solo sobre la **muestra de dos filas** (`publish_structured_sample.py`).

Verificado aquí sobre la serie publicada: **949 balances, 947 verificables, 0 descuadrados**.
El claim es cierto; no está respaldado por código.

### F7 · Duplicidades que hacen que `SUM(valor)` sume de más

En `agf_resultados`, para una misma sociedad, período y tipo de balance:

* `ERI` (resultado integral) **repite** la línea `Ganancia (pérdida)` que ya trae el `ERFG`;
* dentro del propio `ERFG`, `Ganancia (pérdida)` aparece **dos veces** (orden 12 y 14) con el
  mismo monto.

Es decir: `SELECT sum(valor) WHERE cuenta = 'Ganancia (pérdida)'` devuelve el triple de la
utilidad real. **Las consultas sugeridas ya se protegen** con
`estado_financiero IN ('ERFG','ERNG') AND repeticion = 1` (`docs/js/sidebar.js`), pero:

* el **diccionario** describe `repeticion` y `estado_financiero` por separado y nunca advierte que
  hay que filtrar por ambos para no duplicar;
* el **visor de datos** y la pestaña de consultas no heredan esa protección: quien escriba SQL
  nuevo se equivoca en silencio.

Riesgo menor, mismo origen: 3 pares (período, RUT) de securitizadoras informan **individual y
consolidado** en el mismo trimestre, así que un agregado sectorial sin `tipo_balance` los cuenta
dos veces.

### F8 · `escribir()` puede borrar un trimestre en silencio

En `actualizar.py`, la guarda anti-pérdida compara **entidades**, no filas por tabla:

```python
ents = sorted({f["rut"] for t in TABLAS for f in datos[sec][t]})
antes = previo.get(sec, {}).get("entidades", 0)
if len(ents) < antes: ...continue        # protege
for tabla in TABLAS:
    escribir(sec, tabla, periodo, datos[sec][tabla])
```

y `escribir()` reescribe el año **quitando el período** y agregando lo nuevo. Si una relectura
pierde las filas de una sola tabla (p. ej. cambia el esquema y todas las líneas de balance caen en
el `avisos` por `len(c) != 9`, o el prefijo `ESF` cambia), `ents` se mantiene — porque la entidad
sigue apareciendo en resultados — y entonces `escribir(sec, "balance", periodo, [])` **elimina el
balance de ese trimestre** del Parquet publicado, sin aviso. Una guarda por tabla
(`filas[tabla] < previo["filas"][tabla]`) cierra el hueco.

### F9 · Unidades dispares entre industrias

`corredoras_bolsa_balance.valor_miles_clp` está en **miles de pesos**; `agf_balance.valor`,
`ccaf_balance.valor` y `factoring_leasing_*_serie.valor_archivo` están en **pesos**. Cada columna
lo declara en su nombre/diccionario, pero una comparación entre industrias sin leer el
diccionario queda mal por un factor 1.000. No hay una columna `unidad`/`escala` normalizada.

### F10 · Cobertura: nadie avisa de lo que falta

Con corte a 2026-06:

| Sector | En la lista | Con dato publicado | Sin dato |
| :--- | ---: | ---: | ---: |
| AGF | 72 | 53 | **19** |
| Securitizadoras | 16 | 9 | **7** |
| CCAF | 6 | 4 | **2** |

Algunas son bajas reales (CORPBANCA AGF, BANEDWARDS AGF, securitizadoras *en liquidación*), pero
otras no están explicadas en ninguna parte: **SARTOR AGF** deja de informar en 2024-12,
**AZ ANDES (Azimut) AGF** en 2025-09, **CCAF Gabriela Mistral** no aparece nunca. El pipeline no
emite aviso por entidad que desaparece: la guarda actual solo detecta una caída del total del
sector **al releer el mismo trimestre**. Para un trimestre nuevo, no hay contra qué comparar.

### F11 · Sin pruebas unitarias en el extractor más usado

`pipelines/ifrs_sectores/actualizar.py` (615 líneas) y
`corredoras_bolsa/scripts/actualizar_eeff.py` no tienen tests. Sí los tienen
`bancos/` (646 líneas), `factoring_leasing/` (677), `macro/`, `pipelines/normativa_cmf/` y
`pipelines/auto/` (`cuadratura`, `estable`). La lógica crítica —reparto por sector, `orden`,
`repeticion`, guardas anti-pérdida— queda fuera de la red.

### F12 · Detalles menores del parseo

* `orden` se cuenta con la clave `(rut, tipo, moneda, estado)` y **no incluye la taxonomía**: si
  una sociedad informa el mismo estado con dos taxonomías, las cuentas se interleavan. Hoy todas
  las filas publicadas son `TAX CI`, así que no se manifiesta, pero F2 lo vuelve posible.
* El límite de altas (`MAX_ALTAS = 10`) solo aplica a `SOLO_LISTA` (factoring/leasing). Los
  patrones de nombre de AGF, securitizadoras y CCAF **no tienen tope**: un patrón demasiado
  amplio agregaría entidades al publicado sin freno (solo queda el `::notice` y la lista
  `fuera_de_lista` del manifiesto).
* Un trimestre cerrado (> 150 días) **nunca se vuelve a leer**. Es una decisión documentada y
  razonable, pero significa que una corrección tardía de la CMF no se recoge jamás.
* `2010-03` falta en la serie (archivo histórico de la CMF con 4 sociedades). Está bien manejado
  (`ErrorContenido` + aviso), pero conviene que conste en el manifiesto como ausencia conocida.

---

## 4. Lo que está bien y conviene no perder

* **Idempotencia por SHA-256**: si la fuente no cambia, no se reescribe ni se despliega nada
  (`estable.py` evita los commits de solo-marca-de-tiempo).
* **Cierre a 150 días** con relectura de los trimestres abiertos, para recoger presentaciones
  tardías, y **respaldo al archivo anual** cuando el trimestre aislado falla.
* **Fail-closed de verdad** en lo estructural: HTML en vez de TXT, menos de 50 sociedades, o
  `>= 3` descuadres y `> 5 %` ⇒ no se publica. Los descuadres aislados quedan como aviso, no
  tiran el trimestre (acierto: la sociedad que presenta mal su XBRL no debe dejar al sector sin
  dato para siempre).
* **Nada se inventa**: importe no entero ⇒ `valor` nulo y texto original conservado. Medido en
  `agf_resultados`: 6.314 filas no numéricas, de las cuales **6.312 son ganancia por acción**
  (legítimamente con decimales) y solo **2** son montos en pesos con decimales (ERI de 2011-09,
  conservadas como texto). Casi perfecto.
* **RUT canónico** con guardián en CI (`scripts/audit_rut_formatos.py`), escritura atómica
  (`.tmp` + `os.replace`) y partición por año.

---

## 5. Oportunidades, en orden de costo/beneficio

1. **Auditoría ejecutable de cuadratura sobre la historia** (`scripts/auditar_eeff_ifrs.py`):
   recorre los Parquet publicados por trimestre y falla si algo no cuadra o si la fracción de
   balances verificables baja de un umbral. Convierte F5 y F6 en hechos comprobables y le da
   soporte real a lo que el README promete. Costo bajo; cierra el hallazgo más grave.
2. **Cerrar F3**: sustituir la lista blanca de glosas por una detección con respaldo (por código
   de cuenta cuando exista, o por tolerancia a variantes) y **exigir una cobertura mínima de
   cuadratura** («≥ 95 % de los balances del trimestre deben ser verificables») en vez de apoyarse
   solo en `verificados >= 20`. Sin esto, ampliar industrias es publicar a ciegas.
3. **Validar el estado de resultados** con las dos identidades de F4 (ERI = ER en la línea
   ganancia; ganancia bruta = ingresos − costo), con la misma política fail-closed por bloque.
4. **Unificar los dos extractores del TXT** (F1): un solo parseo, una sola convención de columnas
   (`tipo_balance` traducido, `orden` presente, `moneda`/`unidad` explícitas) y cuadratura para
   todos. Prerrequisito para cualquier industria nueva.
5. **Ampliar industrias** (F2): partir por un sondeo en Actions que liste, del archivo vigente,
   los RUT/nombre/taxonomía/estado de las ~300 sociedades descartadas y cuántas son de cada giro
   (el sandbox no alcanza la CMF). Con eso se elige con datos y no con hipótesis.
6. **Cobertura y continuidad** (F10): publicar en el manifiesto la lista de entidades del sector
   sin dato en el trimestre y avisar cuando una entidad que informaba deja de hacerlo.
7. **Documentar la duplicidad** (F7) en el diccionario y añadir consultas sugeridas que muestren
   el filtro correcto, para que el error no sea silencioso.
8. **Pruebas unitarias** de `ifrs_sectores` (F11, F8): reparto por sector, `orden`/`repeticion`,
   y un caso que demuestre que una relectura parcial **no** borra el trimestre.
