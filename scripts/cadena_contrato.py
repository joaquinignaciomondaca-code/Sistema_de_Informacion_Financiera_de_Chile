#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orden de la cadena de artefactos derivados del contrato (docs/api/README.md).

Vive en su propio módulo, sin dependencias, por dos razones:

  1. La comparten `contrato_publicado.yml` (vía `scripts/refrescar_contrato.py`) y las
     pruebas que comprueban que el flujo no se salte un eslabón. Si la lista viviera dentro
     de un generador, importarla obligaría a instalar todo lo que ese generador necesita:
     `build_macro_web` importa pandas, y el job que corre estas pruebas solo instala pyarrow.
     Un `ModuleNotFoundError` ahí se ve como un fallo del guardián y esconde el real.
  2. Una sola lista evita que dos flujos regeneren partes distintas del mismo contrato y
     publiquen una mezcla. El 2026-11-04 la cadena vieja dejó el catálogo API con 19.814.981
     filas y las descargas con 19.814.992, y `web_audit` falló en `main` sin que nadie
     hubiera tocado el código.

`build_macro_web` reexporta `CADENA` para los llamadores anteriores.
"""

from __future__ import annotations

# Orden de dependencia: cada paso lee artefactos que dejaron los anteriores.
CADENA = (
    "build_reconciliacion.py",
    "verificar_claves.py",
    "build_macro_web.py",          # el diccionario macro se genera antes de los esquemas
    "build_esquemas.py",
    "build_api.py",
    "build_contrato.py",
    "build_ficha_piloto.py",
    "build_resultados.py",
    "build_download_exports.py",   # exportaciones antes del catálogo que las enlaza
    "build_download_catalog.py",
    # Las métricas se reconcilian justo después de los catálogos que leen: es el paso que
    # sincroniza las cifras publicadas de README.md y detecta cualquier desalineación antes
    # de que el commit llegue a la rama.
    "build_metricas_publicadas.py",
    # Los totales del aviso de privacidad (prestadores FinTech, corredoras) son
    # cifras de la fuente, no del código: se escriben desde los Parquet antes de
    # que `build_metadatos` selle el HTML. Escritos a mano, un alta en el registro
    # de la CMF ponía `web_audit` en rojo sin que nadie hubiera tocado nada
    # (2026-11-09: 267 → 268 prestadores).
    "build_privacidad_cifras.py",
    "build_estado_claves.py",
    "build_landing_pages.py",
    "build_metadatos.py",
    "construir_reproducibilidad.py",
    "generar_indice_busqueda.py",
    "auditar_contrato.py",
)
