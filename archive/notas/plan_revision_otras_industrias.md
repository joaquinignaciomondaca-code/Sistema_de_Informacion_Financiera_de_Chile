# Plan de revisión de las industrias restantes

Continuación del trabajo XML/XBRL. Cada fila indica qué falta comprobar exactamente y cómo
sabremos que la fuente sirve. Nada de esto se publica hasta pasar el cotejo de muestra que ya se
aplicó en Corredoras (ficha CMF vs dato extraído, período y moneda incluidos).

## A. Ya resuelto

| Industria | Fuente | Estado |
| :--- | :--- | :--- |
| Corredoras (`COBOL`) | XML IFRS `IVEF` | En uso; cotejo de 2 filas OK |
| Fondos mutuos (`RGFMU`) | XML IFRS `FMEF` | Descarga verificada; pendiente cargar histórico |
| Fondos de inversión (`FIRES`/`FINRE`) | XML IFRS `FIEF` (`pestania=29`) | Descarga verificada; pendiente cargar histórico |
| CCAF | XBRL (listado de envíos IFRS) | Ya en uso por el pipeline de CCAF |
| AFP | XML de la Superintendencia de Pensiones | Ya en uso por el pipeline de pensiones |

## B. Pendiente de identificar (hipótesis a probar, no hechos)

1. **Compañías de seguros (vida y generales).**
   Falta el `tipoentidad` de la ficha por compañía. CMF publica los módulos "IFRS Mercado de Seguros"
   y "XBRL Mercado de Seguros" (taxonomías `CL-HS` y `CL-BS`), así que la expectativa es XBRL.
   Cómo probarlo: tomar 2 compañías de vida y 2 generales desde el maestro de seguros del repo,
   abrir su ficha y buscar enlaces `XBRL`; si aparecen, bajar el archivo y comparar contra el PDF.
   Si ninguna ficha expone XBRL, revisar el módulo de cartera (Circular 1835) que ya usa el repo.

2. **Cooperativas de ahorro y crédito.**
   No se identificó IFRS XML por entidad; el repo hoy lee la serie de estadísticas del portal CMF.
   Cómo probarlo: revisar si existe envío XBRL como en CCAF (`novedades_envio_sa_ifrs.php`) y si el
   portal "Reportes Mensuales Cooperativas" entrega archivo estructurado. Si no hay XML, la serie
   actual se mantiene y se documenta el motivo.

3. **Patrimonios separados (securitizadoras).**
   Hoy se lee `pestania=18`. Cómo probarlo: revisar si ese módulo entrega XML/XLSX en vez de PDF y si
   el XML de la sociedad securitizadora (`RGSEC`) incluye los patrimonios o solo la matriz.

4. **Bancos.**
   CMF publica PDF y reportes mensuales (el repo ya parsea el TSV MB1: campos separados por tabulador, importes con ceros a la izquierda). Cómo
   probarlo: verificar si los reportes mensuales vienen en XBRL estructurado; si es así, comparar
   una línea del MB1 contra el XBRL antes de cambiar nada.

5. **AGF y retail financiero.**
   Ya hay XBRL, pero sin mapeo de taxonomía: contextos, dimensiones, moneda y consolidación.
   Cómo avanzar: construir un mapa de conceptos versionado (por año de taxonomía) y validar con una
   entidad y un período antes de generalizar. Mientras no exista el mapa, no se publican cifras.

6. **Sistemas de pago y FinTech (RPSF).**
   No tienen módulo de estados financieros en la ficha CMF. Solo cabría información societaria o
   registros; se documenta como "no aplica" salvo hallazgo nuevo.

## C. Criterio de aceptación (igual para todas)

* El archivo se descarga desde la ficha oficial de la entidad y período consultados.
* Identidad verificada: RUT/RUN y DV coherentes, período declarado igual al consultado.
* Moneda y escala declaradas en el propio archivo (miles de pesos, miles de dólar, `PROM`, `$$`).
* Cuadre según la estructura del sector (no todas las industrias suman igual: en FI el pasivo
  reportado incluye el patrimonio).
* Resultado del ejercicio presente; si falta, se marca, no se rellena con cero.
* Cotejo de una muestra contra la ficha CMF antes de publicar, con la fuente y el hash guardados.

## D. Riesgos abiertos que conviene no olvidar

* El XBRL de CMF viene con la advertencia de que su contenido "está en revisión": usar PDF como contraste.
* Los enlaces de CMF con token `auth=` son efímeros: se obtienen de la ficha en cada corrida.
* El laboratorio en Actions no debe confundirse con datos: un job en verde puede no haber extraído nada;
  el resumen declara `estado_global` y el backfill manual falla si no validó ninguna fila.
