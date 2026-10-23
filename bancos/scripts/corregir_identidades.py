#!/usr/bin/env python3
"""Corrige los RUT del maestro de bancos que la CMF no reconoce.

El cotejo de `validar_identidades.py` encontró 9 filas cuyo RUT no aparece en el
registro BANCO, ni entre los vigentes ni entre los no vigentes. Los que estaban
mal siguen un patrón que no es de la CMF (`59048000-2`, `59060000-8`,
`59070000-2`, `59015000-2`, `97058000-K`…) con el dígito verificador calculado;
el registro oficial usa números irregulares.

Cada corrección lleva el RUT y el nombre con que la CMF publica hoy esa entidad,
leídos de `docs/outputs/bancos/registro_cmf_banco.json`. El nombre del maestro no
se toca: es el que identifica la entidad en los archivos históricos (el caso
extremo es The Royal Bank of Scotland (Chile), que la CMF lista como «BANCO
SUDAMERICANO (ANTES THE ROYAL BANK OF SCOTLAND (CHILE))» con otro RUT).

Reescribe `bancos_maestro.json` y su Parquet conservando el esquema publicado.
Idempotente.

    python3 bancos/scripts/corregir_identidades.py            # aplica
    python3 bancos/scripts/corregir_identidades.py --check    # exit 1 si falta alguna
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BANCOS = ROOT / "docs" / "outputs" / "bancos"
MAESTRO = BANCOS / "bancos_maestro.json"
PARQUET = BANCOS / "bancos_maestro.parquet"

# codigo_institucion -> (rut_cuerpo, dv, nombre en el registro CMF del 2026-10-23)
CORRECCIONES = {
    "017": ("97003000", "K", "BANCO DO BRASIL S.A."),
    "043": ("59002030", "3", "BANCO DE LA NACION ARGENTINA"),
    "045": ("59002220", "9", "THE BANK OF TOKYO-MITSUBISHI UFJ, LTD"),
    "046": ("97919000", "K", "BANCO SUDAMERICANO (ANTES THE ROYAL BANK OF SCOTLAND (CHILE))"),
    "052": ("96929050", "2", "DEUTSCHE BANK CHILE"),
    "054": ("97949000", "3", "RABOBANK CHILE (EX HNS BANCO)"),
    "056": ("97952000", "K", "BANCO PENTA"),
    "057": ("99565970", "0", "BANCO PARIS"),
    "058": ("59141000", "8", "DNB NOR BANK ASA"),
}


def con_dv(cuerpo: str, dv: str) -> str:
    # Sin puntos: el maestro publica `rut` (cuerpo) y `rut_dv` (RUT completo) en
    # el mismo formato en sus 41 filas, para que se puedan concatenar y comparar.
    return f"{cuerpo}-{dv}"


def escribir_parquet(filas: list[dict]) -> None:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    esquema = pq.read_schema(PARQUET)
    df = pd.DataFrame(filas).reindex(columns=esquema.names)
    for campo in esquema:
        if pa.types.is_integer(campo.type):
            df[campo.name] = pd.to_numeric(df[campo.name], errors="coerce").astype("Int64")
    tabla = pa.Table.from_pandas(df, schema=esquema.remove_metadata(), preserve_index=False)
    temporal = PARQUET.with_suffix(".parquet.tmp")
    pq.write_table(tabla, temporal, compression="zstd", version="2.6")
    comprobada = pq.read_table(temporal)
    if comprobada.num_rows != len(filas) or comprobada.column_names != esquema.names:
        temporal.unlink(missing_ok=True)
        raise RuntimeError("El Parquet temporal no conserva filas ni columnas")
    temporal.replace(PARQUET)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="no escribe: falla si queda una corrección pendiente")
    args = ap.parse_args()

    filas = json.loads(MAESTRO.read_text(encoding="utf-8"))
    por_codigo = {str(f["codigo_institucion"]): f for f in filas}
    # El formato del RUT es único en todo el maestro: sin puntos y con `rut_dv`
    # igual a `rut` más el dígito verificador. Una fila con puntos rompe las
    # comparaciones y la concatenación que usan los chips del explorador.
    formato = []
    for fila in filas:
        rut, completo = str(fila.get("rut") or ""), str(fila.get("rut_dv") or "")
        if "." in rut or "." in completo or (completo and not completo.startswith(rut + "-")):
            formato.append(f"{fila.get('codigo_institucion')}: {completo}")
            if rut and completo:
                dv = completo.rsplit("-", 1)[-1]
                esperado = {"rut": rut.replace(".", ""), "rut_dv": con_dv(rut.replace(".", ""), dv)}
                if not args.check:
                    fila.update(esperado)

    pendientes, aplicadas = [], []
    for codigo, (cuerpo, dv, nombre_cmf) in CORRECCIONES.items():
        fila = por_codigo.get(codigo)
        if fila is None:
            pendientes.append(f"{codigo}: no está en el maestro")
            continue
        esperado = {"rut": cuerpo, "rut_dv": con_dv(cuerpo, dv)}
        if all(str(fila.get(k)) == v for k, v in esperado.items()):
            continue
        pendientes.append(f"{codigo}: {fila.get('rut_dv')} → {esperado['rut_dv']} ({nombre_cmf})")
        fila.update(esperado)
        aplicadas.append(codigo)

    resumen = {"filas": len(filas), "correcciones": len(CORRECCIONES), "aplicadas": aplicadas,
               "rut_con_formato_inconsistente": formato}
    if args.check:
        resumen["pendientes"] = pendientes
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    if args.check:
        if pendientes or formato:
            if pendientes:
                print("BANCA: el maestro conserva RUT que la CMF no reconoce")
            if formato:
                print("BANCA: el maestro tiene RUT con formato inconsistente (puntos o sin `rut_dv`)")
            return 1
        print("BANCA: los 9 RUT corregidos siguen en su lugar")
        return 0

    MAESTRO.write_text(json.dumps(filas, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    escribir_parquet(filas)
    print(f"Maestro y Parquet actualizados ({len(aplicadas)} fila(s) corregidas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
