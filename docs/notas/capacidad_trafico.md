# Capacidad y tráfico del sitio

## Medidas activas en el repositorio

- El sitio y la API son archivos estáticos; DuckDB-Wasm procesa SQL en la pestaña del visitante. No se crea un servidor compartido de consultas.
- DuckDB se inicia de forma perezosa. Las consultas preparan únicamente las vistas usadas.
- La preparación de vistas/archivos remotos queda limitada a **4 operaciones simultáneas por pestaña**. Las peticiones concurrentes al mismo manifiesto o al mismo Parquet se deduplican en memoria.
- `scripts/audit_pages_capacity.py`, ejecutado por `web_audit.yml`, falla si `docs/` alcanza **900 MiB** y avisa desde 750 MiB. Es una guarda preventiva frente al máximo de 1 GiB de GitHub Pages, no una medida de ancho de banda.

Estas protecciones reducen ráfagas causadas por una consulta amplia de una persona; **no limitan el tráfico global entre visitantes**.

## Capacidad conocida y sus límites

El catálogo API/Descargas suma **728 Parquet, 487.665.291 bytes (≈488 MB)**. El directorio físico `docs/outputs/` contiene **805 Parquet, 548.713.850 bytes (≈549 MB)**: 728 del catálogo/descargas, 4 auxiliares SQL, 69 archivos en manifiestos separados y 4 muestras/registros con referencias de mantenimiento. Cifras verificadas contra la publicación `data_release` `2026-10-25.fb9d60ca0bd3`. Las categorías son excluyentes y `scripts/audit_pages_capacity.py` falla si queda un archivo sin clasificar. Esto describe archivos disponibles en el árbol publicado, no solicitudes ni uso real.

Si una aplicación descargara solo el conjunto completo del catálogo en cada visita, unas **205 transferencias completas** equivaldrían a 100 GB. El sitio normalmente lee sólo rangos y columnas requeridos, por lo que esa cuenta es un límite de referencia, no una estimación de visitas.

GitHub Pages publica un límite blando de 100 GB/mes y puede responder `429` ([límites oficiales](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)); Vercel Hobby anuncia 100 GB de transferencia y un millón de solicitudes CDN ([cuotas oficiales](https://vercel.com/docs/plans/hobby)). El plan activo de Vercel no se puede determinar desde este repositorio. Consultar las cuotas vigentes en el proveedor antes de tomar decisiones de capacidad.

Las lecturas Parquet usan rangos HTTP, como describe el [artículo de DuckDB-Wasm en PVLDB](https://www.vldb.org/pvldb/vol15/p3574-kohn.pdf). Se conserva `no-store` y el sufijo anti-caché aleatorio por carga: evita reutilizar respuestas de rango corruptas observadas en Chrome/Edge. Vercel no incluye solicitudes `Range` entre las respuestas elegibles para su caché CDN ([criterios oficiales](https://vercel.com/docs/caching/cdn-cache)), así que no se debe contar con su caché de borde para absorber estas lecturas.

## Operación recomendada

1. Revisar transferencia, solicitudes, errores `429`/`5xx` y caché por separado en cada hosting que sirva el sitio o los Parquet.
2. Si la transferencia proyectada supera la mitad de la cuota mensual, revisar qué rutas/archivos concentran bytes y preparar una alternativa antes de cambiar encabezados.
3. Si se acerca al 70 %, o aparecen `429` repetidos, probar una réplica de Parquet en un almacén/CDN con soporte explícito para `Range` y URLs versionadas por contenido. Mantener los manifiestos pequeños y revalidables.
4. Hacer pruebas de concurrencia en un despliegue de prueba o réplica, no bombardear el sitio de producción. Medir bytes, solicitudes, `206 Partial Content`, `Content-Range`, `429`/`5xx`, latencia y caché.
5. No añadir un endpoint SQL ni un rate limiter de aplicación para corregir este riesgo: la aplicación actual no recibe las consultas en servidor. Si se incorpora un backend en el futuro, entonces sí debe tener cuotas, límites de tiempo, límites de filas y protección WAF.

El cambio de caché de Parquet no es automático: primero debe reproducir las lecturas de rango en los navegadores afectados y verificar que los valores devueltos sigan intactos.
