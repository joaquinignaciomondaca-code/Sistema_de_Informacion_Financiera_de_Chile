#!/usr/bin/env python3
"""Genera el índice de `docs/notas/`, la puerta de entrada a las decisiones.

Hay más de sesenta notas —auditorías, decisiones de publicación, mediciones,
correcciones— y hasta ahora no había forma de encontrarlas sin abrir la carpeta.
Una decisión que no se puede encontrar no se puede citar, y este repositorio se
sostiene sobre decisiones que se pueden citar.

El índice se genera, no se escribe: cada nota aporta su título (el primer `# `),
su fecha (el `AAAA-MM-DD` del nombre del archivo) y la línea que sigue al título
si es una frase de resumen (`**Motivo:**`, `**Qué:**` o texto suelto).

    python3 scripts/build_indice_notas.py            # reescribe docs/notas/README.md
    python3 scripts/build_indice_notas.py --check    # falla si está atrasado
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NOTAS = RAIZ / "docs" / "notas"
INDICE = NOTAS / "README.md"

FECHA = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def limpiar_resumen(candidata: str) -> str:
    """Deja texto plano y legible, sin anidar enlaces Markdown en el índice."""
    candidata = re.sub(r"^\*\*[^*]+\*\*\s*", "", candidata)
    candidata = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", candidata)
    candidata = re.sub(r"`([^`]*)`", r"\1", candidata)
    candidata = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), candidata)
    candidata = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)|(?<!\w)_(.+?)_(?!\w)", lambda m: m.group(1) or m.group(2), candidata)
    # Los resúmenes son una sola línea; si la nota abre énfasis y lo cierra
    # en la línea siguiente, quitar el delimitador huérfano tras el recorte.
    candidata = re.sub(r"\*{1,2}", "", candidata)
    return candidata.strip()


def titulo_y_resumen(ruta: Path) -> tuple[str, str]:
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    titulo = ""
    resumen = ""
    for linea in texto.splitlines():
        limpia = linea.strip()
        if not titulo:
            if limpia.startswith("# "):
                titulo = limpia[2:].strip()
            continue
        if not limpia or limpia.startswith("#") or limpia in {"---", "***"}:
            if resumen:
                break
            continue
        # La primera línea con contenido después del título es el resumen.
        candidata = limpiar_resumen(limpia)
        if candidata.startswith("|") or candidata.startswith(">"):
            continue
        # Una fecha sola no resume nada, y un «Estado:» pertenece a la nota, no al índice.
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}[.]?", candidata) or candidata.lower().startswith("estado:"):
            continue
        resumen = re.split(r"(?<=[.])\s", candidata)[0].strip()
        break
    if not titulo:
        titulo = ruta.stem.replace("_", " ")
    if len(resumen) > 190:
        corte = resumen[:170].rsplit(" ", 1)[0]
        resumen = corte + "…"
    return titulo, resumen


def entradas() -> list[dict]:
    filas = []
    for ruta in sorted(NOTAS.iterdir()):
        if ruta.name == "README.md" or not ruta.is_file():
            continue
        # Sólo notas. La carpeta guarda además JSON de auditorías, que son
        # evidencia de una corrida, no una nota: no tienen título ni resumen y
        # contarlos como notas inflaba el índice («63 notas» con 59 archivos).
        if ruta.suffix != ".md":
            continue
        titulo, resumen = titulo_y_resumen(ruta)
        m = FECHA.search(ruta.name)
        fecha = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
        filas.append({"archivo": ruta.name, "titulo": titulo, "resumen": resumen, "fecha": fecha})
    return filas


def bloque() -> str:
    filas = entradas()
    sin_fecha = [f for f in filas if not f["fecha"]]
    con_fecha = [f for f in filas if f["fecha"]]
    con_fecha.sort(key=lambda f: (f["fecha"], f["archivo"]), reverse=True)

    lineas = [
        "# Notas: decisiones, mediciones y auditorías",
        "",
        "<!-- Generado por scripts/build_indice_notas.py. No editar a mano:",
        "     --check falla si no coincide con las notas de la carpeta. -->",
        "",
        f"Las {len(filas)} notas de esta carpeta. Cada una registra una decisión, una",
        "medición o una corrección, con la fecha en que se hizo y el motivo. Se citan",
        "desde el código, la web y las respuestas a las revisiones externas, así que",
        "están escritas para poder verificarse: qué se afirmó, contra qué se contrastó",
        "y qué quedó abierto.",
        "",
        "Para añadir una: crea `AAAA-MM-DD_tema.md` con un `# Título` y ejecuta",
        "`python3 scripts/build_indice_notas.py`; el índice se rehace solo.",
        "",
    ]

    actual = ""
    for fila in con_fecha:
        mes = fila["fecha"][:7]
        if mes != actual:
            actual = mes
            anio, numero = mes.split("-")
            lineas += ["", f"## {MESES[int(numero) - 1]} de {anio}", ""]
        detalle = f" — {fila['resumen']}" if fila["resumen"] else ""
        lineas.append(f"- [{fila['titulo']}]({fila['archivo']}){detalle}")

    if sin_fecha:
        lineas += ["", "## Sin fecha en el nombre", ""]
        for fila in sorted(sin_fecha, key=lambda f: f["archivo"]):
            detalle = f" — {fila['resumen']}" if fila["resumen"] else ""
            lineas.append(f"- [{fila['titulo']}]({fila['archivo']}){detalle}")

    lineas.append("")
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="no escribe; falla si el índice no coincide")
    args = ap.parse_args()

    nuevo = bloque()
    actual = INDICE.read_text(encoding="utf-8") if INDICE.exists() else ""
    if args.check:
        if actual != nuevo:
            print("INDICE-NOTAS: docs/notas/README.md no coincide con las notas; "
                  "ejecuta scripts/build_indice_notas.py")
            return 1
        print(f"INDICE-NOTAS: al día ({len(entradas())} notas)")
        return 0
    if actual == nuevo:
        print(f"INDICE-NOTAS: sin cambios ({len(entradas())} notas)")
        return 0
    INDICE.write_text(nuevo, encoding="utf-8")
    print(f"INDICE-NOTAS: escrito docs/notas/README.md con {len(entradas())} notas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
