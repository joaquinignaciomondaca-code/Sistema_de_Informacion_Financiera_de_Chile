"""Prueba real del transporte Streamable HTTP del servidor MCP (mcp>=2).

Levanta uvicorn en un puerto efímero de loopback y habla con él como lo haría un
agente remoto: initialize, list_tools y call_tool. Además comprueba que la
protección DNS-rebinding rechaza un Host ajeno (421).
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import threading
import time
import unittest
from pathlib import Path

DOCS = Path(__file__).resolve().parents[3] / "docs"

try:
    import uvicorn
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from sif_chile import mcp as sif_mcp
    HAY_HTTP = True
except ImportError:  # mcp 1.x o sin uvicorn: el modo stdio sigue probado en test_agente
    HAY_HTTP = False


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@unittest.skipUnless(HAY_HTTP, "requiere mcp>=2 y uvicorn")
class MCPHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SIF_CHILE_BASE"] = str(DOCS)
        cls.port = _puerto_libre()
        servidor = sif_mcp.crear_servidor()
        app = sif_mcp.crear_app_http(
            servidor, host="127.0.0.1", port=cls.port,
            allowed_hosts=[f"127.0.0.1:{cls.port}"],
            allowed_origins=[f"http://127.0.0.1:{cls.port}"],
        )
        config = uvicorn.Config(app, host="127.0.0.1", port=cls.port, log_level="warning")
        cls.server = uvicorn.Server(config)
        cls.hilo = threading.Thread(target=cls.server.run, daemon=True)
        cls.hilo.start()
        for _ in range(100):
            if cls.server.started:
                break
            time.sleep(0.05)
        if not cls.server.started:
            raise RuntimeError("uvicorn no arrancó")

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.hilo.join(timeout=5)
        from sif_chile import agente
        agente.cerrar()
        os.environ.pop("SIF_CHILE_BASE", None)

    def test_initialize_list_tools_y_call(self):
        async def correr():
            url = f"http://127.0.0.1:{self.port}/mcp"
            async with streamable_http_client(url) as (lectura, escritura):
                async with ClientSession(lectura, escritura) as sesion:
                    await sesion.initialize()
                    herramientas = (await sesion.list_tools()).tools
                    self.assertEqual({h.name for h in herramientas}, {"sif_buscar", "sif_ejecutar"})
                    r = await sesion.call_tool("sif_ejecutar", {"sql": "SELECT 42 AS respuesta"})
                    texto = r.content[0].text if r.content else json.dumps(r.structuredContent)
                    datos = json.loads(texto)
                    self.assertEqual(datos["datos"], [[42]])
                    self.assertIn("celdas_recortadas", datos)
        asyncio.run(correr())

    def test_host_ajeno_es_421(self):
        import httpx2 as httpx
        with httpx.Client() as cliente:
            r = cliente.post(
                f"http://127.0.0.1:{self.port}/mcp",
                headers={"host": "evil.example", "content-type": "application/json",
                         "accept": "application/json, text/event-stream"},
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "t", "version": "0"}}},
            )
            self.assertEqual(r.status_code, 421)


if __name__ == "__main__":
    unittest.main()
