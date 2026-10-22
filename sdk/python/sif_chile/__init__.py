"""SDK de Python del Sistema de Información Financiera de Chile.

    import sif_chile

    sif = sif_chile.connect()                  # contra el sitio publicado
    sif.tablas()                               # los 90 objetos del contrato
    sif.esquema("seguros_renta_fija")          # columnas y tipos reales
    sif.sql("SELECT count(*) FROM bancos_balance").fetchone()

Para trabajar contra una copia local del repositorio, sin tocar el código:

    sif = sif_chile.connect(base="/ruta/al/repo/docs")
    # o bien:  export SIF_CHILE_BASE=/ruta/al/repo/docs
"""
from .cliente import BASE_CANONICA, Sif, connect
from . import guardia

__version__ = "0.1.0"
__all__ = ["connect", "Sif", "guardia", "BASE_CANONICA", "__version__"]
