"""Servidor MCP de SIF Chile, en **modo código**: dos herramientas y nada más.

Por qué dos y no noventa: un agente que descubre 90 herramientas paga cada ficha
en contexto antes de la primera pregunta. El MCP de la CMF que revisamos en el
estudio lo midió en 88 herramientas ≈ 37.000 tokens, y por eso ofrece un modo
código con 2 y ~736. Aquí nace directamente así: `sif_buscar` descubre y
`sif_ejecutar` consulta; el catálogo de 90 objetos se busca, no se inyecta.

    pip install mcp
    sif-mcp                       # servidor por stdio, como lo arranca un cliente
    sif-mcp --http --port 8001    # Streamable HTTP (opcional, para agentes remotos)

En un cliente MCP (Claude Desktop, por ejemplo):

    {"mcpServers": {"sif-chile": {"command": "sif-mcp"}}}

Contra una copia local del repositorio, sin red: `SIF_CHILE_BASE=/ruta/a/docs`.

Por stdio el servidor no abre nada de red: ejecuta `views.sql` con DuckDB y lee
los Parquet del sitio (o de la carpeta que diga `SIF_CHILE_BASE`). El guardia de
solo lectura es el mismo del SDK y, como allí, es una conveniencia y no una
frontera de seguridad. En modo HTTP se añade la protección DNS-rebinding del SDK
oficial (Host/Origin); para exponerlo fuera de loopback hay que listar los hosts
y orígenes exactos permitidos, o desactivarla explícitamente bajo un proxy TLS.
"""
from __future__ import annotations

import argparse
import os
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


def _lista(valor: str | None) -> list[str]:
    return [v.strip() for v in (valor or "").split(",") if v.strip()]


def crear_app_http(servidor, host: str = "127.0.0.1", port: int = 8001,
                   allowed_hosts: list[str] | None = None,
                   allowed_origins: list[str] | None = None,
                   dns_rebinding: bool = True):
    """App Starlette de Streamable HTTP con la seguridad de transporte del SDK.

    `allowed_hosts`/`allowed_origins` aceptan valores exactos o comodín de puerto
    (`host:*`), no comodines de hostname. Para un preview iframe hay que listar el
    host exacto, o poner `dns_rebinding=False` detrás de un proxy que ya valide.
    """
    try:
        from mcp.server.transport_security import TransportSecuritySettings
    except ImportError as exc:  # mcp 1.x no trae este módulo
        raise RuntimeError("El modo HTTP requiere mcp>=2 (pip install -U mcp).") from exc
    hosts = allowed_hosts if allowed_hosts is not None else _lista(os.environ.get("SIF_MCP_ALLOWED_HOSTS"))
    origins = allowed_origins if allowed_origins is not None else _lista(os.environ.get("SIF_MCP_ALLOWED_ORIGINS"))
    if not hosts:
        hosts = [f"{host}:{port}", "localhost:*", "127.0.0.1:*"]
    if not origins:
        origins = [f"http://{host}:{port}", "http://localhost:*", "http://127.0.0.1:*"]
    seguridad = TransportSecuritySettings(
        enable_dns_rebinding_protection=dns_rebinding,
        allowed_hosts=hosts, allowed_origins=origins,
    )
    return servidor.streamable_http_app(transport_security=seguridad, host=host)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sif-mcp", description="Servidor MCP de SIF Chile (dos herramientas).")
    ap.add_argument("--http", action="store_true", help="Streamable HTTP en vez de stdio")
    ap.add_argument("--host", default=os.environ.get("SIF_MCP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("SIF_MCP_PORT", "8001")))
    ap.add_argument("--allowed-host", action="append", default=None,
                    help="Host permitido (exacto o host:*). Repetible. Por defecto loopback.")
    ap.add_argument("--allowed-origin", action="append", default=None,
                    help="Origin permitido (exacto o http://host:*). Repetible.")
    ap.add_argument("--no-dns-rebinding-protection", action="store_true",
                    help="Desactiva la validación Host/Origin (solo detrás de un proxy TLS de confianza).")
    args = ap.parse_args(argv)
    try:
        servidor = crear_servidor()
    except ImportError:
        print("Falta el SDK de MCP. Instálalo con: pip install mcp", file=sys.stderr)
        return 2
    if not args.http:
        servidor.run("stdio")
        return 0
    try:
        import uvicorn
    except ImportError:
        print("El modo HTTP requiere uvicorn. Instálalo con: pip install uvicorn", file=sys.stderr)
        return 2
    try:
        app = crear_app_http(
            servidor, host=args.host, port=args.port,
            allowed_hosts=args.allowed_host, allowed_origins=args.allowed_origin,
            dns_rebinding=not args.no_dns_rebinding_protection,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"MCP Streamable HTTP en http://{args.host}:{args.port}/mcp", file=sys.stderr)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
