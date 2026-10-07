# Automatización BDP: implementación y bloqueo de publicación

## Disponible en esta rama

- `scripts/extraer_carteras_afp.py`: lectura local de CSV originales separados por
  `;`, solos o dentro de ZIP, en lotes de 10.000 filas por familia. No extrae rutas
  ZIP al disco. Guarda Parquet comprimido únicamente bajo `.local-data/`.
- `config/familias_bdp.json`: 63 códigos observados, distribuidos en 14 familias
  disjuntas. No es todavía un catálogo histórico exhaustivo: cualquier otro código
  se conserva en `otros_no_clasificados` y bloquea la auditoría.
- `scripts/audit_carteras_afp.py`: comprueba esquema, conservación por fuente y
  familia, cobertura fecha×AFP×fondo×instrumento, inventario de particiones y
  unicidad del linaje. No deduplica registros económicos ni cuenta contratos.
- `.github/workflows/pensiones_carteras.yml`: pruebas sin red en push/PR,
  ejecución manual y control mensual el día 10 a las 10:25 UTC. **No descarga ni
  publica datos**. El horario empieza a aplicar al integrarse en la rama por defecto.

## Ejecutar con originales descargados legítimamente

```bash
python -m pip install pyarrow==21.0.0
python pensiones/scripts/extraer_carteras_afp.py \
  .local-data/originales/carteras.zip \
  --output .local-data/pensiones/corrida-001 \
  --encoding cp1252 --max-archivos 50 --minutos 60
python pensiones/scripts/audit_carteras_afp.py .local-data/pensiones/corrida-001
python -m unittest discover -s pensiones/tests -v
```

Elegir `cp1252` o `utf-8-sig` según el original; no hay sustitución silenciosa de
caracteres. Cada corrida exige directorio nuevo. Un fallo o límite deja
`audit.json` incompleto y nunca habilita publicación. No subir staging como artifact
público de Actions. No utilizar XLSX del espejo para el backfill numérico.

### Límites deliberados de esta primera etapa

Los 18 campos originales permanecen **VARCHAR**, con sus decimales y signos
literales. No se adivinan separadores ni escalas: todavía no hay columnas
numéricas certificadas. La fecha tampoco se interpreta hasta cotejar el formato.
Las particiones son por familia y lote, no aún por año normalizado. El hash es
sobre el CSV descomprimido; `numero_fila_fuente` es el número de registro CSV
(incluye cabecera), no la línea física si hay saltos dentro de una celda.
`fecha_ingestion` registra el instante de ingestión local, no una
fecha de descarga acreditada por la SP. El auditor mantiene IDs en memoria;
para todo el histórico necesitará un índice externo si supera la RAM disponible.
No hay reanudación/incremental ni selección desde/hasta: una corrida limitada
no se presenta como histórico completo.

## Pendiente para activar extracción y publicación automáticas

1. Obtener un CSV/ZIP **original SP** y comprobar cabecera, fechas, encoding,
   separadores, precisión, unidades y controles contra lo publicado por la SP.
2. Documentar las condiciones vigentes de redistribución o autorización aplicable.
   El manual histórico restringe distribución: no basta que el archivo se pueda
   descargar. Ningún booleano de configuración sustituye esa evidencia.
3. Verificar en el navegador la solicitud real de descarga BDP. Implementar el
   adaptador oficial sin inventar URLs/POST/tokens ni eludir controles de acceso.
4. Completar normalización decimal exacta, catálogo histórico, particiones por
   año y reemplazo idempotente de revisiones. Validar cobertura antes de publicar.
5. Implementar publicación atómica, manifiestos por tabla, `data_manifest.json`,
   vocabulario, vistas DuckDB, visor, ERD, navegación y catálogo de descargas,
   con las auditorías web y de automatización del repositorio. No registrar tablas
   vacías ni vínculos a manifiestos inexistentes ahora.
6. Habilitar un job de publicación con permisos mínimos y reintentos ante cambios
   concurrentes. No se ha añadido todavía: hoy el workflow tiene sólo lectura.

## Vercel

El repositorio contiene configuración de cabeceras Vercel, pero eso **no demuestra
que exista un proyecto conectado**. Para el sitio estático, confirmar en Vercel:

- repositorio correcto y rama de producción elegida por el propietario;
- preset «Other», raíz `docs`, sin comando de build (sitio estático);
- preview de la rama de trabajo antes de integrar;
- integración Git activa o, para commits automáticos, un deploy hook protegido
  como secret. Verificar con una ejecución real: un push con `GITHUB_TOKEN` no
  dispara otros workflows de GitHub, y no se debe asumir un despliegue Vercel.

No se han creado proyectos, secrets, hooks ni despliegues remotos. El workflow
`pages.yml` existente despliega GitHub Pages por separado; no configura Vercel.
Hasta completar los puntos anteriores, el sitio mantiene solamente los datos
ya publicados y no promete cartera BDP disponible.

## Revisión previa a fusión (2026-10-07)

16 pruebas sintéticas aprobadas: CSV/ZIP, 14 familias, múltiples lotes,
texto con acentos y saltos de línea, cuarentena, fuentes duplicadas, límites,
corridas incompletas y alteración de particiones. Las particiones tienen SHA256;
el auditor comprueba además tipos, metadatos y rango de registros por fuente.
Aprobadas localmente las auditorías de navegación, web, interfaz, automatización,
RUT, cliente DuckDB, guardia SQL, catálogo de descargas e historial de secretos.

**Alcance de fusión:** investigación y staging privado probado; no equivale a
activación del pipeline productivo SP→Actions→Vercel. No cambia tablas públicas,
no añade permisos de escritura a Actions y no contiene datos originales.
