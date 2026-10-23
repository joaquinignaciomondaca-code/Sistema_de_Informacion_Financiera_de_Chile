# La portada, escrita para quien entra por primera vez

**Fecha:** 2026-10-23
**Motivo:** revisión de la portada «de cara a una persona que entra a la
página». La etiqueta «Calidad medida: 230.288 filas repetidas en origen», que
para quien mantiene el proyecto es transparencia, se lee como un defecto para
quien llega sin contexto. El mismo problema aparecía en otras frases del panel
Información.
**Método:** medir el texto visible del panel con jsdom (17.588 caracteres,
diez bloques), buscar frases coloquiales y de segunda persona, y reescribir sin
tocar una sola cifra: las 21 del HTML siguen respaldadas por el catálogo
(`scripts/audit_cifras.js`).

---

## 1. Qué se cambió y por qué

| Antes | Ahora | Razón |
|---|---|---|
| Etiqueta en el héroe: «Calidad medida: 230.288 filas repetidas en origen», con enlace al bloque | Eliminada; tres etiquetas neutras: «Consultas SQL en el navegador», «Parquet, CSV y Excel», «Sin registro» | Una cifra de filas repetidas como reclamo de la primera pantalla describe un problema interno, no lo que el sitio ofrece. La medición sigue en su sección y en el Diccionario |
| Cuatro cifras del héroe mezclaban núcleo (40 conjuntos, 17 M) con catálogo (74, 19 M) | Las cuatro describen **el catálogo publicado**: 3 fuentes oficiales · 74 tablas en la vista principal · más de 19 millones de filas · 2001–2026 de cobertura | Dos universos en la misma fila obligan al visitante a averiguar cuál es cuál. El núcleo tiene su propia línea, en su sección |
| Lead del héroe largo, con enumeración de fuentes y formatos | Lead de tres frases: qué datos, de quién, y cómo se consultan | Lo mismo, sin repetir lo que ya dicen las etiquetas |
| Cifras del núcleo repartidas en el texto de la sección | Una línea bajo el título: «40 conjuntos en 3 sectores · más de 17 millones de filas» | La cifra del núcleo se lee donde se habla del núcleo, con sus `data-alcance` intactos |
| Bloque de calidad: tres párrafos con la defensa del criterio, las cifras, el gráfico y la consulta a la vista | Un párrafo en llano con la advertencia y el número, enlace al Diccionario, y un plegable «Detalle técnico y verificación» con cifras, gráfico, consulta y pie de comprobación | Quien entra necesita saber que una suma sin agrupar puede sobreestimar; la reproducibilidad es para quien va a comprobarla |
| Alcance: kicker de desarrollo, título largo y pie con tres frases | Kicker «ALCANCE», «Qué incluye cada grupo» y pie con la cifra | El encabezado de una tabla no es el lugar para justificar la clasificación |

Se retiraron además las frases que hablaban del proyecto desde dentro («telón
de fondo», «no es una foto fija», «no hay que creerle», «no las borra»,
«nadie sume de más»). Ninguna cifra cambió: 230.288 filas idénticas, 22 de 90
objetos, 160.564 en `ffmm_cartera_nacional` (10,1 %), 9,7 % de
sobreestimación en 2026-09, más de 17 millones en el núcleo y más de 19
millones en el catálogo visible.

## 2. El plegable y el gráfico

El detalle técnico es un `<details>` cerrado por defecto. El gráfico de barras
vive dentro y **no se construye al cargar**: cerrado, el contenedor no tiene
ancho y el lienzo saldría vacío. `docs/js/calidad_datos.js` lo pinta la primera
vez que se abre (`toggle`), y una sola vez. Las cifras del plegable se pintan
igual que antes desde `js/estado_claves.js`, de modo que con JavaScript
desactivado se lee el valor del HTML y nunca un cero.

## 3. Verificación

`scripts/audit_interfaz_dom.js` suma cinco comprobaciones (104 en total):

- el registro técnico arranca plegado;
- la explicación está en llano, lleva el número y no cita SQL;
- la advertencia y el enlace al Diccionario quedan a la vista;
- el gráfico no se construye con el plegable cerrado;
- al abrirlo aparecen el gráfico y la consulta, y las cifras siguen medidas.

Se comprobó que la prueba falla con la avería correspondiente: abrir el
plegable por defecto rompe la comprobación del plegado y la del gráfico. El
resto de la batería quedó en verde: `audit_interfaz.py`, `audit_movil.py`
(14/14, autoprueba de 13 mutaciones), `audit_movil_dom.js` (15/15),
`audit_aviso_movil.js` (23) y `audit_cifras.js` (21 respaldos, 8 cifras de
calidad, 0 desfasadas).
