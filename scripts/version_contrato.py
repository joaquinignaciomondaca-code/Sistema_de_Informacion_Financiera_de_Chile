#!/usr/bin/env python3
"""La versión del contrato, declarada una sola vez.

El contrato se publica en `docs/api/{API_VERSION}/` y cada pieza que lo compone
—catálogo, esquemas por objeto, particiones, consultas, OpenAPI, resultados y
Data Package— declara la misma versión semver. Si dos piezas dijeran versiones
distintas, el contrato estaría mintiendo sobre sí mismo: el 2026-10-23 pasó
justamente eso (el Data Package decía 2.0.0 y el resto seguía en 1.0.0).

Por eso las constantes viven aquí y las importan los generadores y el auditor:

    python3 -c "import sys; sys.path.insert(0,'scripts'); import version_contrato as v; print(v.VERSION_CONTRATO, v.API_VERSION)"

Regla de versionado (D3): mayor = se rompe un cliente (quitar o renombrar un
recurso o una columna, cambiar un tipo); menor = añadir recurso, columna o campo
`sif.*`; parche = sólo datos, que es `data_release` y no toca la versión.
"""
from __future__ import annotations

# semver del contrato.
#   2.0.0 · 2026-10-23 · recorte de columnas publicadas: quitar columnas rompe clientes.
#   2.0.1 · 2026-10-23 · corrección: el descriptor deja de afirmar 13 claves primarias
#           que no eran únicas (bug de `verificar_claves.py`). No cambia ni una fila
#           ni una columna publicada; sólo se retira una promesa falsa.
#   2.1.0 · 2026-10-23 · campo nuevo `totales.con_filas` (objetos con filas), que
#           separa «tiene archivo» de «tiene datos»: 86 y 85 dejan de confundirse.
VERSION_CONTRATO = "2.1.0"

# Carpeta y `api_version` de todas las piezas. Cambia sólo con una versión mayor.
API_VERSION = "v2"
