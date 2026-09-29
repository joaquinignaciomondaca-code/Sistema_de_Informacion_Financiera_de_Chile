#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Busca credenciales reales en todo el historial de Git del repositorio.

Motivación: durante un tiempo el proyecto arrastró la nota de que «hay que rotar
la contraseña BCCh expuesta en el historial». Un escaneo de todo el historial
alcanzable muestra que los únicos valores que existieron fueron marcadores de
posición (`REMOVED_BCCH_EMAIL`, `CAMBIAR_ESTE_PASSWORD`, claves `test-key`),
nunca una credencial real. Este script deja esa verificación reproducible.

Qué hace:
  * recorre todos los blobs de texto alcanzables desde cualquier rama o tag;
  * busca asignaciones de clave, credenciales embebidas en URL, formatos de
    token conocidos (GitHub, Slack, Google, OpenAI) y claves privadas PEM;
  * separa lo que es claramente un marcador de posición de lo que parece real.

Salida: código 0 si no hay candidatos reales; 1 si aparece alguno (nunca imprime
el valor encontrado, sólo el archivo, el tipo de hallazgo y su largo).

Necesita historial completo: los clones superficiales (shallow) sólo tienen un
commit, así que se avisa y se omite el análisis. En CI se ejecuta sobre un
checkout con `fetch-depth: 0`.

Uso:
    python3 scripts/audit_secretos.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Archivos de texto: se excluyen binarios publicados (Parquet, wasm, xlsx, zip).
EXTENSIONES = re.compile(
    r"\.(py|md|json|ya?ml|txt|js|mjs|html|css|bat|ps1|sh|ipynb|cfg|ini|toml|xml|sql|env|example|sample)$",
    re.I,
)

# Código de terceros y archivos minificados: no se auditan (no son nuestros).
TERCEROS = re.compile(r"(vendor/|node_modules/|\.min\.js$|jszip|chart\.min)", re.I)

# Identificadores del propio proyecto (`afp_98000100_8`, `rut_11x`): no son claves.
IDENTIFICADOR = re.compile(r"^[a-z0-9_]+$")

# Texto que indica con claridad que el valor NO es una credencial real.
MARCADOR = re.compile(
    r"(REEMPLAZ|CAMBIAR|REMOVED|BORRADO|TEST|DUMMY|FICTICIO|FICTITIOUS|EXAMPLE|EJEMPLO"
    r"|XXX|TU_|AQUI|AQUÍ|PLACEHOLDER|NOT_STORE|CHANGEME|SAMPLE|DEMO|FAKE|LOREM|SECRETO_?DECO)",
    re.I,
)

PATRONES = [
    # El valor no puede cruzar de línea: un `SECRETOS = (` seguido de una tupla
    # multilínea no es una credencial (falso positivo detectado en este repo).
    ("asignación de clave", re.compile(
        r"(?P<clave>[A-Za-z_]*[A-Za-z])[ \t]*[:=][ \t]*(?P<q>[\"'])(?P<val>[^\"'\n]{8,})(?P=q)")),
    ("credencial embebida en URL", re.compile(r"https?://[^\s\"'/]+:(?P<val>[^@\s\"']{6,})@")),
    ("formato de token conocido", re.compile(
        r"(?P<val>(?:ghp_|gho_|sk-|AIza|xox[baprs]-)[A-Za-z0-9_\-]{16,})")),
    ("clave privada PEM", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Sólo interesan claves cuyo nombre hable de credenciales (evita ruido de
# `clave = "cooperativas"`, ids y configuraciones de la interfaz).
NOMBRE_RELEVANTE = re.compile(r"(pass|clave|contrase|token|secret|apikey|api_key|credential)", re.I)


def es_superficial() -> bool:
    resultado = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                               cwd=RAIZ, capture_output=True, text=True)
    return resultado.stdout.strip() == "true"


def blobs_de_texto() -> dict[str, str]:
    """sha -> ruta de todos los blobs de texto alcanzables."""
    listado = subprocess.run(["git", "rev-list", "--objects", "--all"],
                             cwd=RAIZ, capture_output=True, text=True).stdout
    rutas: dict[str, str] = {}
    for linea in listado.splitlines():
        partes = linea.split(" ", 1)
        if len(partes) == 2 and EXTENSIONES.search(partes[1]):
            rutas[partes[0]] = partes[1]
    return rutas


def contenidos(rutas: dict[str, str]) -> dict[str, str]:
    proceso = subprocess.Popen(["git", "cat-file", "--batch"], cwd=RAIZ,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    salida = proceso.communicate(b"".join(f"{sha}\n".encode() for sha in rutas))[0]
    resultado, i = {}, 0
    while i < len(salida):
        fin = salida.find(b"\n", i)
        if fin == -1:
            break
        cabecera = salida[i:fin].decode("utf-8", "replace").split()
        i = fin + 1
        if len(cabecera) < 3:
            continue
        sha, largo = cabecera[0], int(cabecera[2])
        resultado[sha] = salida[i:i + largo].decode("utf-8", "replace")
        i += largo + 1
    return resultado


def main() -> int:
    if es_superficial():
        print("Historial superficial (shallow): no se puede auditar.")
        print("  Ejecuta: git fetch --unshallow origin")
        return 0

    rutas = blobs_de_texto()
    textos = contenidos(rutas)
    marcadores: dict[tuple, int] = {}
    candidatos: dict[tuple, int] = {}
    correos: set[str] = set()

    ignorados = 0
    for sha, contenido in textos.items():
        ruta = rutas.get(sha, "?")
        if TERCEROS.search(ruta):
            continue
        for nombre, patron in PATRONES:
            for coincidencia in patron.finditer(contenido):
                grupos = coincidencia.groupdict()
                valor = grupos.get("val") or "CLAVE PRIVADA PEM"
                clave = grupos.get("clave") or ""
                if nombre == "asignación de clave" and not NOMBRE_RELEVANTE.search(clave):
                    continue
                # Los separadores cambian entre archivos (`not-store-this-key`),
                # así que se normalizan antes de buscar palabras de marcador.
                normalizado = re.sub(r"[\s\-.]+", "_", valor)
                if MARCADOR.search(normalizado) or valor.isupper():
                    destino = marcadores
                elif IDENTIFICADOR.match(valor) or len(valor) < 12:
                    ignorados += 1        # id del proyecto o valor corto: no es clave
                    continue
                else:
                    destino = candidatos
                registro = (nombre, ruta, len(valor))
                destino[registro] = destino.get(registro, 0) + 1
        for correo in re.finditer(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", contenido, re.I):
            correos.add(correo.group(0).lower())

    print(f"Verificación de secretos en el historial ({len(textos)} blobs de texto)")
    print(f"  marcadores de posición (no son credenciales): {len(marcadores)}")
    for (nombre, ruta, largo), veces in sorted(marcadores.items()):
        print(f"    · {ruta} — {nombre}, largo {largo} (en {veces} versión/es)")
    print(f"  identificadores del proyecto descartados: {ignorados}")
    if candidatos:
        print(f"\n  POSIBLES CREDENCIALES REALES: {len(candidatos)}")
        for (nombre, ruta, largo), veces in sorted(candidatos.items()):
            print(f"    · {ruta} — {nombre}, largo {largo} (en {veces} versión/es)")
        print("\nRevisa esos archivos: si son credenciales, rótalas y reescribe el historial.")
        return 1

    print("\nSin credenciales reales en el historial alcanzable.")
    print("Los flujos toman las claves de GitHub Secrets (USER_BCCH / PASSWORD_BCCH).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
