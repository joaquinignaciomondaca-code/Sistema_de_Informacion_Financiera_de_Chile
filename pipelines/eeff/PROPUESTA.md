# Propuesta: factoring y leasing

Una industria. Dos secciones. La llave no es el número de la nota.

## Las dos secciones

**EEFF.** Solo el PDF de Información Financiera. Balance, estado de resultados y las notas comunes, cada una en su tabla. La API no escribe filas aquí.

**De Interés.** Maestro y serie histórica de totales de la API, para la tendencia. No es el estado. Las tablas de porcentajes fijos no vuelven a EEFF.

Flujo de efectivo y cambios en el patrimonio están en el PDF y la norma los pide. No entran en esta vuelta. Quedan en el archivo.

## La llave

El número cambia de año y de sociedad. Security, la misma empresa:

- 2013, nota 13: «Préstamos que devengan intereses». La carátula dice otros pasivos financieros y cita la 13.
- 2018, la misma nota 13, el mismo título.
- 2026-03, nota 13: «Otros pasivos financieros corrientes».

Patrimonio en 2013 y 2018 se llama «Movimientos de patrimonio». En 2026, «Patrimonio». Gastos de administración en 2013 no tiene nota. En 2018 es la 23. En 2026 es la 22.

La llave es el nombre económico, con alias. «Préstamos que devengan intereses» es otros pasivos financieros. «Movimientos de patrimonio» y «capital y reservas» son patrimonio. Si el título de 2026 no aparece, no es que la nota no exista.

Un índice cortado no niega una nota. Eurocapital, en el archivo de marzo, solo tiene las notas 5 a 8.

## Qué se guarda

Carátula, una fila por línea del PDF. Se guarda el nombre tal como viene y, al lado, la cuenta canónica cuando el alias calza. No se renombra el PDF para que se parezca a la API.

Columnas de carátula que están en las siete carátulas completas de marzo 2026: efectivo, deudores, otros activos no financieros, propiedades planta y equipo, cuentas por pagar comerciales, relacionadas por pagar, otros pasivos financieros, capital, ganancias acumuladas, total de activos, total de patrimonio, ingresos, costo de ventas, ganancia bruta, unidades de reajuste, impuesto y ganancia del periodo. El gasto de administración se guarda. En Penta la cifra quedó cortada: se deja vacía, no se completa a ojo.

Notas, una tabla por nombre. No una bolsa `nota_lineas`.

Comunes en los nueve índices que cubren esa zona:

| Tabla | Alias que hay que aceptar | Estructura |
| --- | --- | --- |
| nota_efectivo | efectivo y equivalentes | concepto, saldo del corte, saldo comparativo. Ya leída en Security |
| nota_deudores | deudores comerciales, cuentas comerciales por cobrar | producto, colocación, provisión, neto. El que cuadra con el balance es el neto. Ya leída en Security |
| nota_pasivos_financieros | otros pasivos financieros, préstamos que devengan intereses | no leída. No se inventan columnas |
| nota_cuentas_por_pagar | cuentas por pagar comerciales, cuentas comerciales y otras cuentas por pagar | no leída |
| nota_relacionadas | relacionadas, transacciones con entidades relacionadas | no leída. Autofin a veces titula solo el por pagar |
| nota_impuestos | impuesto corriente, diferido, gasto por impuesto. A veces son dos notas y una tabla | no leída |
| nota_patrimonio | patrimonio, movimientos de patrimonio, capital y reservas, capital emitido | no leída |
| nota_ppe | propiedades planta y equipo, plantas y equipos | no leída |

Ingresos está en los nueve, pero no es la misma tabla. Security los junta con costos, Autofin les mete la administración, Tanner los llama composición de resultados. Se guarda la línea de la carátula. La nota de ingresos no entra como tabla común hasta ver, en un solo PDF, si el corte es comparable.

No entran como tabla obligatoria, porque un índice completo no las tiene: otros activos financieros y valor razonable (faltan Security y General Motors), intangibles (falta General Motors), arrendamientos, deterioro como nota propia, inventario, plusvalía, asociadas, mantenidos para la venta. Si el PDF las trae, quedan en el índice con `extraida=0`. No se inventa la fila.

Medio ambiente, contingencias, cauciones, sanciones y hechos posteriores son el cierre que pide la práctica CMF. No mueven el balance. Quedan en el índice, no como tabla de montos.

## Validación

Dos chequeos. Ninguno rellena.

1. La nota contra su propia carátula. El total de efectivo es la línea de efectivo. El neto de deudores es la línea de deudores. Si no cuadra, la nota queda marcada. No se ajusta.
2. La carátula contra `ver_archivo.php`. Misma sociedad, mismo periodo, mismo tipo: individual contra individual, consolidado contra consolidado. El PDF está en miles. La API, en pesos. Se compara miles dividido por mil contra el millón de la API. Tolerancia de un millón de pesos. Si difiere, gana el PDF y la fila queda `DIFIERE`. Si el PDF no trae la línea, queda `SOLO_API`. No se copia el número.

La API no tiene las notas. No valida colocación ni provisión.

## Orden

1. Diccionario de alias, antes de parsear el resto. Sin eso, 2013 no entra.
2. Security, marzo 2026, las seis notas comunes que todavía no tienen tabla leída. De ahí salen las columnas. Si una tabla no tiene forma estable, no se masifica.
3. Recién ahí, las otras nueve de marzo 2026. Tanner y Eurocapital no se completan con el HTML.
4. Otros años, Security 2013 y 2018 incluidos, con el mismo diccionario. No con los números de 2026.

El loop de descarga ya existe. Desde esta red CMF no responde. No se reintenta el TLS para simular que el masivo está listo.

## Cuándo está lista esta vuelta

- Security marzo 2026 tiene las ocho tablas de nota, o una marca explícita de que esa tabla no se leyó.
- Cada tabla cuadra con su línea de la carátula, o queda marcada.
- Ninguna nota vive en `nota_lineas`.
- La API no ha escrito una cifra en EEFF.
