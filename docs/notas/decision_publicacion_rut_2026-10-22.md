# Publicar el RUT del emisor en `fi.cartera_nacional`: plan y justificación

**Estado:** propuesta, no ejecutada. Sustituye la regla vigente sólo si se aprueba.
**Objeto:** reponer `rut_emisor` para las 202.835 filas que hoy se publican sin identificador.
**Fecha:** 2026-10-22. **Vigencia legal relevante:** 2026-12-01 (Ley 21.719).

> **Estado (2026-10-23).** El contrato vigente es **2.0.0** y se publica en
> `docs/api/v2/`. Esta nota se escribió cuando la ruta era `api/v1/`: las rutas de
> archivo y de URL se actualizaron para que los comandos sigan funcionando, y las
> referencias a «v1» como nombre de la fase se conservan como se escribieron.

## 0 bis. Estado: lo que ya quedó implementado (2026-10-22)

Dos piezas del plan se ejecutaron sin cambiar la regla de publicación:

1. **Una sola columna de identificador** — `rut_emisor` conserva el RUT de las personas jurídicas
   y, en lugar del RUT de una persona natural, publica un seudónimo estable `EMI-…` derivado de él.
   Permite seguir a esa contraparte entre trimestres y fondos sin publicar su identidad, y resuelve
   el problema analítico que motivaba publicar el RUT.
2. **`rut_omitido_por_ley`** — booleano por fila: verdadero si `rut_emisor` trae el seudónimo, falso
   si trae el RUT.
3. **Interruptor de publicación** — `SIF_PUBLICAR_RUT_EMISOR=publicar` repone los RUT; el valor por
   omisión (`suprimir`) mantiene la regla. La compuerta de privacidad rechaza una publicación que
   mezcle los dos modos.

Con eso, publicar los 31.215 RUT deja de ser un cambio de código y pasa a ser un cambio de
configuración, reversible en una corrida. La decisión de fondo —si se activa— sigue abierta.

---

## 0. Qué se decide exactamente

Hoy `fi.cartera_nacional` publica `rut_emisor` para sociedades (730.593 filas) y lo deja nulo para
personas naturales probables (202.835 filas, 31.215 RUT), con la columna `emisor_tipo` que declara
el criterio aplicado.

La decisión es una sola: **publicar también esos 31.215 RUT**, o mantener la supresión.

No se decide aquí publicar nombres, correos ni direcciones: el conjunto no los contiene y la fuente
tampoco los ofrece para esta tabla. Publicar el RUT no agrega ninguna columna nueva al contrato.

---

## 1. Punto de partida medido

| Métrica | Valor |
|---|---|
| Filas suprimidas | 202.835 |
| RUT distintos | 31.215 |
| Fondos afectados | 28 de los 90 del catálogo de FI |
| Trimestres | 26 (2020-03 a 2026-06) |
| Peso en el monto del objeto | 0,28 % (795.356 de 288.512.050 miles de la moneda funcional) |
| Emisores presentes en más de un trimestre | 30.062 (96 %) |
| Emisores con más de un nemotécnico | 11.629 (37 %), máximo 194 |
| Emisores presentes en más de un fondo | 1.968 |
| Filas por emisor (promedio) | 6,5 |
| Filas con `codigo_grupo_empresarial` | 0 |
| Filas con participación en el capital (`pct_capital_emisor` > 0) | 2 |
| Coincidencias con otros 55 objetos del catálogo que tienen RUT | 0 |

Y lo que ya se publica hoy: 55 de 90 objetos tienen alguna columna RUT, incluidas dos listas
nominales de personas naturales (`fintech_rpsf_lista_entidades`, 264 filas, y
`corredoras_bolsa_lista_entidades`, 120 filas) y 317 nombres de tasadores.

---

## 2. La tesis a favor

**2.1. La ley no prohíbe publicar un RUT; regula el tratamiento.**
El RUT es dato personal (art. 2 f de la Ley 19.628 y de la Ley 21.719), no dato sensible (art. 2 g).
Ninguna de las dos leyes contiene una prohibición de publicar identificadores. Lo que exigen es base
de licitud y deberes asociados.

**2.2. Fuente pública con exención expresa, hoy.**
El art. 4 inciso quinto de la Ley 19.628 exime de autorización el tratamiento de datos provenientes
de fuentes accesibles al público «cuando sean de carácter económico, financiero, bancario o
comercial». La cartera trimestral de un fondo de inversión que publica la CMF es exactamente eso.

**2.3. Base de licitud declarada para el régimen que viene.**
El proyecto ya invoca interés legítimo (art. 13 d de la Ley 21.719) y ya tiene publicado el aviso
(`PRIVACIDAD.md`, `docs/privacidad.html`), con responsable, canal de derechos, plazo de respuesta,
conservación, destinatarios, seguridad y registro de actividades de tratamiento. La infracción más
frecuente del nuevo régimen —no tener aviso— no aplica aquí.

