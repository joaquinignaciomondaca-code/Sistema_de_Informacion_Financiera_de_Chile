---
name: sif-test-design
description: Diseña pruebas herméticas para transformaciones, extracción, contratos y UI del SIF con atención a invariantes financieros y fallos de fuentes públicas.
---

# Diseño de pruebas para el SIF

Usa esta skill al añadir una regla, reparar un bug o preparar un refactor. La prueba debe proteger un comportamiento observable/invariante, no solo ejecutar una línea del código.

## Selección de nivel

- **Unitarias:** normalizadores, parsers y cálculos deterministas; cubre entrada válida, límites y rechazo claro de datos inválidos.
- **Integración local:** pipeline, publicación, builders o SDK con fixtures pequeños, fakes y `tempfile.TemporaryDirectory`; verifica archivos, esquema y metadatos.
- **Contrato/auditoría:** usa los builders con `--check`, auditores existentes o pruebas de compatibilidad cuando un artefacto publicado o consumidor puede verse afectado.
- **DOM/UI:** ejecuta el test/auditoría Node específica si cambian eventos, contenido accesible, navegación, SQL o estado visual. Las auditorías estáticas/DOM no equivalen a una prueba visual en navegador.

## Casos relevantes (elige según la regla)

- Archivo vacío, truncado, encoding inesperado, encabezado/columna nueva o faltante, separador cambiado.
- Campos nulos o inválidos, importes con signo/separadores, valores grandes, precisión y redondeo.
- Fecha/cierre límite, hueco temporal, zona horaria, duplicado, reordenamiento o lote sin novedades.
- RUT con/sin DV y ceros iniciales, sin confundir RUT con RUN o con identidad validada.
- Diferenciar sin datos, dato no disponible y valor numérico cero.
- Cuadraturas y totales con tolerancia definida; controlar casos justo dentro/fuera de umbral.
- Error de red, timeout, respuesta no exitosa, reintento, paginación incompleta o descarga con tamaño/formato inesperado, si se toca I/O.
- Para UI/contrato: carga, vacío, error, éxito, esquema/columnas nuevas y navegación/escape de valores.

## Reglas de calidad

- Las pruebas no acceden a internet, CMF, BCCh ni servicios externos; simula respuestas y dependencias.
- No uses datos privados ni copies registros reales innecesarios. Mantén fixtures mínimos y con procedencia evidente si son públicos.
- Fija reloj/fechas y locale cuando influyan; evita expectativas sobre «hoy» o el último dato vivo.
- Comprueba tanto resultados como fallos: error entendible y ausencia de publicación parcial cuando ese sea el contrato.
- Evita snapshots enormes de Parquet/JSON y aserciones frágiles sobre detalles internos. Verifica contenido, esquema e invariantes pertinentes.
- Sigue el estilo existente, principalmente `unittest` para Python y scripts `node` para JavaScript. No añadas un runner ni dependencia solo por conveniencia sin justificarlo.

## Comandos

Adapta al módulo; no existe un comando universal de pruebas:

```bash
python -m unittest paquete.tests.test_modulo -v
python -m unittest discover -s sector/tests -v
node scripts/test_modulo.js
```

Si el cambio genera contrato, usa además el `scripts/build_*.py --check` o auditor que documente su workflow. Ejecuta comandos solo para pruebas existentes y pertinentes; informa qué no pudo correr.
