#!/usr/bin/env python3
"""Mide la cardinalidad real de cada unión del mapa relacional (punto 10).

Lee las uniones de docs/js/erd_graph.js (ERD_LINKS) y las tablas (ERD_TABLES con su archivo),
cuenta cuántas filas tiene cada lado por clave y escribe docs/outputs/cardinalidad_relaciones.json.
El mapa usa ese archivo para marcar las uniones que no son uno a uno.

Clasificación (el lado «from» es el de la izquierda del mapa):
  1:1  la clave no se repite en ninguno de los dos lados
  1:N  se repite en el lado «to» (un registro del padre, varios hijos)
  N:1  se repite en el lado «from»
  N:M  se repite en ambos lados

Las claves que el mapa describe en texto libre y no a nivel de columna se marcan como
«no medido», no se adivinan.

Uso:
  python scripts/medir_cardinalidad_relaciones.py
"""
from __future__ import annotations

import datetime
import glob
import json
import os
import re
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
ERD = DOCS / "js" / "erd_graph.js"
SALIDA = DOCS / "outputs" / "cardinalidad_relaciones.json"

# Clave de texto del mapa → columnas (lado from, lado to). Solo las que son columnas reales.
# Las demás (texto libre como «rut_administradora (gestión fiduciaria LUF)») no se miden.
CLAVES = {
    "run_fondo": (["run_fondo"], ["run_fondo"]),
    "rut": (["rut"], ["rut"]),
    "rut = rut_agf": (["rut"], ["rut_agf"]),
    "sector, rut_aseguradora": (["sector", "rut_aseguradora"], ["sector", "rut_aseguradora"]),
    "codigo_institucion (código fuente CMF)": (["codigo_institucion"], ["codigo_institucion"]),
    "fecha": (["fecha"], ["fecha"]),
    "fecha (bono pesos − bono UF)": (["fecha"], ["fecha"]),
    "periodo": (["periodo"], ["periodo"]),
    "periodo (inflación efectiva vs esperada)": (["periodo"], ["periodo"]),
    "periodo (TPM efectiva vs esperada)": (["periodo"], ["periodo"]),
    "rut = rut_administradora (cuerpo, sin dígito verificador)": (["rut"], ["rut_administradora"]),
    "rut_administradora (administración fiduciaria)": (["rut"], ["rut_administradora"]),
}


def rutas_de_manifest(manifest: Path) -> list[Path]:
    """Archivos .parquet que lista un manifest (o, si no hay, todos los de la carpeta)."""
    base = manifest.parent
    datos = json.loads(manifest.read_text(encoding="utf-8"))
    archivos: list[str] = []

    def recorrer(o):
        if isinstance(o, dict):
            for v in o.values():
                if isinstance(v, str) and v.endswith(".parquet"):
                    archivos.append(v)
                else:
                    recorrer(v)
        elif isinstance(o, list):
            for x in o:
                recorrer(x)

    recorrer(datos)
    rutas = [base / a for a in archivos if (base / a).exists()]
    return rutas or sorted(Path(p) for p in glob.glob(str(base / "**" / "*.parquet"), recursive=True))


def cargar(ruta_tabla: str, columnas: list[str]) -> pa.Table:
    """Lee solo las columnas de la clave (como texto), de un parquet o de todos los de un manifest."""
    ruta = DOCS / ruta_tabla
    archivos = [ruta] if ruta.suffix == ".parquet" else rutas_de_manifest(ruta)
    partes = []
    for a in archivos:
        if not set(columnas).issubset(pq.read_schema(a).names):
            raise KeyError(f"{a.name} no tiene {columnas}")
        t = pq.read_table(a, columns=columnas)
        partes.append(t.cast(pa.schema([(c, pa.string()) for c in columnas])))
    return pa.concat_tables(partes)


def clasificar(tf: pa.Table, tt: pa.Table, cf: list[str], ct: list[str]) -> dict:
    """Mide las claves y devuelve la clasificación con los números que la justifican.

    Trabaja con claves distintas (group_by), no con copias de las filas, para que las
    tablas grandes (más de dos millones de filas) quepan en memoria.
    """
    filas_f, filas_t = tf.num_rows, tt.num_rows
    claves_f = tf.group_by(cf).aggregate([])
    claves_t = tt.group_by(ct).aggregate([])
    n_f, n_t = claves_f.num_rows, claves_t.num_rows
    renombradas = claves_t.rename_columns([f"__k{i}" for i in range(len(ct))])
    coinciden = claves_f.join(renombradas, keys=cf, right_keys=[f"__k{i}" for i in range(len(ct))],
                              join_type="inner").num_rows
    from_unico = n_f == filas_f
    to_unico = n_t == filas_t
    if to_unico and from_unico:
        cardinalidad = "1:1"
    elif from_unico:
        cardinalidad = "1:N"
    elif to_unico:
        cardinalidad = "N:1"
    else:
        cardinalidad = "N:M"
    coincidencia = coinciden / n_t if n_t else 0.0
    if coinciden == 0:
        cardinalidad = "sin coincidencias"
    return {
        "cardinalidad": cardinalidad,
        "filas_from": filas_f,
        "filas_to": filas_t,
        "claves_distintas_from": n_f,
        "claves_distintas_to": n_t,
        "filas_to_sobrantes_por_clave_repetida": filas_t - n_t,
        "coincidencia_claves_to_en_from": round(coincidencia, 4),
    }


def tabla_de_erd() -> dict[str, str]:
    texto = ERD.read_text(encoding="utf-8")
    tablas = {}
    for m in re.finditer(r'id: "([^"]+)",\s*name: "[^"]*",[\s\S]*?file: "([^"]*)"', texto):
        tablas[m.group(1)] = m.group(2)
    return tablas


def uniones_de_erd() -> list[dict]:
    texto = ERD.read_text(encoding="utf-8")
    bloque = re.search(r"const ERD_LINKS = \[([\s\S]*?)\n\];", texto)
    if not bloque:
        raise SystemExit("No se encontró ERD_LINKS en erd_graph.js")
    return [
        {"from": m.group(1), "to": m.group(2), "key": m.group(3)}
        for m in re.finditer(r'\{ from: "([^"]+)", to: "([^"]+)", key: "([^"]+)" \}', bloque.group(1))
    ]


def main() -> int:
    tablas = tabla_de_erd()
    resultados = []
    for u in uniones_de_erd():
        base = {"from": u["from"], "to": u["to"], "key": u["key"]}
        if u["key"] not in CLAVES:
            resultados.append({**base, "cardinalidad": "no medido",
                               "motivo": "la clave está descrita en texto y no a nivel de columna"})
            continue
        if u["from"] not in tablas or u["to"] not in tablas:
            resultados.append({**base, "cardinalidad": "no medido", "motivo": "tabla sin archivo en el mapa"})
            continue
        cols_from, cols_to = CLAVES[u["key"]]
        try:
            df_from = cargar(tablas[u["from"]], cols_from)
            df_to = cargar(tablas[u["to"]], cols_to)
            medida = clasificar(df_from, df_to, cols_from, cols_to)
            resultados.append({**base, **medida, "columnas": {"from": cols_from, "to": cols_to}})
        except (KeyError, FileNotFoundError, OSError) as e:
            resultados.append({**base, "cardinalidad": "no medido", "motivo": str(e)[:200]})
        print(f"{u['from']} → {u['to']}: {resultados[-1]['cardinalidad']}", file=sys.stderr)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({"generado": datetime.date.today().isoformat(),
                                  "uniones": resultados}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("→", SALIDA.relative_to(RAIZ), f"({len(resultados)} uniones)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
