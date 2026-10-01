"""Audita lo publicado de FI, incluidos TODOS los contextos, no solo el actual.

Contabilidad, completitud por contexto, claves, fechas/moneda y cobertura igual
entre balance y resultados actuales. Las cifras de comparativos rechazados no
pueden estar en los Parquet. Sin red, sin escritura.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq

from fi.scripts import eeff_xml as xml

RAIZ = Path(__file__).resolve().parents[2]
CLAVES = ("periodo", "run_fondo", "contexto")


def verificar_filas(tabla, filas):
    grupos = defaultdict(list)
    errores, reglas, verificados = [], 0, 0
    for f in filas:
        grupos[tuple(f.get(c) for c in CLAVES)].append(f)
    for clave, fs in grupos.items():
        per, run, ctx = clave
        etiqueta = "/".join(map(str, clave))
        codigos = [f.get("codigo_cuenta") for f in fs]
        if len(codigos) != len(set(codigos)):
            errores.append(f"{tabla}/{etiqueta}: claves de cuenta duplicadas")
        if set(codigos) != xml.CODIGOS_TABLA[tabla]:
            errores.append(
                f"{tabla}/{etiqueta}: conjunto de cuentas no es el del catálogo"
            )
        if ctx not in xml.CONTEXTOS_TABLA[tabla]:
            errores.append(f"{tabla}/{etiqueta}: contexto no permitido")
        campos = (
            "moneda",
            "moneda_cmf",
            "tipo_entidad",
            "fuente_archivo",
            "sha256_archivo",
            "fecha_inicio_contexto",
            "fecha_fin_contexto",
            "tipo_periodo",
            "cotejo_ficha",
        )
        if any(len({f.get(c) for f in fs}) != 1 for c in campos):
            errores.append(
                f"{tabla}/{etiqueta}: metadatos mezclados dentro de un contexto"
            )
        r = fs[0]
        try:
            corte = xml.fin_periodo(per)
            inicio, fin = (
                date.fromisoformat(r["fecha_inicio_contexto"]),
                date.fromisoformat(r["fecha_fin_contexto"]),
            )
            if ctx == "SaldoInicialTerceraColumna":
                correcto = inicio <= fin < date(corte.year, 1, 1)
            else:
                y = (
                    corte.year
                    if ctx in ("PeriodoActual", "TrimestreActual")
                    else corte.year - 1
                )
                m = 12 if ctx == "PeriodoAnualAnterior" else corte.month
                minimo = (
                    date(y, m - 2, 1)
                    if ctx and ctx.startswith("Trimestre")
                    else date(y, 1, 1)
                )
                correcto = (
                    fin == date(y, m, calendar.monthrange(y, m)[1])
                    and minimo <= inicio <= fin
                )
            if not correcto:
                raise ValueError("fecha no corresponde al contexto")
        except (ValueError, TypeError, KeyError) as e:
            errores.append(f"{tabla}/{etiqueta}: fechas inválidas ({e})")
        if not isinstance(run, str) or not run.isdigit():
            errores.append(f"{tabla}/{etiqueta}: RUN inválido")
        else:
            if any(f.get("run_fondo_dv") != f"{run}-{xml.dv(run)}" for f in fs):
                errores.append(f"{tabla}/{etiqueta}: RUN-DV publicado inválido")
        if xml.MONEDAS.get(r.get("moneda_cmf")) != r.get("moneda"):
            errores.append(f"{tabla}/{etiqueta}: moneda incoherente")
        if r.get("tipo_entidad") not in ("FINRE", "FIRES"):
            errores.append(f"{tabla}/{etiqueta}: tipo de fondo inválido")
        if not xml.ARCHIVO_RE.fullmatch(r.get("fuente_archivo") or ""):
            errores.append(f"{tabla}/{etiqueta}: falta archivo FIEF válido")
        sha = r.get("sha256_archivo") or ""
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            errores.append(f"{tabla}/{etiqueta}: SHA-256 inválido")
        tipop = (
            "saldo"
            if tabla == "balance"
            else "trimestre"
            if ctx and ctx.startswith("Trimestre")
            else "acumulado"
        )
        if r.get("tipo_periodo") != tipop:
            errores.append(f"{tabla}/{etiqueta}: tipo de período incorrecto")
        if r.get("cotejo_ficha") not in ("coincide", "sin_columna") or (
            ctx == "PeriodoActual" and r.get("cotejo_ficha") != "coincide"
        ):
            errores.append(f"{tabla}/{etiqueta}: falta cotejo del contexto actual")
        esperado = {cod: (i, sec, tipo) for i, cod, _, sec, tipo in xml.CATALOGO[tabla]}
        for f in fs:
            if esperado.get(f.get("codigo_cuenta")) != (
                f.get("orden"),
                f.get("seccion"),
                f.get("tipo_linea"),
            ):
                errores.append(
                    f"{tabla}/{etiqueta}: orden/clasificación no corresponde a la cuenta"
                )
                break
        cuentas = {f.get("codigo_cuenta"): f.get("valor_miles_mf") for f in fs}
        n, malos = xml.verificar_cuentas(tabla, cuentas)
        reglas += n
        if n:
            verificados += 1
        errores += [f"{tabla}/{etiqueta}: {m}" for m in malos]
    entidades = {(p, run) for p, run, _ in grupos}
    actuales = {(p, run) for p, run, ctx in grupos if ctx == "PeriodoActual"}
    if entidades != actuales:
        errores.append(f"{tabla}: existen comparativos sin un estado actual")
    return {
        "grupos": len(grupos),
        "verificados": verificados,
        "reglas": reglas,
        "actuales": actuales,
        "errores": errores,
    }


def verificar_tablas(filas):
    rs = {t: verificar_filas(t, filas[t]) for t in ("balance", "resultados")}
    errores = [e for r in rs.values() for e in r["errores"]]
    if rs["balance"]["actuales"] != rs["resultados"]["actuales"]:
        errores.append("cobertura distinta entre balance y resultados actuales")
    if not rs["balance"]["actuales"]:
        errores.append("ningún fondo con ambos estados actuales")
    return {
        "reglas": sum(r["reglas"] for r in rs.values()),
        "fondos_cierres": len(rs["balance"]["actuales"]),
        "contextos": {t: r["grupos"] for t, r in rs.items()},
        "errores": errores,
    }


def auditar(salida, permitir_vacio=False):
    """Lee una partición a la vez: no carga toda la historia de FI en memoria."""
    salida = Path(salida)
    errores, reglas, contextos = [], 0, {}
    actuales = {"balance": set(), "resultados": set()}
    controlp = salida / "fi_eeff_control.json"
    control = (
        json.loads(controlp.read_text(encoding="utf-8"))
        if controlp.exists()
        else {"periodos": {}}
    )
    for t, actuales_t in actuales.items():
        carpeta = salida / f"fi_{t}"
        mp = carpeta / "manifest.json"
        if not mp.exists():
            if permitir_vacio and not control["periodos"]:
                continue
            errores.append(f"falta manifiesto de fi_{t}")
            continue
        man = json.loads(mp.read_text(encoding="utf-8"))
        archivos = sorted(
            p for p in carpeta.glob("*.parquet") if p.name != "_vacio.parquet"
        )
        if [p.name for p in archivos] != [Path(f).name for f in man["files"]]:
            errores.append(f"fi_{t}: manifiesto no enumera exactamente las particiones")
        if man["periodos"] != [p.stem for p in archivos] or man["periodos"] != sorted(
            control["periodos"]
        ):
            errores.append(f"fi_{t}: períodos no coinciden con particiones/control")
        total = 0
        contextos[t] = 0
        for p in archivos:
            table = pq.read_table(p)
            if tuple(table.column_names) != xml.COLUMNAS:
                errores.append(f"{p}: esquema inesperado")
            fs = table.to_pylist()
            total += len(fs)
            if {f.get("periodo") for f in fs} != {p.stem}:
                errores.append(f"{p}: período distinto de la partición o archivo vacío")
            if p.stem not in control["periodos"]:
                errores.append(f"{p}: período no registrado en el control")
            else:
                ctl = control["periodos"][p.stem]
                if ctl["filas"][t] != len(fs):
                    errores.append(f"{p}: filas no coinciden con el control")
                esperado = ctl.get("sha256_parquet", {}).get(t)
                if esperado and esperado != hashlib.sha256(p.read_bytes()).hexdigest():
                    errores.append(f"{p}: SHA-256 Parquet no coincide con el control")
                rechazados = {
                    (run, ctx)
                    for run, reg in ctl["registros"].items()
                    for ctx, v in reg.get("validacion", {}).get(t, {}).items()
                    if v["estado"] == "rechazado"
                }
                if any(
                    (f.get("run_fondo"), f.get("contexto")) in rechazados for f in fs
                ):
                    errores.append(
                        f"{p}: se publicaron cifras de un comparativo rechazado"
                    )
            r = verificar_filas(t, fs)
            reglas += r["reglas"]
            contextos[t] += r["grupos"]
            actuales_t.update(r["actuales"])
            errores += r["errores"]
        if man["total_records"] != total:
            errores.append(f"fi_{t}: conteo de filas distinto del manifiesto")
    if actuales["balance"] != actuales["resultados"]:
        errores.append("cobertura distinta entre balance y resultados actuales")
    if not actuales["balance"] and not (permitir_vacio and not control["periodos"]):
        errores.append("ningún fondo con ambos estados actuales")
    return {
        "fondos_cierres": len(actuales["balance"]),
        "reglas": reglas,
        "contextos": contextos,
        "errores": errores,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salida", type=Path, default=RAIZ / "docs/outputs/fi")
    p.add_argument("--permitir-vacio", action="store_true")
    a = p.parse_args(argv)
    r = auditar(a.salida, a.permitir_vacio)
    for e in r["errores"][:30]:
        print(f"FALLA FI EEFF: {e}")
    print(
        f"FI EEFF: {r['fondos_cierres']} fondo-cierres, {r['reglas']} identidades verificadas, {len(r['errores'])} fallas"
    )
    return int(bool(r["errores"]))


if __name__ == "__main__":
    raise SystemExit(main())
