# El monitor normativo se cayó por el origen, no por el repositorio

**Fecha:** 2026-10-23
**Motivo:** la corrida [40038135849](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/40038135849),
disparada por la mezcla del PR #65 en `main` (`ab673ee`), terminó en rojo en
«Monitor normativo CMF por industria».
**Método:** leer el registro del trabajo fallido, comprobar que el pipeline no
se tocó en esa mezcla y reproducir las pruebas del sector en local.

---

## 1. Qué falló

El paso «Actualizar publicaciones CMF y análisis respaldado»:

```
[WARNING] Consulta CMF intento 1/3 falló: SourceUnavailable
[WARNING] Consulta CMF intento 2/3 falló: SourceUnavailable
[WARNING] Consulta CMF intento 3/3 falló: SourceUnavailable
[ERROR] Actualización cancelada sin publicar falsos 'sin novedades':
        No se pudo validar el listado CMF luego de 3 intentos.
##[error]Process completed with exit code 1.
```

Los tres intentos ocurrieron entre las 23:11:11 y las 23:11:27 UTC: **16
segundos**. El listado de la CMF no respondió o no se pudo interpretar.

## 2. Qué no falló

- **El cambio mezclado.** El PR #65 sólo tocó `docs/index.html`,
  `docs/notas/`, `scripts/audit_interfaz_dom.js` y
  `scripts/build_indice_notas.py`. El flujo se dispara porque `docs/index.html`
  está en su lista de rutas, pero `git diff 78f5ff8..ab673ee -- pipelines/` está
  vacío.
- **Las pruebas.** El paso anterior corrió 39 pruebas y la auditoría web: todo
  en verde.
- **Los datos.** El guardián hizo lo que debía: al no poder validar el listado,
  no escribió `state.json` ni `feed.json`. La última revisión válida sigue
  siendo `2026-10-23T22:32:18Z`, la de la corrida anterior. Un `feed` con
  «sin novedades» habría sido una afirmación falsa sobre la CMF.

## 3. Lo que se corrigió

El comportamiento era correcto; la resiliencia, escasa. Tres cambios:

1. **Ventana de reintento de ~70 s** en vez de 16 s: cuatro intentos con
   esperas de 10, 20 y 40 segundos (`fetch_listing`). Una caída pasajera del
   origen ya no deja la corrida en rojo.
2. **Anotación en Actions** cuando el origen no responde:
   `::error title=CMF no disponible::… No se publicó nada: el feed conserva la
   última revisión válida.` El aspa roja dice qué pasó sin abrir el registro.
3. **Cinco pruebas nuevas** (`ListingRetryTests`): que se reintenta cuatro
   veces con espera creciente y se falla cerrado; que un intento posterior que
   sí responde devuelve las filas; que la página de error de la CMF queda
   descrita; que una página distinta sin filas también; y que en Actions el
   fallo de origen queda anotado. Se comprobó la mutación: volver a
   `attempts=3` con esperas de 5 y 10 segundos rompe dos pruebas, y quitar la
   descripción de la respuesta rompe otras dos.

## 4. Qué devolvía la CMF

La corrida siguiente a la mezcla del arreglo (`1c74153`, 23:33 UTC) volvió a
fallar: los cuatro intentos, repartidos en 70 s, dieron `SourceUnavailable`.
Eso ya descarta la caída pasajera: el origen responde, pero no con el listado.
Consultado a través de un lector público, el 23 de octubre a las 23:40 UTC el
listado devuelve **HTTP 200 con la propia página de error de la CMF**:

```
ERROR Linea 387 Archivo /web/SVS_website/institucional/legislacion_normativa/normativa2.php
```

No es un cambio de HTML ni un bloqueo: es un error de la aplicación de la CMF.
El repositorio no tiene nada que corregir ahí. Lo que sí se corrigió es que
ahora el mensaje lo diga —`HTTP 200, la CMF devuelve su página de error:
«ERROR Linea 387…»`— en vez de dejar «no se pudo validar» y parecer un fallo
propio.

## 5. Lo que queda

El monitor seguirá en rojo mientras la CMF no arregle su página, y **eso es lo
correcto**: el guardián no publica «sin novedades» cuando no pudo leer el
listado. `last_checked_at` conserva la última revisión válida y la web no
afirma nada nuevo. Cuando la CMF responda, la corrida siguiente publica sola.

No se puede relanzar desde el agente: la API responde 403 a `rerun` y a
`workflow_dispatch`.
