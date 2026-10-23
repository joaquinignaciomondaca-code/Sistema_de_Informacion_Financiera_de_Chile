# Contrato 1.x: retirado

Esta carpeta existió hasta el 2026-10-23. El contrato **1.0.0** describía un esquema que
ya no se publica: cada conjunto llevaba columnas de control interno —huellas, rutas y
URLs de la fuente, claves sintéticas— repetidas en cada fila.

El esquema publicado se recortó (ver `pipelines/esquema_publicado.py`) y eso, según la
propia regla de versionado del contrato, es un cambio **mayor**. El contrato vigente es:

- https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/api/v2/datapackage.json
- https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/api/v2/catalog.json

Los datos siguen en los mismos Parquet. Si consumías `/api/v1/`, compara el esquema de
cada objeto en `/api/v2/schema/{id}.json` antes de actualizar el cliente.
