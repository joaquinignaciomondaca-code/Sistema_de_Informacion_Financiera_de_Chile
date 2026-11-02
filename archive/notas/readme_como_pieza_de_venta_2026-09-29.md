# El README como pieza de venta — 2026-09-29

La revisión anterior preguntaba *¿es cierto?*. Esta pregunta otra cosa:
**¿vende?**. Son criterios distintos y a veces opuestos: hay frases verdaderas
que restan, y hay cosas ciertas que no están dichas y deberían estarlo.

---

## 0. El diagnóstico en una línea

El README está escrito **para alguien que ya decidió estudiar el proyecto**, no
para alguien a quien hay que convencer de que lo estudie. Es un excelente
documento de referencia y una pieza de venta mediocre — no por lo que dice, sino
por lo que reparte: dedica 75 de sus 229 líneas a tablas de consulta y 10 a la
única sección que demuestra criterio.

---

## 1. Tres hallazgos que pesan más que cualquier edición de texto

### 1.1 El producto es invisible

**Cero imágenes en todo el repositorio.** Ni una captura, ni un GIF.

El argumento central del proyecto es *«una web donde consultas 8,9 millones de
filas con SQL desde el navegador»*. Es un argumento **visual**, y el documento
que lo defiende no muestra nada. El lector tiene que imaginarse el producto a
partir de una tabla de siete pestañas.

Una captura de la pestaña de consultas SQL con un resultado real cambia más la
percepción del proyecto que las 229 líneas de texto juntas. Es, con diferencia,
la mejor relación esfuerzo/impacto de toda la lista.

### 1.2 El sitio no está publicado

```
GET /repos/.../pages → 404 Not Found
```

GitHub Pages **no está activado**. El workflow `pages.yml` existe y es correcto,
pero nunca se habilitó el servicio, así que no hay sitio en vivo.

Esto tiene una consecuencia incómoda: el README dedica su sección más persuasiva
a explicar que todo corre en el navegador sin backend… y el lector no puede
comprobarlo salvo que clone el repositorio, instale Python y levante un servidor
local. Le estás pidiendo diez minutos de trabajo para ver la demo.

Activarlo son dos clics (*Settings → Pages → Source: GitHub Actions*). Es el
cambio de mayor impacto del proyecto entero y no requiere escribir una línea.

### 1.3 La ficha de GitHub está vacía

| Campo | Estado |
|---|---|
| Descripción | *(vacía)* |
| Website | *(vacío)* |
| Topics | *(ninguno)* |

Antes de que nadie lea el README, ve la ficha del repositorio: un título en
`snake_case` y nada más. Si alguien llega desde un CV o un enlace de LinkedIn,
esa ficha es la primera impresión, y ahora mismo no dice absolutamente nada.
Son 30 segundos de trabajo.

---

## 2. Lo que hay que mencionar y no está

### 2.1 Una consulta SQL de ejemplo, con su resultado

Es la promesa entera del proyecto y no aparece ni una sola vez. El README
explica *que* se puede consultar con SQL, nunca *enseña* una consulta. Tres
líneas de SQL que crucen dos sectores —cartera de seguros contra tasas del
BCCh, por ejemplo— demuestran en cinco segundos el valor que los párrafos
intentan argumentar en cinco minutos: que esto no son 52 archivos sueltos, sino
un modelo de datos unificado.

### 2.2 Para quién es esto

La §1 dice que los datos «existen, son públicos y son difíciles de usar». Es
cierto y está bien escrito, pero es un problema abstracto. No aparece nunca una
persona concreta: el analista de riesgo, el regulado que prepara un informe, el
periodista económico, el estudiante de finanzas. Sin esa persona, el lector no
tiene dónde colocar el proyecto.

La diferencia entre «normalizo RUT con módulo 11» y «cruzar la cartera de una
aseguradora con la de un fondo mutuo era imposible porque cada fuente escribe el
RUT distinto» es la diferencia entre describir una tarea y describir un
problema resuelto.

### 2.3 Que esto lleva meses funcionando solo

Es el dato más fuerte del proyecto y está enterrado dentro de una tabla de 12
filas. Un pipeline que corre programado, valida, publica con commit y abre un
issue cuando una fuente se atrasa —y que lleva meses haciéndolo sin que nadie lo
toque— es exactamente lo que separa un proyecto de portafolio de un sistema. El
README lo trata como una fila más de una tabla de frecuencias.

### 2.4 La escala, dicha en términos humanos

«8.942.793 filas» es un número. «25 años de historia del sistema financiero
chileno, desde enero de 2001» es una magnitud que se entiende sin pensar. Ambas
son la misma verdad; una se recuerda.