**2.4. Es el mismo dato que la fuente ya publica, sin ampliación de finalidad.**
La CMF publica el RUT del emisor en su página de cartera. El proyecto normaliza, tipifica y sirve
en Parquet lo mismo que ya está público, para un fin declarado (transparencia y análisis
reproducible). No hay recolección encubierta ni dato nuevo.

**2.5. El fin estadístico protege frente a la supresión.**
El art. 7 letra v) de la Ley 21.719 exceptúa la supresión cuando el tratamiento es necesario para
fines históricos, estadísticos o científicos de interés público. Un titular que pida borrado
encontraría una respuesta fundada, no un vacío.

**2.6. Suprimir tiene un costo analítico real y medible.**
Sin identificador estable del emisor no se puede: sumar la exposición total de una contraparte,
seguir su serie entre trimestres (96 % de los emisores aparece en más de uno), medir concentración,
ni cruzar entre fondos (1.968 emisores en varios). El nemotécnico no sustituye al emisor: 2.852
nemotécnicos son compartidos por emisores distintos y 37 % de los emisores usa varios.

---

## 3. Los contraargumentos, con su respuesta

Se enuncian en su versión más fuerte.

**3.1. «Publicar el RUT sin el nombre no anonimiza: el RUT identifica por sí solo.»**
Cierto. Quien tenga acceso a un padrón del SII identifica al titular. La publicación no es
anonimización; es publicación de un identificador. *Respuesta:* eso es igual de cierto para los
264 registros fintech y los 120 corredores que ya se publican con nombre y RUT, y para los cuales
la publicación se considera correcta. La diferencia no está en el identificador, sino en el hecho
asociado.

**3.2. «El hecho asociado es financiero: deuda, monto, fondo y trimestre.»**
Es la objeción más fuerte. Con 26 trimestres y 28 fondos, el conjunto permite construir un perfil
de solvencia de una persona natural que no optó por ser emisora de un fondo de deuda privada.
*Respuesta parcial:* el dato ya es público en la fuente, y el proyecto no lo enriquece ni lo cruza
con nombres. *Respuesta honesta:* la agregación sí agrega valor informativo, y eso es precisamente
lo que hay que ponderar.

**3.3. «El aviso dice que el proyecto no elabora perfiles.»**
Es exacto: `PRIVACIDAD.md` §3 lo afirma. Publicar el RUT en estas condiciones obliga a corregir esa
frase o a dejar de publicar. Cualquier versión del plan debe resolver esta contradicción antes de
fusionarse.

**3.4. «La tendencia legislativa va en contra.»**
Hay al menos cinco proyectos para restringir la publicación de datos de deudas (boletines
13897-03, 13695-03, 12924-03, 11841-03, 11716-07). Ninguno es ley. *Respuesta:* son proyectos, no
norma vigente; pero anticipan el criterio con que la Agencia podría ponderar.

**3.5. «Una multa grave son hasta 10.000 UTM y el proyecto no tiene patrimonio.»**
Cierto. El responsable es una persona natural y el régimen sancionatorio (arts. 34 bis a 36 de la
Ley 21.719) contempla hasta 10.000 UTM por infracción grave —tratar sin base de licitud— y 20.000
por las gravísimas. El riesgo no es teórico, pero recae sólo si la ponderación se declara
insuficiente, no por el hecho de publicar.

**3.6. «El interés legítimo exige ponderación, no basta invocarlo.»**
Cierto y es el nudo del asunto: finalidad legítima (sí), necesidad (discutible: un seudónimo
estable en `rut_emisor` cubre casi todo el análisis) y proporcionalidad (la más débil). La publicación se
sostiene mejor si se acepta que la necesidad es parcial y se argumenta sobre interés público.

---

## 4. Salvaguardas que harían sostenible la publicación

Sin estas seis, la publicación es difícil de defender. Con ellas, es defendible.

1. **Aviso corregido:** reconocer que se publican identificadores de emisores personas naturales y
   que el conjunto permite reconstruir su historial como contraparte. Retirar la frase «no elabora
   perfiles» o acotarla a «no elabora perfiles con fines comerciales».
2. **Canal de oposición operativo:** un procedimiento mensual que procese solicitudes y excluya al
   titular de la siguiente publicación, con constancia escrita. Hoy el canal existe (issues), el
   procedimiento de exclusión no.
3. **Lista de exclusiones versionada:** archivo privado con los RUT excluidos por solicitud del
   titular, aplicado por el pipeline antes de escribir.
4. **Minimización del resto:** no publicar nombre, ni correo, ni dirección del emisor (hoy no se
   publican); no ofrecer endpoint de búsqueda por RUT; no indexar los Parquet con nombres.
