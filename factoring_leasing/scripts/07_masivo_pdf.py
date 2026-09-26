#!/usr/bin/env python3
"""Masivo de factoring y leasing: abre el PDF y lee la cara y las notas.

Es la misma lectura de la prueba de diez, no el texto convertido. Si el balance
o el resultado no cierran, queda marcado. Si una nota no suma su línea, queda
sin leer. No se inventa el número. El PDF se borra al leerlo.

Si se corta, la próxima corrida salta lo ya leído con esta versión.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff import cmf_pdf
from pipelines.eeff.validate_api import validar_documento

DEST = ROOT / "factoring_leasing" / "eeff_masivo"
MAESTRO = ROOT / "docs" / "outputs" / "factoring_leasing" / "factoring_leasing_maestro.json"
SERIE = ROOT / "docs" / "outputs" / "factoring_leasing" / "factoring_leasing_balance_resumen.json"
VERSION = 2


def _modulo(nombre: str, path: Path):
    spec = importlib.util.spec_from_file_location(nombre, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sociedades(maestro: list[dict]) -> list[dict]:
    """Factoring o leasing. Automotriz puro y consumo no entran."""
    salida = []
    vistos = set()
    for row in maestro:
        if not (row.get("es_factoring") or row.get("es_leasing_financiero") or row.get("es_leasing_habitacional")):
            continue
        rut = row.get("rut") or ""
        if not rut or rut in vistos:
            continue
        vistos.add(rut)
        salida.append({"rut": rut, "razon_social": row.get("razon_social") or ""})
    return salida


def cola(sociedades_ind: list[dict], serie: list[dict]) -> list[dict]:
    """Lo más nuevo primero. Marzo 2026 entra aunque la serie no lo traiga."""
    por_rut = {row["rut"]: row for row in sociedades_ind}
    api = {}
    for row in serie:
        rut = row.get("rut") or ""
        periodo = row.get("periodo") or ""
        if rut in por_rut and periodo:
            api[(rut, periodo)] = row
    for soc in sociedades_ind:
        api.setdefault((soc["rut"], "2026-03"), None)
    documentos = []
    for (rut, periodo), fila in api.items():
        documentos.append({
            "rut": rut,
            "razon_social": por_rut[rut]["razon_social"],
            "periodo": periodo,
            "fila_api": fila,
        })
    documentos.sort(key=lambda doc: (doc["periodo"], doc["rut"]), reverse=True)
    return documentos


def debe_saltar(prev: dict | None, version: int = VERSION) -> bool:
    """Lo ya leído no se repite. Un PDF que no bajó sí se reintenta."""
    if not prev or prev.get("version") != version:
        return False
    if prev.get("error"):
        return False
    return prev.get("estado") in {"leido", "marcado"}


def _cargar_estado(path: Path) -> dict:
    if not path.exists():
        return {"version": VERSION, "documentos": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("documentos", {})
    return data


def _guardar(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporal = path.with_suffix(path.suffix + ".tmp")
    temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(path)


def _leer_uno(notas_mod, prueba_mod, doc: dict) -> dict:
    rut = doc["rut"]
    periodo = doc["periodo"]
    year, month = (int(parte) for parte in periodo.split("-"))
    meta = {
        "rut": rut,
        "razon_social": doc["razon_social"],
        "periodo": periodo,
        "tipo_eeff": "",
    }
    blob, tipo, url = b"", "", ""
    for intento in range(4):
        blob, tipo, url = cmf_pdf.descargar_pdf(rut.split("-")[0], year, month, preferir="C")
        if blob:
            break
        print(f"[masivo] {rut} {periodo} intento {intento + 1}: {cmf_pdf.ultimo_error}", flush=True)
        time.sleep(8 * (intento + 1))
    if not blob:
        return {
            "rut": rut,
            "razon_social": doc["razon_social"],
            "periodo": periodo,
            "estado": "marcado",
            "error": "sin PDF",
            "version": VERSION,
        }
    meta["tipo_eeff"] = tipo
    extraido = notas_mod._leer_pdf(blob)
    del blob
    caratula = prueba_mod._caratula(extraido, meta)
    balance = caratula["balance"]["lineas"]
    resultados = caratula["resultado"]["lineas"]
    notas = notas_mod.extraer_notas(extraido["paginas"], extraido["tablas"], balance, meta)
    del extraido
    resumen = notas_mod._resumen(notas, caratula)
    validacion = validar_documento(balance, doc.get("fila_api"))
    falla_cara = (
        resumen["cuadre_balance"] != "OK"
        or resumen["cuadre_resultados"] != "OK"
        or resumen["cuadre_detalle"] != "OK"
        or resumen["caidas_balance"]
        or resumen["caidas_resultados"]
    )
    carpeta = DEST / periodo
    carpeta.mkdir(parents=True, exist_ok=True)
    _guardar(carpeta / f"{rut}.json", {
        "rut": rut,
        "razon_social": doc["razon_social"],
        "periodo": periodo,
        "tipo_eeff": tipo,
        "url_pdf": url,
        "balance": balance,
        "resultados": resultados,
        "notas": notas["cuadre"],
        "indice": notas["indice"],
        "validacion_api": validacion,
        "resumen": resumen,
    })
    return {
        "rut": rut,
        "razon_social": doc["razon_social"],
        "periodo": periodo,
        "tipo_eeff": tipo,
        "estado": "marcado" if falla_cara or resumen["no_leida"] else "leido",
        "error": "",
        "version": VERSION,
        "cuadre_balance": resumen["cuadre_balance"],
        "cuadre_resultados": resumen["cuadre_resultados"],
        "cuadre_detalle": resumen["cuadre_detalle"],
        "caidas": len(resumen["caidas_balance"]) + len(resumen["caidas_resultados"]),
        "notas_ok": resumen["ok"],
        "notas_sin_leer": resumen["no_leida"],
        "lineas_balance": resumen["lineas_balance"],
        "lineas_resultados": resumen["lineas_resultados"],
        "api": sorted({fila["estado"] for fila in validacion}),
    }


def _publicar() -> None:
    """Deja lo ya leído en la rama de revisión, sin mover la rama de trabajo."""
    rama = os.environ.get("MASIVO_RAMA")
    if not rama:
        return
    subprocess.run(["git", "add", "-f", "factoring_leasing/eeff_masivo"], check=False)
    subprocess.run(["git", "commit", "-m", "factoring: masivo parcial"], check=False)
    subprocess.run(["git", "push", "origin", f"HEAD:{rama}"], check=False)


def correr(minutos: int = 330) -> int:
    maestro = json.loads(MAESTRO.read_text(encoding="utf-8"))
    serie = json.loads(SERIE.read_text(encoding="utf-8")) if SERIE.exists() else []
    documentos = cola(sociedades(maestro), serie)
    estado_path = DEST / "checkpoint.json"
    estado = _cargar_estado(estado_path)
    notas_mod = _modulo("notas10", ROOT / "factoring_leasing" / "scripts" / "06_notas_10_pdf.py")
    prueba_mod = _modulo("prueba10", ROOT / "factoring_leasing" / "scripts" / "04_prueba_10_pdf.py")
    limite = time.time() + minutos * 60
    leidos = saltados = 0
    print(f"[masivo] {len(documentos)} documentos. Lo ya leído no se repite.", flush=True)
    for doc in documentos:
        if time.time() > limite:
            print("[masivo] se corta por tiempo. Lo guardado queda. La próxima sigue.", flush=True)
            break
        clave = f"{doc['rut']}|{doc['periodo']}"
        if debe_saltar(estado["documentos"].get(clave)):
            saltados += 1
            continue
        print(f"[masivo] {doc['rut']} {doc['periodo']} {doc['razon_social']}", flush=True)
        try:
            fila = _leer_uno(notas_mod, prueba_mod, doc)
        except Exception as exc:
            fila = {
                "rut": doc["rut"],
                "razon_social": doc["razon_social"],
                "periodo": doc["periodo"],
                "estado": "marcado",
                "error": f"{type(exc).__name__}: {exc}",
                "version": VERSION,
            }
            print(f"[masivo] {clave} error: {fila['error']}", flush=True)
        estado["documentos"][clave] = fila
        estado["version"] = VERSION
        _guardar(estado_path, estado)
        leidos += 1
        if leidos % 5 == 0:
            _publicar()
        print(
            f"[masivo] {clave} balance={fila.get('cuadre_balance', '-')} "
            f"resultados={fila.get('cuadre_resultados', '-')} "
            f"notas={fila.get('notas_ok', 0)}/{fila.get('notas_sin_leer', 0)} "
            f"error={fila.get('error') or '-'}",
            flush=True,
        )
    filas = list(estado["documentos"].values())
    sin_pdf = sum(1 for fila in filas if fila.get("error") == "sin PDF")
    marcados = sum(1 for fila in filas if fila.get("estado") == "marcado" or fila.get("error"))
    lineas = [
        "# Masivo factoring y leasing",
        "",
        "Misma lectura que la prueba: el PDF, no el texto convertido. Lo que no cierra queda marcado.",
        "",
        f"Leídos en esta pasada: {leidos}. Saltados: {saltados}. En el checkpoint: {len(filas)}.",
        f"Marcados: {marcados}. Sin PDF: {sin_pdf}.",
        "",
    ]
    for fila in sorted(filas, key=lambda item: (item.get("periodo", ""), item.get("rut", "")), reverse=True):
        lineas.append(
            f"- {fila.get('razon_social', '')} ({fila.get('rut')} {fila.get('periodo')}): "
            f"balance={fila.get('cuadre_balance', '-')} resultados={fila.get('cuadre_resultados', '-')} "
            f"notas ok={fila.get('notas_ok', 0)} sin leer={fila.get('notas_sin_leer', 0)} "
            f"caidas={fila.get('caidas', 0)}"
            + (f" error={fila['error']}" if fila.get("error") else "")
        )
    (DEST / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas[:8]), flush=True)
    return 0 if leidos or saltados else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutos", type=int, default=330)
    args = parser.parse_args()
    raise SystemExit(correr(args.minutos))


if __name__ == "__main__":
    main()
