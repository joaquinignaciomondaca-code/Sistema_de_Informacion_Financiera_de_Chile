# Despliegue de Pages: tope de CSV a 10 MB y totales del aviso de privacidad

**Fecha:** 2026-11-09 · **Origen:** el despliegue de `main` falló con
`Timeout reached, aborting!` (estado `syncing_files`) y `web_audit` quedó en rojo
en `main` por una cifra del aviso de privacidad. Son dos problemas distintos que
se arreglaron en la misma pasada porque comparten causa: cifras y pesos escritos
a mano que se separan de los datos publicados.

## 1 · El despliegue se cayó por peso, no por contenido

Lo que se vio en la corrida cancelada:

```
Current status: syncing_files        (repetido ~10 minutos)
Error: Timeout reached, aborting!
Canceled deployment with ID 230a99ca26e363cf2b2f6ecf61696bccbf14ea63
```

`syncing_files` es el estado en que el servidor de Pages recibe el artefacto.
`actions/deploy-pages` espera como máximo 10 minutos (`MAX_TIMEOUT = 600000`) y
no se puede subir: es un tope del propio action. Con `docs/` en **866,9 MiB** el
envío no alcanzaba a terminar.

Medido sobre las últimas 94 corridas del publicador de Pages (`main`): 61 con
éxito, 2 con fallo y 31 canceladas. Las canceladas son la misma congestión vista
desde el otro lado: un push nuevo cancela el envío anterior. Los éxitos tardan
entre 80 y 150 s, así que el margen es real pero se consume cuando el payload
crece.

### Qué se cambió

El peso no estaba en los datos: 549,8 MiB son Parquet (imposible de reducir sin
perder cobertura) y 276 MiB eran los CSV/JSON pre-generados por
`scripts/build_download_exports.py`, que existían para que Power BI y Data Studio
lean series largas sin generar nada en el navegador. Once conjuntos concentraban
195,4 MiB de esos CSV:

| Conjunto | CSV | Filas |
|---|---:|---:|
| `ffmm_balance` | 33,3 MiB | 126.256 |
| `ffmm_futuros` | 26,5 MiB | 282.045 |
| `seguros_acciones` | 25,7 MiB | 109.019 |
| `seguros_fondos_mutuos` | 20,8 MiB | 100.472 |
| `corredoras_bolsa_balance` | 18,3 MiB | 109.305 |
| `corredoras_bolsa_resultados` | 15,2 MiB | 78.683 |
| `seguros_acciones_relevantes` | 12,6 MiB | 109.019 |
| `agf_balance` | 12,0 MiB | 71.423 |
| `seguros_control_inversiones` | 10,6 MiB | 111.410 |
| `fi_cartera_extranjera` | 10,4 MiB | 76.849 |
| `seguros_otras_inversiones` | 10,3 MiB | 42.494 |

Se bajó `CSV_MAX_MB` de 35 a **10** por conjunto. Resultado medido:

- `docs/`: **866,9 → 671,5 MiB** (1.493 → 1.482 archivos).
- Exportes publicados: 68 → **57 CSV**, 249,7 → **44,8 MB**.
- Ningún dato desaparece: los 11 conjuntos conservan su Parquet publicado y su
  CSV se genera en el navegador con DuckDB-Wasm, igual que hoy ocurre con los
  conjuntos que tienen filtro SQL. El panel de Descargas ya muestra el botón
  «CSV» en ese caso (`docs/js/downloads_panel.js`), sin cambios de interfaz.

**Defecto encontrado al aplicarlo:** el pase incremental comparaba sólo la firma
de la fuente («no cambió el Parquet, conservo el CSV»). Al bajar el tope, el CSV
de 33 MB seguía publicado y la bajada no tenía efecto. Ahora un CSV registrado
que supera el tope vigente se retira; la regresión tiene prueba
(`test_bajar_el_tope_retira_el_csv_ya_publicado`).

## 2 · El aviso de privacidad declaraba 267 prestadores y había 268

`web_audit` fallaba en `main` con:

```
[FALLA] fintech: 268 filas; el aviso declara 267 prestadores
```

La CMF dio de alta un prestador en el Registro de Prestadores de Servicios
Financieros (Ley 21.521). El pipeline hizo lo correcto —publicar la fila nueva— y
el aviso quedó un alta atrás; el único arreglo posible era editar el número a
mano, y el mismo rojo vuelve con la próxima entidad.

### Qué se cambió

`PRIVACIDAD.md` declara dos clases de cifra y conviene no confundirlas:

- **El criterio de privacidad:** 36 personas naturales en FinTech, 11 corredores
  personas naturales, 317 nombres de tasadores (233/263). Se revisan a mano y la
  compuerta debe fallar si cambian, porque cambia el riesgo.
- **El tamaño del registro de la fuente:** «de N prestadores», «de M
  corredoras». Son cifras de la CMF y no dicen nada del riesgo.

Las segundas ahora las escribe `scripts/build_privacidad_cifras.py`, que va en la
cadena derivada (`scripts/cadena_contrato.py`) **antes** de `build_metadatos.py`,
de modo que el Markdown y su espejo `docs/privacidad.html` quedan al día en la
misma pasada que el catálogo. El script:

- reescribe sólo los totales; los conteos del criterio quedan intactos y su
  compuerta sigue funcionando;
- falla si el texto cambió de forma y no encuentra el total, en vez de pasar en
  silencio;
- acepta `--check`, así que `refrescar_contrato.py` lo verifica y `web_audit`
  avisa en el push cuando alguien publica la tabla sin regenerar la cadena.

`scripts/auditar_personas_publicadas.py` ya no trae 267 y 120 escritos: lee la
cifra **del aviso** y la contrasta con los Parquet. La compuerta sigue midiendo
lo que debe medir —que el aviso no se separe de los archivos— y se probó en los
dos sentidos: con el aviso atrasado falla (`el aviso declara 267`), con el aviso
al día pasa.

## Qué no se cambió

- Los Parquet, sus particiones, la API v2 y el contrato derivado: el
  `data_release` sigue en `2026-11-09.520df1378a5c`.
- El umbral preventivo de `scripts/audit_pages_capacity.py` (900 MiB). El AVISO
  bajó de 870 a 700 MiB, que es el margen nuevo para crecer antes de que un
  despliegue vuelva a acercarse al timeout.
- La página de privacidad conserva su redacción y su estructura; sólo cambia el
  total del registro.

## Lo que queda abierto

- El peso del sitio es ahora 671,5 MiB, pero cada periodo nuevo de seguros suma
  ~10 MiB de Parquet: el margen es de meses, no indefinido. La salida de fondo
  es externalizar los Parquet a un almacén con soporte de `Range`
  (`archive/notas/capacidad_trafico.md`, punto 3 de la operación recomendada).
- Un despliegue cancelado por un push nuevo no es un fallo, pero cuenta como
  rojo en el historial. Si vuelve a ocurrir, la lectura correcta es «congestión
  de publicadores», no «el sitio está caído»: el sitio siguió sirviendo la
  publicación anterior.