5. **Evaluación de impacto (art. 15 de la Ley 21.719):** documento corto que fije finalidad,
   necesidad, proporcionalidad, riesgos y medidas. Es el respaldo que la Agencia pediría primero.
6. **Reversibilidad:** conservar la versión suprimida como rama congelada (`git` ya la tiene: el
   commit `3b88beb` y su padre). Si la ponderación se cae, revertir es un `git revert` más volver a
   correr `enmascarar_identificadores.py`.

---

## 5. Plan de ejecución

- [ ] **Decisión y responsable.** Registrar la decisión, su fecha y quién la toma en esta nota.
- [ ] **Evaluación de impacto** (§4.5) escrita y enlazada desde `PRIVACIDAD.md`.
- [ ] **Aviso corregido:** `PRIVACIDAD.md`, `docs/privacidad.html` y el registro de actividades
      (§9) con la nueva fila: finalidad, titulares, categorías, base, origen, destinatarios, plazo.
- [ ] **Canal de oposición:** procedimiento y lista de exclusiones privada; el pipeline la aplica.
- [ ] **Código:** `pipelines/auto/privacidad.proteger_cartera_nacional` con un modo `publicar` que
      conserva `rut_emisor` y sigue calculando `emisor_tipo` para auditoría.
- [ ] **Datos:** repoblar los 26 Parquet desde `git show 3b88beb^:docs/outputs/fi/cartera_nacional/…`
      con `scripts/enmascarar_identificadores.py --revertir`.
- [ ] **Compuerta:** `scripts/auditar_personas_publicadas.py` cambia su bloque 4: en vez de exigir
      cero RUT de persona, exige que el aviso declare la publicación, que exista la lista de
      exclusiones y que `emisor_tipo` cuadre con `rut_emisor`.
- [ ] **Contrato:** `docs/api/v2/schema/fi_cartera_nacional.json`, `datapackage.json`,
      `queries.json`, `views.sql` y el diccionario con el nuevo significado de la columna.
- [ ] **Guía:** sección «si eres titular de un RUT publicado», con el enlace al canal.
- [ ] **Ejemplos:** uno reproducible que siga un emisor entre trimestres, usando el RUT como clave.
- [ ] **Compuertas locales y CI**; PR con la decisión, la evaluación de impacto y el diff de datos.

**Esfuerzo estimado:** 6–10 h de trabajo más la revisión del texto legal.

---

## 6. Riesgo residual

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Reclamo de un titular pidiendo supresión | Media | Bajo | Canal y exclusión en un ciclo mensual |
| Reclamo ante la Agencia por falta de base | Baja | Alto (hasta 10.000 UTM) | Evaluación de impacto y aviso corregido |
| Cambio legislativo que restrinja la publicación | Media en 12–24 meses | Medio | Reversión en horas; datos versionados |
| Daño reputacional por publicar deuda de personas | Media | Medio | Comunicar el criterio y el canal de oposición |
| Reidentificación por terceros con padrones del SII | Alta, fuera del control del proyecto | Alto | No se puede mitigar publicando; sólo no publicando |

La última fila es la que no tiene solución técnica: el RUT, por definición, identifica.

---

## 7. Preguntas abiertas para revisión externa

1. ¿El interés legítimo del art. 13 d de la Ley 21.719 sostiene la publicación del RUT de
   contrapartes de pagarés y mutuos hipotecarios, o se requiere consentimiento?
2. ¿La exención del art. 4 inciso quinto de la Ley 19.628 cubre la publicación en un sitio propio,
   o sólo el tratamiento interno?
3. ¿Un aviso que declare la publicación y un canal de oposición bastan para acreditar la licitud
   exigida por el art. 14 de la Ley 21.719?
4. ¿El fin estadístico del art. 7 letra v) impide la supresión pedida por un titular, o sólo la
   posterga?
5. ¿El deber del art. 14 bis —datos resultantes de organizar o combinar fuentes públicas— se
   satisface con medidas de seguridad, o exige no publicar?
6. ¿Es preferible publicar el RUT con el nombre del emisor ausente, o un seudónimo estable
   (un seudónimo estable en `rut_emisor`) que conserva todo el análisis y elimina el riesgo? ¿Qué se pierde en cada caso?

---

## 8. Fuentes

| Documento | URL |
|---|---|
| Ley 19.628, texto vigente y versión diferida | https://www.bcn.cl/leychile/navegar?idNorma=141599 |
| Ley 21.719 | https://www.bcn.cl/leychile/navegar?idNorma=1209272 |
| CMF, Descargo de responsabilidades | https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html |
| Dirección del Trabajo, Registro Público de Empresas Contratistas | https://www.dt.gob.cl/portal/1626/w3-article-98244.html |

Este documento es la lectura del proyecto sobre fuentes públicas. No es asesoría jurídica.
