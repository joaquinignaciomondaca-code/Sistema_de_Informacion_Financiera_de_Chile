#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Escribe en el aviso de privacidad los conteos que vienen de la fuente publicada.

Por qué existe
--------------
`PRIVACIDAD.md` declara cuántas personas hay detrás de cada conjunto con datos
personales: «36 personas naturales (de **N** prestadores)» en FinTech,
«11 corredores … (de **M**)» en corredoras de bolsa, y los nombres de tasadores
de bienes raíces. Son cifras de la CMF, no del proyecto: cada alta en el Registro
de Prestadores de Servicios Financieros las deja obsoletas sin que nadie toque una
línea de código.

El 2026-11-09 el registro pasó de 267 a 268 prestadores y `web_audit` se puso en
rojo en `main` por esa fila: el aviso era correcto sobre el riesgo (quién es
persona natural) pero estaba un alta atrás. Con las cifras escritas a mano, el
único arreglo posible era el que se hacía hasta ahora —editar el número—, y el
mismo fallo vuelve con la próxima entidad.

Qué hace este script
--------------------
Reescribe **sólo los totales** en `PRIVACIDAD.md` y en su espejo
`docs/privacidad.html`, leyendo los Parquet publicados. Los conteos que expresan
el criterio de privacidad (36 personas naturales, 11 corredores, 317 nombres de
tasadores y su reparto 233/263) **no** se tocan: si cambian, la compuerta
`scripts/auditar_personas_publicadas.py` debe fallar para que alguien revise si
el riesgo cambió. Así el aviso sigue siendo la declaración que se audita, no una
copia del código, y el ruido de un alta ya no lo apaga.

Va en la cadena derivada (`scripts/cadena_contrato.py`), antes de
`build_metadatos.py`, y acepta `--check` como el resto de los generadores.

Uso:
    python3 scripts/build_privacidad_cifras.py            # escribe el aviso
    python3 scripts/build_privacidad_cifras.py --check    # falla si está atrasado
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # el job `automatizacion` de web_audit no instala duckdb: sólo prueba el texto
    import duckdb
except Exception:  # pragma: no cover
    duckdb = None

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
PRIVACIDAD = RAIZ / "PRIVACIDAD.md"
PRIVACIDAD_HTML = DOCS / "privacidad.html"


def _conectar():
    if duckdb is None:
        raise SystemExit(
            "FALLA: duckdb no está instalado (python -m pip install duckdb); "
            "sin él no se pueden leer los Parquet publicados"
        )
    return duckdb.connect()


def contar_prestadores(con) -> int:
    ruta = DOCS / "outputs" / "fintech" / "fintech_rpsf_maestro.parquet"
    return int(con.execute(f"SELECT count(*) FROM read_parquet('{ruta}')").fetchone()[0])


def contar_corredoras(con) -> int:
    ruta = DOCS / "outputs" / "corredoras_bolsa" / "corredoras_bolsa_maestro.parquet"
    return int(con.execute(f"SELECT count(*) FROM read_parquet('{ruta}')").fetchone()[0])


def sincronizar(texto: str, prestadores: int, corredoras: int, archivo: str) -> tuple[str, list[str]]:
    """Devuelve el texto con los totales al día y la lista de cambios aplicados."""
    cambios: list[str] = []

    def cambiar(patron: str, reemplazo: str, que: str) -> None:
        nonlocal texto
        nuevo, n = re.subn(patron, reemplazo, texto, count=1)
        if not n:
            print(
                f"FALLA: {archivo} no declara {que}; el texto cambió de forma y el total "
                "no se puede mantener sincronizado",
                file=sys.stderr,
            )
            raise SystemExit(1)
        if nuevo != texto:
            cambios.append(f"{archivo}: {que}")
        texto = nuevo

    cambiar(
        r"(personas naturales[^|\n<]*?de\s+)[\d.]+(\s+prestadores)",
        rf"\g<1>{prestadores}\g<2>",
        "prestadores FinTech",
    )
    cambiar(
        r"(corredores[^|\n<]*?de\s+)[\d.]+",
        rf"\g<1>{corredoras}",
        "corredoras de bolsa",
    )
    return texto, cambios


def main() -> int:
    revisar = "--check" in sys.argv
    con = _conectar()
    prestadores = contar_prestadores(con)
    corredoras = contar_corredoras(con)

    cambios: list[str] = []
    pendientes: list[tuple[Path, str]] = []
    for ruta in (PRIVACIDAD, PRIVACIDAD_HTML):
        if not ruta.exists():
            print(f"FALLA: falta el aviso {ruta.relative_to(RAIZ)}")
            return 1
        original = ruta.read_text(encoding="utf-8")
        actualizado, aplicados = sincronizar(
            original, prestadores, corredoras, str(ruta.relative_to(RAIZ))
        )
        cambios.extend(aplicados)
        if actualizado != original:
            pendientes.append((ruta, actualizado))

    if revisar:
        if pendientes:
            for ruta, _ in pendientes:
                print(f"FALLA: {ruta.relative_to(RAIZ)} declara un total que no coincide con los archivos")
            print("Ejecuta scripts/build_privacidad_cifras.py")
            return 1
        print(f"Aviso al día: {prestadores} prestadores FinTech · {corredoras} corredoras de bolsa")
        return 0

    for ruta, texto in pendientes:
        ruta.write_text(texto, encoding="utf-8")
    if cambios:
        print("Aviso actualizado: " + " · ".join(cambios))
    else:
        print("Aviso sin cambios: los totales ya coincidían con los archivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
