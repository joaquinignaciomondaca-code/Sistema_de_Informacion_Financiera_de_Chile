# Mapa relacional, cifras y contrato: lo que se corrigió el 2026-10-23

> **Snapshot histórico (2026-10-23).** Las mediciones de filas y fallos documentan el release revisado ese día; las cifras vigentes se regeneran desde el catálogo y están en [`metricas_publicadas.json`](../metricas_publicadas.json).

**Fecha:** 2026-10-23
**Motivo:** tres defectos vistos en pantalla —los títulos del mapa relacional se
salían de su tarjeta, las cifras se redondeaban al alza y estaban escritas a
mano— y una decisión pendiente sobre `fi_bienes_raices`.
**Método:** medir el render del canvas con un contexto falso (no a ojo), comparar
cada cifra del HTML con lo que calcula la página, y reproducir el vacío de
`fi_bienes_raices` sobre el Parquet publicado.

---

## 1. El mapa relacional tenía cuatro defectos, no uno

La captura del usuario mostraba un título que pisaba la insignia de la tarjeta
vecina. Al medir las coordenadas y los textos apareció más:

| Defecto | Medición |
|---|---|
| Dos tarjetas en la misma coordenada | `seguros_registros_tipo6` y `seguros_acciones_relevantes`, las dos en (1280, 1080) |
| Una tercera debajo de otra | `ffmm_resultados` en (1340, 1099), bajo una tarjeta que llega a x=1540 |
| Título sin límite | 118 caracteres en una tarjeta de 240 px; `fillText` sin `maxWidth` ni `clip` |
| Insignia sin hueco | se pintaba siempre a la derecha del título, sin medir cuánto quedaba |
| Tipo de columna con desplazamiento fijo | `x + w − 55`, encima de los nombres largos |
| Cinco columnas siempre | aunque la tarjeta tuviera alto para tres |

**Arreglo:** coordenadas libres; título recortado con «…»; la insignia pasa a su
propia línea si al título no le quedan 110 px; tipos medidos y alineados a la
derecha; número de filas de columnas calculado con el alto real; `clip()` a la
tarjeta; nombre completo bajo el puntero en una etiqueta fija.

**Prueba:** `scripts/audit_erd_visual.js` dibuja los 84 nodos con un canvas falso
y mide cada `fillText`. Con el código anterior marca **19 textos fuera de su
tarjeta**; con el nuevo, **0**. También detectó los dos solapes de coordenadas,
que no se ven sin medir.

## 2. Las cifras: truncar hacia abajo y no escribirlas a mano

La portada decía «19,7 millones de filas (99,5 % de los 19,8 millones
publicados)» con 19.777.517 filas. Las dos cifras eran redondeos al alza.

- **Regla:** se trunca (nunca al alza), con «más de» cuando queda resto, a dos
  cifras significativas: 19.777.517 → «más de 19 millones»; 4.312.000 → «más de
  4,3 M»; 185.921 → «más de 185 mil».
- **Generadores:** `build_metadatos.py` y `build_og_image.py` leen el catálogo. El
  PNG social llevaba «90 objetos · 19,8 millones de filas» impreso en el archivo.
- **Respaldos sin JavaScript:** los `data-alcance` de `index.html` ahora coinciden
  con lo que pinta `portada.js`. Tres no coincidían: seguros decía **9 conjuntos
  y son 24**, y AGF y corredoras mostraban la cifra exacta vieja.
- **Guarda:** `scripts/audit_cifras.js` compara los 18 respaldos y verifica que
  ninguna cifra declare más de lo que hay.

## 3. `fi_bienes_raices`: se conserva el archivo vacío y se declara

Publica `docs/outputs/fi/bienes_raices/vacio.parquet` con **0 filas** y las 15
columnas del esquema, porque la vista SQL se construye sobre ese archivo.
Retirarlo dejaría la vista sin origen; y publicar el esquema con cero filas es más
honesto que esconder que la fuente no informa cartera de bienes raíces desde
2020.

La diferencia de uno deja de ser una resta: el contrato **2.1.0** añade
`totales.con_filas` (**85**) junto a `totales.con_datos` (**86**). Los cuatro
números tienen nombre: 90 objetos · 89 conjuntos del explorador · 86 con archivo
· 85 con filas.

## 4. Fechas que no cambiaban

La barra del visor decía «Actualizado: 2026-09-23» en todas las tablas desde el
primer día, y el Diccionario usaba la misma fecha de respaldo. Ahora salen del
Diccionario o del catálogo de descargas, y si no hay fecha el distintivo no se
pinta.

## 5. La lección de la etiqueta de caché

El cambio se publicó, pero `docs/index.html` seguía cargando los `js/*.js` con
`?v=fl-202610-2314-claves-y-og`, la etiqueta de la ronda anterior. El código nuevo
estaba en el servidor y, aun así, un navegador que hubiera entrado antes podía
seguir ejecutando el mapa viejo durante la ventana de caché de Pages (600 s).

Subirla era un paso manual que dependía de acordarse. Ahora es un comando:

```bash
python3 scripts/subir_etiqueta.py mapa-y-cifras
```

`--check` falla si las 22 referencias no comparten una sola etiqueta o si alguna
se quedó sin ella, y `scripts/audit_interfaz.py` lo ejecuta en cada auditoría.
