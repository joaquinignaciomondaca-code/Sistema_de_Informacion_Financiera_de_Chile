#!/usr/bin/env python3
"""Compuerta del servidor MCP (fase 2): presupuesto de contexto y prueba real.

Hace tres cosas, contra el servidor arrancado **como lo arranca un agente** (un
proceso aparte, por stdio, con el SDK oficial de MCP):

  2.2  Mide lo que el modelo paga por las herramientas (nombre, descripción y
       `inputSchema` tal como los devuelve el servidor) y falla si pasa de 1.000
       tokens. La referencia es 88 herramientas ≈ 37.000; aquí son 2.
  2.3  Responde la pregunta del README usando **solo** las dos herramientas:
       `sif_buscar` («dónde invierten fuera de Chile los fondos mutuos») y
       `sif_ejecutar` con la agregación. Comprueba que US, LU e IE quedan en
       cabeza, igual que el ejemplo del sitio.
       Extra: un SQL roto tiene que volver como `error` + `pista`, no como
       excepción, y un `DROP` tiene que rebotar en el guardia.

    python3 scripts/auditar_mcp.py            # informe
    python3 scripts/auditar_mcp.py --check    # exit 1 si algo falla

Requiere `pip install mcp`. Deja la evidencia en `docs/api/mcp.log`.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
SDK = RAIZ / "sdk" / "python"
LOG = DOCS / "api" / "mcp.log"

sys.path.insert(0, str(SDK))

PRESUPUESTO = 1_000
ESPERADAS = {"sif_buscar", "sif_ejecutar"}
TOP3 = {"US", "LU", "IE"}

SQL_FFMM = """
SELECT pais_emisor, count(*) AS posiciones, count(DISTINCT run_fondo) AS fondos
FROM ffmm_cartera_extranjera
WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera)
GROUP BY pais_emisor
ORDER BY posiciones DESC
"""


def texto(resultado) -> str:
    """El SDK 2.x puede devolver el texto en `content` o en `structuredContent`."""
    if getattr(resultado, "structuredContent", None):
        return json.dumps(resultado.structuredContent, ensure_ascii=False)
    partes = []
    for bloque in getattr(resultado, "content", []) or []:
        partes.append(getattr(bloque, "text", "") or "")
    return "".join(partes)


async def correr() -> list[tuple[str, bool, str]]:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    from sif_chile.agente import contar_tokens

    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    entorno["PYTHONPATH"] = str(SDK)
    entorno["SIF_CHILE_BASE"] = str(DOCS)
    parametros = StdioServerParameters(
        command=sys.executable, args=["-m", "sif_chile.mcp"], env=entorno,
    )

    checks: list[tuple[str, bool, str]] = []
    async with stdio_client(parametros) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()
            inicio = time.time()

            # --- 2.1 · las dos herramientas ---------------------------------
            herramientas = (await sesion.list_tools()).tools
            nombres = {h.name for h in herramientas}
            checks.append(("2.1 herramientas", nombres == ESPERADAS,
                           f"{len(herramientas)} herramientas: {sorted(nombres)}"))

            # --- 2.2 · presupuesto de contexto ------------------------------
            # `mcp` 2.x renombró el campo a snake_case; se aceptan las dos formas.
            esquema = json.dumps(
                [{"name": h.name, "description": h.description or "",
                  "inputSchema": getattr(h, "inputSchema", None) or getattr(h, "input_schema", None)}
                 for h in herramientas],
                ensure_ascii=False)
            tokens = contar_tokens(esquema)
            checks.append(("2.2 presupuesto", tokens <= PRESUPUESTO,
                           f"{tokens} tokens de {PRESUPUESTO} permitidos "
                           f"({len(esquema)} caracteres; 88 herramientas ≈ 37.000)"))

            # --- 2.3 · la pregunta del README, con dos herramientas ---------
            busqueda = json.loads(texto(await sesion.call_tool(
                "sif_buscar", {"texto": "dónde invierten fuera de Chile los fondos mutuos", "limite": 3})))
            ids = [o["id"] for o in busqueda.get("objetos", [])]
            checks.append(("2.3 descubrir", "ffmm_cartera_extranjera" in ids,
                           f"«{busqueda.get('consulta')}» → {ids}"))

            resultado = json.loads(texto(await sesion.call_tool(
                "sif_ejecutar", {"sql": SQL_FFMM, "limite": 5})))
            filas = resultado.get("datos") or []
            paises = [f[0] for f in filas]
            checks.append(("2.3 responder", TOP3 <= set(paises),
                           f"{resultado.get('filas')} filas; en cabeza {paises[:5]} "
                           f"(se esperaba {sorted(TOP3)})"))

            roto = json.loads(texto(await sesion.call_tool(
                "sif_ejecutar", {"sql": "SELECT nope FROM ffmm_cartera_extranjera"})))
            checks.append(("2.3 error útil", bool(roto.get("error")) and bool(roto.get("pista")),
                           f"error con pista: {roto.get('pista', '')[:60]}"))

            bloqueado = json.loads(texto(await sesion.call_tool(
                "sif_ejecutar", {"sql": "DROP VIEW ffmm_cartera_extranjera"})))
            checks.append(("2.3 solo lectura", bool(bloqueado.get("error")),
                           "el guardia rechaza DROP y responde con JSON"))

            # --- 2.4 · la ficha de un objeto sin clave ----------------------
            # La 2.0.1 publica `primaryKey: null` en 27 objetos. La herramienta
            # no puede romperse ni devolver una clave inventada: `pk` va en null.
            sin_clave = json.loads(texto(await sesion.call_tool(
                "sif_buscar", {"texto": "cartera nacional de fondos mutuos", "limite": 3})))
            ficha = next((o for o in sin_clave.get("objetos", [])
                          if o.get("id") == "ffmm_cartera_nacional"), None)
            checks.append((
                "2.4 sin clave",
                ficha is not None and ficha.get("pk") is None and "pk" in ficha,
                "ffmm_cartera_nacional llega con pk null (antes afirmaba una clave falsa)"
                if ficha else "la búsqueda no devolvió ffmm_cartera_nacional",
            ))

            duracion = time.time() - inicio
            checks.append(("2.3 llamadas", True, f"5 llamadas en {duracion:.2f} s"))
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 si algo falla")
    args = ap.parse_args()

    lineas = [f"# Servidor MCP · {datetime.now().isoformat(timespec='seconds')}", ""]
    t0 = time.time()
    try:
        checks = asyncio.run(correr())
    except ImportError as exc:
        print(f"Falta el SDK de MCP: {exc}. Instala con: pip install mcp")
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"[FALLA] no se pudo hablar con el servidor: {type(exc).__name__}: {exc}")
        return 1

    for nombre, ok, detalle in checks:
        linea = f"{'OK   ' if ok else 'FALLA'} {nombre} · {detalle}"
        print(linea)
        lineas.append(linea)

    fallos = [c for c in checks if not c[1]]
    duracion = time.time() - t0
    veredicto = ("MCP: dos herramientas, presupuesto de contexto y pregunta del README en verde"
                 if not fallos else f"MCP: {len(fallos)} comprobación(es) fallaron")
    print(f"\nDuración: {duracion:.1f} s · comprobaciones: {len(checks)} · fallos: {len(fallos)}")
    print(veredicto)
    lineas += ["", f"Duración: {duracion:.1f} s · comprobaciones: {len(checks)} · fallos: {len(fallos)}",
               veredicto]
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia: {LOG.relative_to(RAIZ)}")
    return 1 if (fallos and args.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())
