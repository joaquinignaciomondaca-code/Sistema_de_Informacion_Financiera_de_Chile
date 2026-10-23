#!/usr/bin/env python3
"""Calcula y verifica `importe_clp` en las particiones de banca publicadas.

`bancos.balance` y `bancos.resultados` publican el importe de cada línea en pesos,
en una columna numérica que se puede sumar, y el desglose por moneda tal como lo
entrega la CMF (`importes_fuente_raw`). El importe es la suma de ese desglose:

  * en B1/B2, la suma de los cuatro componentes por moneda, que es el total de la
    cuenta según el Manual del Sistema de Información de la CMF (MB1/MB2);
  * en R1, el único importe que trae el archivo, acumulado del ejercicio.

El archivo de origen cambia de formato a mitad de la serie —hasta 2024-05 escribe
la coma decimal (`26458735676131,00`) y desde 2024-06 el entero de 15 dígitos
(`025258284006864`)— y el publicado mezcla los dos; la columna se calcula aceptando
las dos formas. El archivo no publica fracciones de peso: si alguna vez lo hiciera,
el script lo detecta y falla en vez de redondear en silencio.

    python3 bancos/scripts/normalizar_importes.py            # agrega la columna si falta
    python3 bancos/scripts/normalizar_importes.py --check    # exit 1 si falta o no cuadra
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SALIDA = ROOT / "docs" / "outputs" / "bancos" / "cmf_b1_b2_r1"
COLUMNA_IMPORTE = "importe_clp"
COLUMNA_DESGLOSE = "importes_fuente_raw"


def particiones() -> list[Path]:
    return sorted(SALIDA.glob("*/lineas.parquet"))


def componente(valor: str) -> Decimal:
    """Importe de un componente del archivo CMF: entero de 15 dígitos o con coma."""
    texto = str(valor).strip()
    try:
        return Decimal(texto.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"importe fuente ilegible: {texto!r}") from exc


def calcular(raw: list[str]) -> tuple[int, int]:
    """(importe en pesos, componentes con fracción de peso)."""
    valores = [componente(v) for v in raw]
    fraccionarios = sum(1 for v in valores if v != v.to_integral_value())
    return int(sum(valores)), fraccionarios


def completar(archivo: Path) -> tuple[bool, int, int]:
    """Agrega `importe_clp` si falta. Devuelve (cambió, filas, fraccionarios)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    tabla = pq.read_table(archivo)
    if COLUMNA_IMPORTE in tabla.column_names:
        return False, tabla.num_rows, 0

    importes, fraccionarios = [], 0
    for raw in tabla.column(COLUMNA_DESGLOSE).to_pylist():
        importe, con_fraccion = calcular(raw)
        importes.append(importe)
        fraccionarios += con_fraccion

    ancla = tabla.schema.get_field_index(COLUMNA_DESGLOSE)
    nueva = tabla.add_column(
        ancla + 1,
        pa.field(COLUMNA_IMPORTE, pa.int64(), nullable=True),
        pa.array(importes, type=pa.int64()),
    )

    temporal = archivo.with_suffix(".parquet.tmp")
    pq.write_table(nueva, temporal, compression="zstd", version="2.6")
    comprobada = pq.read_table(temporal)
    if comprobada.num_rows != tabla.num_rows or comprobada.column_names != nueva.column_names:
        temporal.unlink(missing_ok=True)
        raise RuntimeError(f"{archivo}: el Parquet temporal no conserva filas ni columnas")
    os.replace(temporal, archivo)
    return True, tabla.num_rows, fraccionarios


def inspeccionar(archivo: Path) -> tuple[int, int, int]:
    """(filas, importes que no cuadran, componentes con fracción de peso)."""
    import pyarrow.parquet as pq

    columnas = [COLUMNA_DESGLOSE, COLUMNA_IMPORTE]
    tabla = pq.read_table(archivo, columns=columnas)
    malas = 0
    fraccionarios = 0
    for raw, importe in zip(*(tabla.column(c).to_pylist() for c in columnas)):
        esperado, con_fraccion = calcular(raw)
        fraccionarios += con_fraccion
        if importe != esperado:
            malas += 1
    return tabla.num_rows, malas, fraccionarios


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="no escribe: falla si falta la columna o no cuadra")
    args = ap.parse_args()

    archivos = particiones()
    if not archivos:
        print(f"No hay particiones en {SALIDA.relative_to(ROOT)}")
        return 1

    reescritas = 0
    filas = 0
    malas = 0
    fraccionarios = 0
    for archivo in archivos:
        if args.check:
            n, incorrectas, con_fraccion = inspeccionar(archivo)
        else:
            cambio, _, _ = completar(archivo)
            reescritas += int(cambio)
            n, incorrectas, con_fraccion = inspeccionar(archivo)
        malas += incorrectas
        fraccionarios += con_fraccion
        filas += n

    resumen = {
        "particiones": len(archivos),
        "filas": filas,
        "reescritas": reescritas,
        "filas_con_importe_incorrecto": malas,
    }
    if fraccionarios:
        resumen["componentes_con_centavos"] = fraccionarios
    print(json.dumps(resumen, ensure_ascii=False, indent=1))

    if malas:
        print("BANCA: hay filas cuyo `importe_clp` no coincide con `importes_fuente_raw`")
        return 1
    if fraccionarios:
        print("BANCA: hay importes con fracciones de peso; `importe_clp` las descarta y hay que revisarlo")
        return 1
    print("BANCA: `importe_clp` cuadra con `importes_fuente_raw` en todas las particiones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
