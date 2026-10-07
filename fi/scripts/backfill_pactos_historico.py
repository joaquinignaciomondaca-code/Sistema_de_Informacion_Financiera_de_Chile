"""Recupera el histórico IFRS de pactos VRC/CRV sin reprocesar las demás carteras FI.

La CMF ofrece una página por RUN y trimestre. El rango histórico se recorre sobre todos los RUN
vigentes y no vigentes del registro CMF. Las páginas sin operaciones se auditan como tales; no se
fabrican filas cero. Las filas centinela que la CMF usa para rellenar una tabla vacía se excluyen
mediante el parser compartido con la actualización incremental.

Uso habitual en Actions:
  python -m fi.scripts.backfill_pactos_historico --desde 2008-03 --hasta 2019-12
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import estable  # noqa: E402
from fi.scripts import actualizar_carteras as ac  # noqa: E402

SALIDA = ac.SALIDA
DIR_PACTOS = SALIDA / "pactos"
ARCHIVO_CONTROL = DIR_PACTOS / "historico_control.json"
ARCHIVO_MANIFIESTO = DIR_PACTOS / "manifest.json"
DESDE_PREDETERMINADO = "2008-03"
HASTA_PREDETERMINADO = "2019-12"


def ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validar_periodo(valor: str) -> str:
    if len(valor) != 7 or valor[4] != "-" or not valor[:4].isdigit() or valor[5:] not in {"03", "06", "09", "12"}:
        raise argparse.ArgumentTypeError(f"cierre trimestral inválido {valor!r}; use AAAA-03/06/09/12")
    return valor


def periodos_rango(desde: str, hasta: str) -> list[str]:
    desde, hasta = validar_periodo(desde), validar_periodo(hasta)
    if desde > hasta:
        raise ValueError(f"el inicio {desde} es posterior al término {hasta}")
    return ac.trimestres(desde, hasta)


def leer_control() -> dict:
    if ARCHIVO_CONTROL.exists():
        control = json.loads(ARCHIVO_CONTROL.read_text(encoding="utf-8"))
    else:
        control = {"version": 1, "fuente": "CMF · ifrs_informe_vrc_crv.php", "periodos": {}, "fallidos": {}}
    control.setdefault("version", 1)
    control.setdefault("fuente", "CMF · ifrs_informe_vrc_crv.php")
    control.setdefault("periodos", {})
    control.setdefault("fallidos", {})
    return control


def guardar_control(control: dict) -> None:
    control["periodos"] = dict(sorted(control.get("periodos", {}).items()))
    control["fallidos"] = dict(sorted(control.get("fallidos", {}).items()))
    rango = sorted(set(control["periodos"]) | set(control["fallidos"]))
    if rango:
        control["rango_registrado"] = {"desde": rango[0], "hasta": rango[-1]}
    control["updated_at"] = ahora_utc()
    estable.escribir_json(ARCHIVO_CONTROL, control)


def runs_registro() -> tuple[list[str], str]:
    registro = ac.descargar_lista()
    runs = sorted({f["run_fondo"] for f in registro}, key=int)
    resumen = "\n".join(runs).encode("utf-8")
    if not runs:
        raise ac.ErrorValidacion("el registro CMF no devolvió RUN de fondos")
    return runs, hashlib.sha256(resumen).hexdigest()


def _descargar_y_parsear(run: str, periodo: str, max_intentos: int = 3):
    """Reintenta páginas HTML con esquema inesperado: CMF puede devolver respuestas transitorias."""
    ultimo_error = None
    for intento in range(1, max_intentos + 1):
        raw = ac._get(ac.url_pagina("V", run, periodo), timeout=45)
        try:
            parseado = ac.leer_pactos_detallado(raw)
            return raw, parseado, intento - 1, None, intento
        except ac.ErrorValidacion as e:
            ultimo_error = e
            if intento < max_intentos:
                time.sleep(2 * intento)
    return raw, None, max_intentos - 1, str(ultimo_error), max_intentos


def sondear_periodo(periodo: str, runs: list[str], hilos: int, hash_registro: str) -> tuple[dict, list[dict]]:
    """Descarga y valida un cierre completo; retorna el acta y solo las operaciones reales."""
    inicio = time.monotonic()
    filas: list[dict] = []
    hashes: list[str] = []
    errores_red, errores_parseo, malas, descuadres = [], [], [], []
    rellenos = paginas_parseadas = paginas_con_operaciones = paginas_descargadas = reintentos_formato = 0
    fondos_con_operaciones: set[str] = set()
    tipos = Counter()

    with ThreadPoolExecutor(max_workers=max(1, min(hilos, 32))) as pool:
        trabajos = {pool.submit(_descargar_y_parsear, run, periodo): run for run in runs}
        for futuro in as_completed(trabajos):
            run = trabajos[futuro]
            try:
                raw, resultado, reintentos, error_parseo, n_descargas = futuro.result()
            except Exception as e:  # no registrar un fallo de red como un trimestre sin operaciones
                errores_red.append(f"{run}: {type(e).__name__}: {e}")
                continue
            paginas_descargadas += n_descargas
            reintentos_formato += reintentos
            hashes.append(f"{run}|{hashlib.sha256(raw).hexdigest()}")
            if error_parseo:
                errores_parseo.append(f"{run}: {error_parseo}")
                continue
            operaciones, malas_pagina, descuadres_pagina, _, rellenos_pagina = resultado
            paginas_parseadas += 1
            rellenos += rellenos_pagina
            malas.extend(f"{run}: {x}" for x in malas_pagina)
            descuadres.extend(f"{run}: {x}" for x in descuadres_pagina)
            if operaciones:
                paginas_con_operaciones += 1
                fondos_con_operaciones.add(run)
            for fila in operaciones:
                fila["periodo"], fila["run_fondo"] = periodo, run
                tipos[str(fila.get("tipo_operacion") or "")] += 1
                filas.append(fila)

    resumen_hash = hashlib.sha256("\n".join(sorted(hashes)).encode("utf-8")).hexdigest()
    fondos_descuadrados = {x.split(":", 1)[0] for x in descuadres}
    corte_ilegibles = 0.01 * max(len(filas), 1)
    corte_descuadres = ac.MAX_DESCUADRE * max(len(fondos_con_operaciones), 1)
    fallas = []
    if errores_red:
        fallas.append(f"{len(errores_red)} descargas fallidas")
    if errores_parseo:
        fallas.append(f"{len(errores_parseo)} páginas sin esquema reconocido")
    if len(malas) > corte_ilegibles:
        fallas.append(f"{len(malas)} filas ilegibles supera el límite de 1 %")
    if len(fondos_descuadrados) > corte_descuadres:
        fallas.append(f"{len(fondos_descuadrados)} fondos no cuadran contra el TOTAL CMF")

    avisos = []
    if malas:
        avisos.append(f"{len(malas)} filas ilegibles (dentro del umbral del extractor)")
    if descuadres:
        avisos.append(f"{len(fondos_descuadrados)} fondos con descuadre (dentro del umbral del extractor)")
    acta = {
        "fecha_sondeo": ahora_utc(),
        "estado": "fallido" if fallas else ("sin_operaciones" if not filas else ("completo_con_avisos" if avisos else "completo")),
        "registro_fondos": len(runs),
        "sha256_registro_runs": hash_registro,
        "paginas_consultadas": len(runs),
        "paginas_descargadas": paginas_descargadas,
        "paginas_parseadas": paginas_parseadas,
        "paginas_reintentadas_por_esquema": reintentos_formato,
        "paginas_con_operaciones": paginas_con_operaciones,
        "fondos_con_operaciones": len(fondos_con_operaciones),
        "filas_operacion": len(filas),
        "filas_relleno_excluidas": rellenos,
        "filas_ilegibles": len(malas),
        "descuadres": len(descuadres),
        "tipos_operacion": dict(sorted(tipos.items())),
        "sha256_resumen_paginas": resumen_hash,
        "segundos": round(time.monotonic() - inicio, 1),
    }
    if avisos:
        acta["avisos"] = avisos
    if fallas:
        acta["errores"] = fallas + [f"red: {x}" for x in errores_red[:20]] + [f"parser: {x}" for x in errores_parseo[:20]]
        acta["detalle_filas_ilegibles"] = malas[:20]
        acta["detalle_descuadres"] = descuadres[:20]
    return acta, filas


def _periodos_en_parquets() -> tuple[list[str], int, list[Path]]:
    rutas = sorted(r for r in DIR_PACTOS.glob("*.parquet") if r.name != "_vacio.parquet")
    periodos, total = set(), 0
    for ruta in rutas:
        pf = pq.ParquetFile(ruta)
        total += pf.metadata.num_rows
        if pf.metadata.num_rows:
            periodos.update(str(x) for x in pq.read_table(ruta, columns=["periodo"])["periodo"].to_pylist() if x)
    return sorted(periodos), total, rutas


def escribir_manifiesto(control: dict) -> None:
    DIR_PACTOS.mkdir(parents=True, exist_ok=True)
    periodos_datos, total, rutas = _periodos_en_parquets()
    if not rutas:
        vacio = DIR_PACTOS / "_vacio.parquet"
        if not vacio.exists():
            pq.write_table(ac.esquema("pactos").empty_table(), vacio)
        rutas = [vacio]
    sondeados = set(control.get("periodos", {}))
    control_general = SALIDA / "manifest.json"
    if control_general.exists():
        publicado = json.loads(control_general.read_text(encoding="utf-8"))
        sondeados |= set(publicado.get("periodos", {}))
        sondeados |= set(publicado.get("sondeados_sin_datos", []))
    sondeados = sorted(sondeados)
    actualizado = {
        "tabla": "pactos",
        "files": [f"outputs/fi/pactos/{r.name}" for r in rutas],
        "total_records": total,
        "periodos": periodos_datos,
        "periodos_sondeados": sondeados,
        "updated_at": ahora_utc(),
    }
    if sondeados:
        actualizado["sondeo_historico"] = {"desde": sondeados[0], "hasta": sondeados[-1],
                                            "cierres_completados": len(sondeados),
                                            "cierres_con_operaciones": len(set(periodos_datos) & set(sondeados))}
    if control.get("fallidos"):
        actualizado["cierres_fallidos"] = sorted(control["fallidos"])
    estable.escribir_json(ARCHIVO_MANIFIESTO, actualizado)


def procesar(periodos: list[str], minutos: float, max_periodos: int, hilos: int, forzar: bool) -> int:
    inicio = time.monotonic()
    SALIDA.mkdir(parents=True, exist_ok=True)
    DIR_PACTOS.mkdir(parents=True, exist_ok=True)
    control = leer_control()
    runs, hash_registro = runs_registro()
    control["registro_fondos"] = len(runs)
    control["sha256_registro_runs"] = hash_registro
    control["rango_ultima_corrida"] = {"desde": periodos[0], "hasta": periodos[-1]}
    ya_completos = set(control["periodos"])
    pendientes = [p for p in periodos if forzar or p not in ya_completos]
    if max_periodos > 0:
        pendientes = pendientes[:max_periodos]
    print(f"Registro CMF: {len(runs)} RUN únicos; sondeo VRC/CRV {periodos[0]}–{periodos[-1]}.")
    print(f"Cierres ya auditados: {len(ya_completos)}; pendientes en esta corrida: {len(pendientes)}.")

    errores = []
    hechos = 0
    for periodo in pendientes:
        if time.monotonic() - inicio >= minutos * 60:
            print(f"Límite de {minutos:g} minutos; el siguiente cierre queda pendiente para reanudar.")
            break
        t0 = time.monotonic()
        acta, filas = sondear_periodo(periodo, runs, hilos, hash_registro)
        if acta["estado"] == "fallido":
            control["fallidos"][periodo] = acta
            guardar_control(control)
            errores.append(periodo)
            print(f"{periodo}: sondeo incompleto ({'; '.join(acta.get('errores', []))}); no se publica este cierre.")
            continue

        # Persistir solo filas reales. Un período vacío queda documentado en el control, sin parquet cero.
        if filas:
            ac.escribir("pactos", periodo, filas)
        control["periodos"][periodo] = acta
        control["fallidos"].pop(periodo, None)
        guardar_control(control)
        escribir_manifiesto(control)
        hechos += 1
        print(f"{periodo}: {acta['estado']}, {acta['filas_operacion']} operaciones, "
              f"{acta['filas_relleno_excluidas']} rellenos excluidos, "
              f"{acta['paginas_parseadas']}/{acta['paginas_consultadas']} páginas ({time.monotonic() - t0:.0f} s).")

    escribir_manifiesto(control)
    print(f"Cierres auditados en esta corrida: {hechos}; total histórico auditado: {len(control['periodos'])}.")
    if errores:
        print("Cierres no publicados por respuestas incompletas: " + ", ".join(errores))
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", default=DESDE_PREDETERMINADO, help="primer cierre, AAAA-03/06/09/12 (default 2008-03)")
    ap.add_argument("--hasta", default=HASTA_PREDETERMINADO, help="último cierre (default 2019-12)")
    ap.add_argument("--max-periodos", type=int, default=0, help="cierres máximos por corrida (0 = sin tope)")
    ap.add_argument("--minutos", type=float, default=270, help="tiempo máximo por corrida; progreso reanudable")
    ap.add_argument("--hilos", type=int, default=16, help="descargas concurrentes (1–32)")
    ap.add_argument("--forzar", action="store_true", help="volver a descargar incluso cierres ya auditados")
    args = ap.parse_args(argv)
    if args.max_periodos < 0 or args.minutos <= 0 or not 1 <= args.hilos <= 32:
        ap.error("max-periodos debe ser >=0, minutos >0 e hilos entre 1 y 32")
    try:
        periodos = periodos_rango(args.desde, args.hasta)
    except (argparse.ArgumentTypeError, ValueError) as e:
        ap.error(str(e))
    return procesar(periodos, args.minutos, args.max_periodos, args.hilos, args.forzar)


if __name__ == "__main__":
    raise SystemExit(main())