---

## 3. Lo que sobra, o está en el lugar equivocado

Nada de esto es falso. Todo esto compite por la atención del lector con lo que
sí vende.

| Sección | Líneas | Diagnóstico |
|---|---:|---|
| §8 Mapa del repositorio | **27** | Es la 2.ª sección más larga y es pura referencia. Nadie decide nada leyendo un árbol de directorios. Su sitio es `PSEUDOCODIGO.md`. |
| §4 Tabla de cobertura | 26 | 16 filas. Las primeras cinco impresionan; las once restantes son consulta. Top 5 + total, resto en `<details>`. |
| §5 Tabla de workflows | 22 | La idea vende en dos líneas; la tabla es operación. Plegar. |
| §6 Comandos de auditoría | 19 | Nueve comandos seguidos leen como un manual. Tres y un enlace transmiten lo mismo. |
| §7 **Decisiones de diseño** | **10** | **La mejor sección del documento y la más corta.** |

Ese último renglón es el problema de fondo. La §7 es el único lugar donde se ve
a alguien **pensando**: por qué fail-closed en vez de «algo es mejor que nada»,
por qué un vocabulario verificado en vez de disciplina, por qué alias en SQL
para no romper consultas ajenas. Eso es lo que un líder técnico compra. Y está
al final, después del árbol de directorios, en diez líneas.

**El orden también juega en contra.** Hoy es: problema → arquitectura → producto.
Vendiendo, sería: problema → **producto** (con imagen) → prueba de que funciona →
cómo está hecho → criterio. La arquitectura antes que el producto es el orden en
que se construyó, no el orden en que se entiende.

---

## 4. Tres cosas mías que, vendiendo, revisaría

Los cambios del PR #9 optimizaron exactitud. Dos de ellos pagan un precio en
percepción que conviene mirar:

1. **«Todos los derechos reservados: el repositorio aún no incluye un archivo
   `LICENSE`».** Es exacto y suena a inacabado. Vendiendo hay que elegir: MIT
   (señal de confianza, invita a mirar y reutilizar, es lo normal en portafolio)
   o una línea propietaria limpia y sin «aún». El estado intermedio es el peor.

2. **La deuda técnica «dos contadores de tablas».** Yo la añadí por rigor, y por
   rigor está bien. Pero anunciar que el repositorio se contradice a sí mismo es
   una herida autoinfligida: se arregla en una tarde regenerando
   `data_manifest.json` desde el mismo cálculo del catálogo, y entonces el punto
   desaparece en vez de publicarse. **Arreglar y borrar, mejor que confesar.**

3. **La sección «Deuda técnica conocida» completa.** Mantenerla es correcto y
   diferencia — casi ningún portafolio la tiene. Pero el título importa: *deuda
   técnica* mira hacia atrás, *próximos pasos* mira hacia adelante. Mismo
   contenido, lectura opuesta. Los dos puntos que quedarían (módulo `common/` y
   cobertura despareja) son decisiones de priorización, no defectos, y así
   deberían leerse.

---

## 5. Lo que ya vende bien (no tocar)

- **La nota «†» de banca.** Explicar que no se muestra un total engañoso porque
  dos vistas comparten particiones es el detalle más persuasivo del documento:
  demuestra que prefieres un número incómodo a uno bonito. Nadie inventa eso.
- **«Fail-closed antes que "algo es mejor que nada"».** Una frase, una postura
  profesional completa.
- **Las cifras verificables.** 26 de 26 correctas, con verificador que falla si
  se desactualizan. Es raro y es defendible en cualquier entrevista.
- **El bloque de badges y la tabla «En números».** La primera pantalla funciona.
  Solo le falta una imagen y un enlace en vivo.

---

## 6. Prioridad, si hubiera que elegir

Ordenado por impacto sobre esfuerzo:

1. Activar GitHub Pages y poner la URL en la primera línea. *(2 clics)*
2. Una captura de la pestaña SQL con una consulta real. *(10 minutos)*
3. Descripción, website y topics en la ficha del repositorio. *(30 segundos)*
4. Una consulta SQL de ejemplo con su resultado, en la §1. *(15 minutos)*
5. Mover el mapa del repositorio a `PSEUDOCODIGO.md` y plegar las tablas largas.
6. Subir «Decisiones de diseño» y desarrollarla.
7. Resolver la licencia en un sentido u otro.
8. Regenerar `data_manifest.json` y borrar ese punto de la deuda técnica.

Los tres primeros no requieren escribir prosa y valen más que cualquier
reescritura del texto.
