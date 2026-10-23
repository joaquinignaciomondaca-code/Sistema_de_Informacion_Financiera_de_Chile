#!/usr/bin/env python3
"""Agrega `importe_clp` y `formato_monto_fuente` a las particiones de banca publicadas.

Motivo: `bancos.balance` y `bancos.resultados` sólo publicaban los arreglos del
extractor (`importes_fuente_raw`, `importes_fuente_decimal`). En el Visor eso se
lee como `001345990724750` —el código del archivo CMF con ceros a la izquierda—
y no hay ninguna columna numérica que se pueda sumar. La ficha de R1 decía «sin
sumar importes» porque, literalmente, no había qué sumar.

Las dos columnas nuevas:

  * `importe_clp` (`BIGINT`, pesos): el importe de R1 —acumulado del ejercicio—
    o, en B1/B2, la suma de los cuatro componentes por moneda, que es el total de
    la cuenta según el Manual del Sistema de Información de la CMF (MB1/MB2).
  * `formato_monto_fuente`: `decimal_coma` hasta 2024-05 (`26458735676131,00`) y
    `entero_15` desde 2024-06 (`025258284006864`). El archivo fuente cambió de
    formato a mitad de la serie y el publicado mezcla los dos.

El cálculo no necesita la CMF: `importes_fuente_decimal` ya trae cada cifra
exacta. Es idempotente, escribe en temporal, verifica filas y columnas antes de
reemplazar y conserva el orden de las columnas (las nuevas quedan junto a los
importes de los que se derivan).

    python3 bancos/scripts/normalizar_importes.py            # agrega las columnas
    python3 bancos/scripts/normalizar_importes.py --check    # exit 1 si falta alguna
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SALIDA = ROOT / "docs" / "outputs" / "bancos" / "cmf_b1_b2_r1"
COLUMNA_IMPORTE = "importe_clp"
COLUMNA_FORMATO = "formato_monto_fuente"
# Se insertan justo después de `importes_fuente_decimal`, que es su origen.
ANCLA = "importes_fuente_decimal"


def particiones() -> list[Path]:
    return sorted(SALIDA.glob("*/lineas.parquet"))


def calcular(exactos: list[str], raw: list[str]) -> tuple[int, str]:
    total = sum(Decimal(valor) for valor in exactos)
    return int(total), "decimal_coma" if any("," in v for v in raw) else "entero_15"


def completar(archivo: Path) -> tuple[bool, int, int]:
    """Devuelve (cambió, filas, filas con centavos descartados)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    tabla = pq.read_table(archivo)
    if COLUMNA_IMPORTE in tabla.column_names and COLUMNA_FORMATO in tabla.column_names:
        return False, tabla.num_rows, 0

    importes, formatos, con_centavos = [], [], 0
    for exactos, raw in zip(tabla.column("importes_fuente_decimal").to_pylist(),
                            tabla.column("importes_fuente_raw").to_pylist()):
        importe, formato = calcular(exactos, raw)
        # El archivo fuente no publica fracciones de peso; si alguna vez lo hace,
        # `int(total)` las descartaría en silencio y hay que enterarse.
        if any(Decimal(v) != Decimal(v).to_integral_value() for v in exactos):
            con_centavos += 1
        importes.append(importe)
        formatos.append(formato)

    ancla = tabla.schema.get_field_index(ANCLA)
    nueva = tabla
    nueva = nueva.add_column(ancla + 1, pa.field(COLUMNA_IMPORTE, pa.int64(), nullable=True),
                             pa.array(importes, type=pa.int64()))
    nueva = nueva.add_column(ancla + 2, pa.field(COLUMNA_FORMATO, pa.string(), nullable=True),
                             pa.array(formatos, type=pa.string()))

    temporal = archivo.with_suffix(".parquet.tmp")
    pq.write_table(nueva, temporal, compression="zstd", version="2.6")
    comprobada = pq.read_table(temporal)
    if comprobada.num_rows != tabla.num_rows or comprobada.column_names != nueva.column_names:
        temporal.unlink(missing_ok=True)
        raise RuntimeError(f"{archivo}: el Parquet temporal no conserva filas ni columnas")
    os.replace(temporal, archivo)
    return True, tabla.num_rows, con_centavos


def inspeccionar(archivo: Path) -> tuple[int, int]:
    """(filas, filas con un importe que no cuadra con los importes exactos)."""
    import pyarrow.parquet as pq

    columnas = [ANCLA, "importes_fuente_raw", COLUMNA_IMPORTE, COLUMNA_FORMATO]
    tabla = pq.read_table(archivo, columns=columnas)
    malas = 0
    for exactos, raw, importe, formato in zip(*(tabla.column(c).to_pylist() for c in columnas)):
        esperado, esperado_formato = calcular(exactos, raw)
        if importe != esperado or formato != esperado_formato:
            malas += 1
    return tabla.num_rows, malas


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
    centavos = 0
    for archivo in archivos:
        if args.check:
            n, incorrectas = inspeccionar(archivo)
            malas += incorrectas
        else:
            cambio, n, descartados = completar(archivo)
            reescritas += int(cambio)
            centavos += descartados
            n, incorrectas = inspeccionar(archivo)
            malas += incorrectas
        filas += n

    resumen = {"particiones": len(archivos), "filas": filas,
               "reescritas": reescritas, "filas_con_importe_incorrecto": malas}
    if centavos:
        resumen["filas_con_centavos"] = centavos
    print(json.dumps(resumen, ensure_ascii=False, indent=1))

    if malas:
        print("BANCA: hay filas cuyo `importe_clp` no coincide con `importes_fuente_decimal`")
        return 1
    if centavos:
        print("BANCA: hay importes con fracciones de peso; `importe_clp` las descarta y hay que revisarlo")
        return 1
    print("BANCA: `importe_clp` y `formato_monto_fuente` cuadran en todas las particiones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
