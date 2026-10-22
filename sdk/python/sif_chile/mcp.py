"""Servidor MCP de SIF Chile, en **modo código**: dos herramientas y nada más.

Por qué dos y no noventa: un agente que descubre 90 herramientas paga cada ficha
en contexto antes de la primera pregunta. El MCP de la CMF que revisamos en el
estudio lo midió en 88 herramientas ≈ 37.000 tokens, y por eso ofrece un modo
código con 2 y ~736. Aquí nace directamente así: `sif_buscar` descubre y
`sif_ejecutar` consulta; el catálogo de 90 objetos se busca, no se inyecta.

    pip install mcp
    sif-mcp                       # servidor por stdio, como lo arranca un cliente

En un cliente MCP (Claude Desktop, por ejemplo):

    {"mcpServers": {"sif-chile": {"command": "sif-mcp"}}}

Contra una copia local del repositorio, sin red: `SIF_CHILE_BASE=/ruta/a/docs`.

El servidor no abre nada de red por su cuenta: ejecuta `views.sql` con DuckDB y
lee los Parquet del sitio (o de la carpeta que diga `SIF_CHILE_BASE`). El guardia
de solo lectura es el mismo del SDK y, como allí, es una conveniencia y no una
frontera de seguridad.
"""
from __future__ import annotations

import sys

from . import agente

INSTRUCCIONES = (
    "Datos financieros chilenos (90 objetos, Parquet + DuckDB). Descubre con "
    "sif_buscar y consulta con sif_ejecutar usando SQL de solo lectura. Filtra "
    "por periodo (AAAA-MM) y usa max(periodo) para el último dato: no lo "
    "supongas. El RUT va sin dígito verificador en `rut`. Si una consulta falla, "
    "vuelve a sif_buscar antes de reintentar: no inventes tablas ni columnas."
)


def _servidor_nuevo():
    """Crea el servidor con el SDK instalado.

    `mcp` 2.x renombró `FastMCP` a `MCPServer`; se admiten las dos versiones para
    no obligar a nadie a cambiar de SDK por un servidor de dos herramientas.
    """
    try:  # mcp >= 2
        from mcp.server.mcpserver import MCPServer as Servidor
    except ImportError:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Servidor
    return Servidor(name="sif-chile", instructions=INSTRUCCIONES)


def crear_servidor():
    """Devuelve el servidor MCP con las dos herramientas registradas."""
    servidor = _servidor_nuevo()

    @servidor.tool()
    def sif_buscar(texto: str, sector: str | None = None, limite: int = 5) -> str:
        """Busca tablas del catálogo y devuelve id, filas, corte, clave y columnas."""
        return agente.buscar(texto, sector=sector, limite=limite)

    @servidor.tool()
    def sif_ejecutar(sql: str, limite: int = 50) -> str:
        """Ejecuta SQL de solo lectura sobre las 90 tablas y devuelve columnas y filas."""
        return agente.ejecutar(sql, limite=limite)

    return servidor


def main() -> int:
    try:
        servidor = crear_servidor()
    except ImportError:
        print("Falta el SDK de MCP. Instálalo con: pip install mcp",
              file=sys.stderr)
        return 2
    servidor.run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
