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

# semver del contrato. Sube a 2.0.0 el 2026-10-23: el recorte de columnas
# publicado en `pipelines/esquema_publicado.py` quita columnas que un cliente
# podía leer, y eso es un cambio mayor.
VERSION_CONTRATO = "2.0.0"

# Carpeta y `api_version` de todas las piezas. Cambia sólo con una versión mayor.
API_VERSION = "v2"
