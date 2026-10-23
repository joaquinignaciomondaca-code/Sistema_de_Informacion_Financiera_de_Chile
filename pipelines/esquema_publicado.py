"""Qué columnas de cada conjunto se publican.

La extracción calcula columnas que sirven para **verificar** el dato —la huella del
ZIP, la URL del XLSX de cotejo, el desglose decimal exacto, la ocurrencia de una
cuenta repetida, el formato del archivo de origen— pero que no aportan nada al leer
el dato financiero y engordan el archivo que descarga una persona. Este módulo fija
el recorte en un solo lugar:

  * los publicadores escriben sólo lo declarado acá (`proyectar`);
  * `scripts/verificar_columnas_publicadas.py` falla si un Parquet publicado trae
    una columna fuera de la lista.

La procedencia no se pierde: cada partición la declara una vez en su manifiesto
(`manifest.json`), con la URL y el SHA-256 del ZIP y del XLSX de cotejo, en lugar de
repetirlos en cada una de las filas.
"""
from __future__ import annotations


# Orden en que se escriben las columnas: primero lo que describe el dato financiero.
COLUMNAS_PUBLICADAS: dict[str, list[str]] = {
    # Banca (CMF B1/B2/R1). Fuera quedan: `id` (clave sintética derivable de periodo,
    # institución, modelo y cuenta), `ocurrencia_codigo_cuenta` (0 en todas las filas),
    # `unidad_monto` (pesos_clp), `tipo_estado` (constante en cada tabla), `fecha_corte`
    # (se deriva del periodo), `rubro`/`linea`/`item` (se derivan de `codigo_cuenta`),
    # `nombre_institucion_fuente` (duplica `razon_social`), `importes_fuente_decimal`
    # (mismo dato que `importes_fuente_raw`), `formato_monto_fuente` y `archivo_fuente`
    # (metadatos del archivo de origen) y las cuatro columnas de procedencia.
    # `numero_fila_fuente` se conserva: es la traza a la línea del TXT oficial.
    "bancos_cmf_lineas": [
        "periodo",
        "codigo_institucion",
        "rut",
        "razon_social",
        "codigo_cuenta",
        "glosa_cuenta",
        "tipo_linea",
        "importe_clp",
        "importes_fuente_raw",
        "familia_archivo_fuente",
        "modelo_cmf",
        "nivel_consolidacion",
        "numero_fila_fuente",
    ],
}


def columnas_publicadas(conjunto: str) -> list[str]:
    """Columnas que se publican del conjunto; error si no está declarado."""
    try:
        return COLUMNAS_PUBLICADAS[conjunto]
    except KeyError as exc:  # pragma: no cover - error de programación
        raise KeyError(
            f"El conjunto {conjunto!r} no declara columnas publicadas en "
            "pipelines/esquema_publicado.py"
        ) from exc


def proyectar(filas: list[dict], conjunto: str) -> list[dict]:
    """Deja sólo las columnas publicadas, en su orden editorial.

    Falla si una columna declarada no viene en la fila: un recorte silencioso
    publicaría nulos donde debería haber un dato.
    """
    columnas = columnas_publicadas(conjunto)
    if not filas:
        return []
    faltantes = [c for c in columnas if c not in filas[0]]
    if faltantes:
        raise KeyError(
            f"{conjunto}: la fila no trae columnas declaradas como publicadas: "
            + ", ".join(faltantes)
        )
    return [{columna: fila[columna] for columna in columnas} for fila in filas]
