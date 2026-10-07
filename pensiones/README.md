# Fondos de pensiones — estado de publicación

**Publicado en el sitio:** únicamente `afp_maestro_administradoras` con cuatro campos de identificación (`id`, RUT, razón social y nombre de fantasía). Son entradas conservadas de un catálogo local; identidad y vigencia todavía requieren cotejo con la Superintendencia de Pensiones. El maestro **ya no contiene** AUM, afiliados, comisiones, encaje ni participación calculada.

El 27-09-2026 se retiraron las antiguas carteras de bonos/acciones, derivados (incluidos forwards sintéticos), agregados y particiones históricas para permitir una extracción desde cero. Los scripts anteriores en `pensiones/scripts/` permanecen **sólo como referencia de laboratorio**: no volver a ejecutar `generate_cartera_afp.py`, `generate_derivados_afp.py`, los extractores ZIP/XML o consolidadores contra `docs/outputs/` sin corregir primero su interpretación de listados y unidades, y cotejar su salida con la fuente oficial. El generador `generate_afp_maestro.py` sólo publica campos de identidad. Ver [auditoría AFP](AUDITORIA_AFP_2026-09-27.md) para los problemas detectados y criterios de validación.

## Investigación de derivados (07-10-2026)

La revisión de fuentes identifica dos vías oficiales complementarias: **SP, listados 22–29**
para posiciones agregadas por AFP/fondo, y **BCCh/SIID-TR, monitor específico de fondos de
pensiones** para montos vigentes y transados y códigos API-BDE. Las notas oficiales de SP
confirman que los swaps de los listados 26/28 son **valorizaciones firmadas, no nocionales**;
no deben filtrarse sus importes negativos ni reutilizarse los antiguos generadores.

**Objetivo de detalle tipo FI:** la captura del usuario confirma que el portal BDP ofrece
carteras históricas desde 1996 y documentación. Un manual SP histórico y un XLSX 2021
inspeccionados en un espejo GitHub contienen 18 columnas con serie, entidad, unidades,
strike de forwards y tasas de swaps. Falta cotejar los CSV originales vigentes: el espejo
muestra indicios de alteración decimal y la serie no identifica de forma única un contrato.
El manual histórico restringe la base a investigación y solicita no redistribuirla; revisar
condiciones actuales/autorización **antes de publicar datos o derivados masivos en el SIF**.
No se incorporó el dataset a Git ni se reactivaron tablas.

Ver [fuentes, evidencia, límites y plan de extracción](FUENTES_DERIVADOS_2026-10-07.md).
Esta investigación no reactiva ninguna tabla ni certifica una extracción ZIP/XML nueva.

### Extracción masiva de toda la cartera

El BDP no se limita a derivados. El [plan de extracción y separación por tablas](PLAN_EXTRACCION_CARTERAS_BDP.md)
propone 14 familias observadas en el espejo 2021, rutas adicionales sujetas a evidencia,
un staging canónico, particiones anuales, catálogo histórico y controles de conservación
de filas. Es un diseño pendiente del CSV SP original y la revisión de condiciones de uso;
no una activación del backfill antiguo.

### Preparación reproducible para Actions y Vercel

El [estado de implementación y guía de activación](AUTOMATIZACION_BDP.md) documenta
la descarga oficial con catálogo de URLs aún bloqueado, el staging CSV/ZIP reanudable,
las actualizaciones incrementales por paquete, las auditorías y el gate de publicación.
**No se han descargado originales SP ni se publican carteras**: faltan el flujo real del
botón BDP, cotejo de campos/cifras, condiciones de redistribución y configuración del
runner privado/Vercel. No hay nuevas tablas BDP en `data_manifest.json` ni en el explorador.
