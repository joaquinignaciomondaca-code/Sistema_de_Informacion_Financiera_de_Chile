#!/usr/bin/env python3
"""Estados financieros IFRS de corredores de bolsa y agentes de valores (CMF).

Fuente: estadística CMF «Estados financieros de intermediarios de valores»
(intermediarios_ifrs1.php con xls=y). Un Excel por trimestre y tipo de intermediario
(1 = corredores, 2 = agentes) con una fila por sociedad y una columna por cuenta
FECU IFRS (código «11.01.00» + nombre). Se publican balance (1x, 2x) y resultados
(30 estado de resultados; 31-32 otros resultados integrales); el flujo de efectivo (5x) no. Cifras en miles de pesos, moneda corriente
del cierre. Los datos parten en 2010-12.

Incremental (docs/outputs/corredoras_bolsa/manifest.json):
  * trimestres cerrados (más de DIAS_CIERRE días desde el cierre) no se vuelven a pedir;
  * los recientes se releen en cada corrida hasta cerrarse (presentaciones tardías);
  * si la CMF responde HTML en vez del Excel, el trimestre aún no está publicado
    (o, antes de 2010-12, no existe).

Salidas (formato largo, una fila por sociedad y cuenta):
  docs/outputs/corredoras_bolsa/corredoras_bolsa_balance/<AAAA>.parquet
  docs/outputs/corredoras_bolsa/corredoras_bolsa_resultados/<AAAA>.parquet
  + manifest.json de cada tabla.
"""
from __future__ import annotations

import argparse
import io
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import cuadratura, estable  # noqa: E402
SALIDA = RAIZ / "docs" / "outputs" / "corredoras_bolsa"
CONTROL = SALIDA / "manifest.json"
URL = ("https://www.cmfchile.cl/institucional/estadisticas/merc_valores/intermediarios_fecu_ifrs/"
       "intermediarios_ifrs1.php?lang=es&sociedad%5B%5D=0&ag=0&indcon=0&xls=y&tiposociedad={tipo}"
       "&cuenta=&estimado=2&vsn=2&mes1={mm}&anno1={aaaa}&mes2={mm}&anno2={aaaa}")
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)"}
DESDE = "2010-12"
DIAS_CIERRE = 150
TIPOS = {1: "corredor de bolsa", 2: "agente de valores"}
TABLAS = ("balance", "resultados")

ESQUEMA = pa.schema([
    ("periodo", pa.string()), ("rut", pa.string()), ("rut_dv", pa.string()), ("razon_social", pa.string()),
    ("tipo_intermediario", pa.string()), ("estado_financiero", pa.string()), ("seccion", pa.string()),
    ("codigo_fecu", pa.string()), ("cuenta", pa.string()), ("nivel", pa.int8()), ("valor_miles_clp", pa.int64()),
    ("en_lista_entidades", pa.bool_()),
])


class ErrorFuente(Exception):
    pass


def _get(url: str) -> bytes:
    ultimo = None
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                return r.read()
        except Exception as e:
            ultimo = e
            time.sleep(5 * (intento + 1))
    raise ErrorFuente(f"{url}: {ultimo}")


def arreglar(txt) -> str:
    """Los encabezados vienen en UTF-8 leído como latin-1 («RazÃ³n»)."""
    s = "" if txt is None or (isinstance(txt, float) and pd.isna(txt)) else str(txt).strip()
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


# Texto sin espacios -> texto legible. Se completa con el informe HTML de cada corrida.
ETIQUETAS: dict[str, str] = {t.replace(" ", ""): t for t in (
    "Estado de situación financiera", "Estado de resultados", "Estado de resultados integrales",
    "Pasivos y Patrimonio", "Activos", "Pasivos", "Patrimonio", "Resultado por intermediación",
    "Ingresos por servicios", "Resultado por instrumentos financieros", "Resultado por operaciones de financiamiento",
    "Gastos de administración y comercialización", "Otros resultados", "Otros resultados integrales")}


def separar_palabras(s: str) -> str:
    """Los nombres de cuenta vienen sin espacios («Efectivoyefectivoequivalente»).
    Se usa el texto legible del informe HTML si existe; si no, se agregan espacios solo
    donde es seguro: antes de mayúsculas, paréntesis y guiones."""
    if s.replace(" ", "") in ETIQUETAS:
        return ETIQUETAS[s.replace(" ", "")]
    s = re.sub(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])", " ", s)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*-\s*", " - ", s)
    return " ".join(s.split())


def trimestres(desde: str, hasta: str) -> list[str]:
    y, m = int(desde[:4]), int(desde[5:])
    out = []
    while f"{y:04d}-{m:02d}" <= hasta:
        out.append(f"{y:04d}-{m:02d}")
        m += 3
        if m > 12:
            y, m = y + 1, 3
    return out


def ultimo_trimestre(hoy: date) -> str:
    y, m = hoy.year, (hoy.month - 1) // 3 * 3
    if m == 0:
        y, m = y - 1, 12
    return f"{y:04d}-{m:02d}"


def _hoy() -> date:
    """Fecha de la corrida (se aparta para que las pruebas no dependan del reloj)."""
    return date.today()


def cerrado(periodo: str, hoy: date) -> bool:
    y, m = int(periodo[:4]), int(periodo[5:])
    fin = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (hoy - fin).days > DIAS_CIERRE


def dv(cuerpo: str) -> str:
    s, m = 0, 2
    for c in reversed(cuerpo):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def nombres_cuentas(periodo: str) -> dict[str, tuple[str, int]]:
    """Nombre legible y nivel jerárquico de cada código FECU, desde la versión HTML del
    informe (el Excel trae los nombres sin espacios). Si falla, se usan los del Excel."""
    try:
        raw = _get(URL.format(tipo=1, mm=periodo[5:], aaaa=periodo[:4]).replace("xls=y", "xls=n"))
    except ErrorFuente:
        return {}
    html = raw.decode("utf-8", errors="replace")
    for texto in re.findall(r"\{c:\[\{v:'([^']*)'\}", html):
        texto = " ".join(texto.replace("&amp;", "&").split())
        if texto and not re.match(r"\d{2}\.", texto):
            ETIQUETAS.setdefault(texto.replace(" ", ""), texto)
    mapa = {}
    for sangria, cod, nombre in re.findall(r"\{v:'(\s*)(\d{2}\.\d{2}\.\d{2})\s+([^']*)'\}", html):
        mapa.setdefault(cod, (" ".join(nombre.replace("&amp;", "&").split()), max(len(sangria) // 3 - 1, 1)))
    return mapa


def leer_excel(raw: bytes, periodo: str, tipo: int, lista: set[str],
               nombres: dict[str, tuple[str, int]] | None = None) -> dict[str, list[dict]]:
    if not raw.startswith(b"PK"):
        raise ErrorFuente("sin Excel (trimestre no publicado)")
    x = pd.read_excel(io.BytesIO(raw), header=None, dtype=str)
    fila_enc = next((i for i in range(min(len(x), 20)) if arreglar(x.iat[i, 0]) == "Fecha"
                     and arreglar(x.iat[i, 1]) == "RUT"), None)
    if fila_enc is None:
        raise ErrorFuente("no se encontró la fila de encabezados")
    # Encabezados superiores (estado y sección) se extienden hacia la derecha.
    def extender(fila):
        vals, act = [], ""
        for v in x.iloc[fila].tolist():
            v = arreglar(v)
            act = v or act
            vals.append(act)
        return vals
    estados = extender(fila_enc - 2) if fila_enc >= 2 else [""] * x.shape[1]
    secciones = extender(fila_enc - 1)
    columnas, vistos = [], set()
    for j, h in enumerate(x.iloc[fila_enc].tolist()):
        h = arreglar(h)
        m = re.match(r"^(\d{2}\.\d{2}\.\d{2})\s*(.*)$", h)
        if not m:
            continue
        cod = m.group(1)
        # Plan FECU IFRS: 1x activos, 2x pasivos y patrimonio, 30 resultados, 31-32 otros resultados
        # integrales, 5x flujo de efectivo (no se publica, igual que en los demás sectores).
        # 30.00.00 (utilidad del ejercicio) se repite al inicio de los resultados integrales: solo
        # se toma la primera aparición de cada código.
        if cod[0] not in "123" or cod in vistos:
            continue
        vistos.add(cod)
        tabla = "balance" if cod[0] in "12" else "resultados"
        est = ("Estado de situación financiera" if tabla == "balance" else
               "Estado de resultados" if cod.startswith("30") else "Estado de otros resultados integrales")
        nombre, nivel = (nombres or {}).get(cod, (separar_palabras(m.group(2)), 0))
        columnas.append((j, tabla, separar_palabras(est), separar_palabras(secciones[j]),
                         cod, nombre, nivel))
    if len(columnas) < 40:
        raise ErrorFuente(f"solo {len(columnas)} cuentas FECU en el Excel")
    esperado = f"{periodo[5:]} / {periodo[:4]}"
    datos = {t: [] for t in TABLAS}
    n = 0
    for i in range(fila_enc + 1, len(x)):
        fecha, rut_txt, nombre = (arreglar(x.iat[i, k]) for k in range(3))
        if not rut_txt or not re.match(r"^[\d.]+-[\dkK]$", rut_txt):
            continue
        if fecha != esperado:
            raise ErrorFuente(f"fila {i}: fecha {fecha!r} distinta de {esperado!r}")
        cuerpo, d = rut_txt.replace(".", "").upper().split("-")
        if dv(cuerpo) != d:
            raise ErrorFuente(f"RUT con dígito verificador inválido: {rut_txt}")
        n += 1
        for j, tabla, est, sec, cod, cuenta, nivel in columnas:
            v = x.iat[i, j]
            if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
                continue
            v = str(v).strip()
            if not re.fullmatch(r"-?\d+(\.0+)?", v):
                raise ErrorFuente(f"{rut_txt} {cod}: valor no entero {v!r}")
            datos[tabla].append({
                "periodo": periodo, "rut": cuerpo, "rut_dv": f"{cuerpo}-{d}", "razon_social": nombre,
                "tipo_intermediario": TIPOS[tipo], "estado_financiero": est, "seccion": sec,
                "codigo_fecu": cod, "cuenta": cuenta, "nivel": nivel, "valor_miles_clp": int(float(v)),
                "en_lista_entidades": cuerpo in lista,
            })
    if n == 0:
        raise ErrorFuente("Excel sin sociedades")
    return datos


def escribir(tabla: str, periodo: str, filas: list[dict]) -> None:
    carpeta = SALIDA / f"corredoras_bolsa_{tabla}"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{periodo[:4]}.parquet"
    partes = []
    if ruta.exists():
        viejo = pq.read_table(ruta).to_pandas()
        partes.append(viejo[viejo["periodo"] != periodo])
    partes.append(pd.DataFrame(filas, columns=ESQUEMA.names))
    partes = [p for p in partes if len(p)]
    if not partes:
        return
    df = pd.concat(partes, ignore_index=True).sort_values(
        ["periodo", "tipo_intermediario", "rut", "codigo_fecu"], kind="stable")
    tmp = ruta.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pandas(df, schema=ESQUEMA, preserve_index=False), tmp,
                   compression="zstd", compression_level=9)
    os.replace(tmp, ruta)


def cargar_control() -> dict:
    return json.loads(CONTROL.read_text()) if CONTROL.exists() else {"periodos": {}}


def guardar_control(c: dict) -> None:
    c["periodos"] = dict(sorted(c["periodos"].items()))
    c["desde"] = DESDE
    c["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estable.escribir_json(CONTROL, c)


def escribir_manifiestos(c: dict) -> None:
    con = [p for p, v in sorted(c["periodos"].items()) if v.get("sociedades")]
    for tabla in TABLAS:
        carpeta = SALIDA / f"corredoras_bolsa_{tabla}"
        carpeta.mkdir(parents=True, exist_ok=True)
        rutas = sorted(carpeta.glob("*.parquet"))
        man = {"tabla": f"corredoras_bolsa_{tabla}",
               "files": [f"outputs/corredoras_bolsa/{carpeta.name}/{r.name}" for r in rutas],
               "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas),
               "periodos": con, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        estable.escribir_json((carpeta / "manifest.json"), man)


ORIGEN = ("CMF — Estadísticas de estados financieros IFRS de intermediarios de valores (corredores de bolsa y "
          "agentes de valores), https://www.cmfchile.cl/institucional/estadisticas/merc_valores/"
          "intermediarios_fecu_ifrs/")
DESCRIPCION = {
    "balance": "Estado de situación financiera de cada corredor de bolsa y agente de valores, cuenta FECU por "
               "cuenta, al cierre de cada trimestre. Miles de pesos.",
    "resultados": "Estado de resultados y resultados integrales de cada corredor de bolsa y agente de valores, "
                  "acumulados del ejercicio al cierre de cada trimestre, cuenta FECU por cuenta. Miles de pesos.",
}


def actualizar_data_manifest() -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    hoy = date.today().isoformat()
    nuevas = []
    for tabla in TABLAS:
        m = SALIDA / f"corredoras_bolsa_{tabla}" / "manifest.json"
        if not m.exists():
            continue
        mm = json.loads(m.read_text())
        per = mm["periodos"]
        nuevas.append({
            "id": f"corredoras_bolsa_{tabla}", "name": f"corredoras.{tabla}", "view_name": f"corredoras_bolsa_{tabla}",
            "sector": "corredoras_bolsa", "sector_label": "Corredoras de Bolsa", "norma": "IFRS · FECU intermediarios CMF",
            "corte": f"{per[0]} a {per[-1]}" if per else "sin trimestres",
            "frescura": f"Último trimestre publicado: {per[-1]}" if per else "",
            "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
            "file_parquet": f"outputs/corredoras_bolsa/corredoras_bolsa_{tabla}/manifest.json",
            "registros_reales": mm["total_records"], "descripcion": DESCRIPCION[tabla], "origen": ORIGEN,
        })
    quitar = {e["id"] for e in nuevas} | {"corredoras_bolsa_balance_resumen", "corredoras_bolsa_caratula_eeff_historico"}
    man["tables"] = [t for t in man["tables"] if t["id"] not in quitar] + nuevas
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    estable.escribir_json(ruta, man)


def refrescar_marcas(lista: set[str], c: dict) -> int:
    """Recalcula en_lista_entidades de todo lo publicado contra la lista vigente (la lista crece
    con pipelines/entidades); reescribe solo los años que cambian."""
    cambios = 0
    for tabla in TABLAS:
        for ruta in sorted((SALIDA / f"corredoras_bolsa_{tabla}").glob("*.parquet")):
            t = pq.read_table(ruta)
            nueva = [r in lista for r in t.column("rut").to_pylist()]
            if nueva == t.column("en_lista_entidades").to_pylist():
                continue
            t = t.set_column(t.schema.get_field_index("en_lista_entidades"), "en_lista_entidades",
                             pa.array(nueva, pa.bool_()))
            tmp = ruta.with_suffix(".tmp")
            pq.write_table(t, tmp, compression="zstd", compression_level=9)
            os.replace(tmp, ruta)
            cambios += 1
    for per in c["periodos"].values():
        if "corredores_fuera_de_lista" in per:
            per["corredores_fuera_de_lista"] = [e for e in per["corredores_fuera_de_lista"]
                                                if e["rut"].split("-")[0] not in lista]
    if cambios:
        print(f"Marca en_lista_entidades actualizada en {cambios} archivos")
    return cambios


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", default=None, help="primer cierre (AAAA-MM); vacío = autodescubre el más antiguo disponible")
    ap.add_argument("--hasta", default=None, help="último mes a considerar (por defecto, el último mes cerrado)")
    ap.add_argument("--minutos", type=float, default=270, help="tope de tiempo de la corrida (el progreso se conserva)")
    ap.add_argument("--max-periodos", type=int, default=0, help="máximo de cierres a revisar por corrida (0 = sin tope)")
    ap.add_argument("--solo-data-manifest", action="store_true")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
        return 0
    inicio, hoy = time.monotonic(), _hoy()
    SALIDA.mkdir(parents=True, exist_ok=True)
    c = cargar_control()
    lista = {str(e["rut"]).replace(".", "").split("-")[0]
             for e in json.loads((SALIDA / "corredoras_bolsa_maestro.json").read_text(encoding="utf-8"))}
    
    # Determinar el primer trimestre
    if a.desde:
        primer_trimestre = a.desde
    elif c["periodos"]:
        # Ya hay datos publicados: usar el más antiguo
        primer_trimestre = min(c["periodos"].keys())
    else:
        # Primera corrida: usar el default
        primer_trimestre = DESDE
    
    hasta = a.hasta or ultimo_trimestre(hoy)
    todos = trimestres(primer_trimestre, hasta)
    pendientes = [p for p in todos if not c["periodos"].get(p, {}).get("cerrado")]
    
    if a.max_periodos > 0:
        pendientes = pendientes[:a.max_periodos]
    
    print(f"Trimestres {primer_trimestre}..{todos[-1]}: cerrados {len(todos) - len(pendientes)}, a leer {len(pendientes)}")
    hechos, errores, defectos = 0, [], []
    nombres = nombres_cuentas(todos[-2]) if pendientes else {}
    print(f"Nombres de cuentas desde el informe HTML: {len(nombres)}")
    for periodo in pendientes:
        if time.monotonic() - inicio > a.minutos * 60:
            print("Tiempo agotado; el resto sigue en la próxima corrida.")
            break
        datos = {t: [] for t in TABLAS}
        por_tipo, avisos, sha_origen = {}, [], {}
        for tipo in TIPOS:
            try:
                raw = _get(URL.format(tipo=tipo, mm=periodo[5:], aaaa=periodo[:4]))
                sha_origen[TIPOS[tipo]] = hashlib.sha256(raw).hexdigest()
                d = leer_excel(raw, periodo, tipo, lista, nombres)
            except ErrorFuente as e:
                avisos.append(f"{TIPOS[tipo]}: {e}")
                continue
            por_tipo[TIPOS[tipo]] = len({f["rut"] for t in TABLAS for f in d[t]})
            for t in TABLAS:
                datos[t] += d[t]
        previo = c["periodos"].get(periodo, {})
        if not por_tipo.get(TIPOS[1]):
            # Sin corredores no hay trimestre publicado; si está cerrado, no existe en la fuente.
            if cerrado(periodo, hoy) and periodo <= "2011-06":
                c["periodos"][periodo] = {"cerrado": True, "sociedades": 0, "avisos": avisos}
                guardar_control(c)
            print(f"{periodo}: sin datos ({'; '.join(avisos)})")
            continue
        total = sum(por_tipo.values())
        if total < previo.get("sociedades", 0):
            print(f"::warning::{periodo}: la relectura trae {total} sociedades (antes {previo['sociedades']}); se mantiene")
            continue
        # Cuadratura contable (README §4): activos = pasivos + patrimonio (FECU 10 = 21 + 22).
        # Se detiene ante una falla en bloque (≥3 y más del 5 %) y también si de pronto casi ningún
        # balance trae los tres totales reconocibles (cambiaron los códigos y la compuerta quedó
        # ciega): sin `balances_totales` esa segunda condición no existía y un cambio de códigos
        # publicaba a ciegas.
        verificados, descuadres = cuadratura.verificar_fecu(datos["balance"])
        balances_totales = cuadratura.contar_grupos(datos["balance"], cuadratura.CLAVES_FECU)
        motivo = cuadratura.motivo_detener(verificados, descuadres, balances_totales)
        if motivo:
            # Un trimestre abierto que no pasa la compuerta es una falla de la corrida; uno ya cerrado
            # es una fuente histórica defectuosa: se avisa, pero no deja la corrida en rojo para siempre.
            (defectos if cerrado(periodo, hoy) else errores).append(f"{periodo}: {motivo}")
            print(f"::warning::{periodo}: {motivo}; no se publica")
            continue
        avisos += [f"balance no cuadra: {m}" for m in descuadres]
        for t in TABLAS:
            escribir(t, periodo, datos[t])
        fuera = sorted({(f["rut_dv"], f["razon_social"]) for f in datos["balance"]
                        if f["tipo_intermediario"] == TIPOS[1] and not f["en_lista_entidades"]})
        c["periodos"][periodo] = {"cerrado": cerrado(periodo, hoy), "sociedades": total, "por_tipo": por_tipo,
                                  "balances_verificados": verificados, "balances_totales": balances_totales,
                                  "filas": {t: len(datos[t]) for t in TABLAS},
                                  "corredores_fuera_de_lista": [{"rut": r, "razon_social": n} for r, n in fuera],
                                  "avisos": avisos, "sha256_origen": sha_origen}
        guardar_control(c)
        hechos += 1
        print(f"{periodo}: {por_tipo} · balance {len(datos['balance'])} · resultados {len(datos['resultados'])}"
              + (f" · avisos: {avisos}" if avisos else ""))
    hechos += refrescar_marcas(lista, c)
    guardar_control(c)
    con = [p for p, v in c["periodos"].items() if v.get("sociedades")]
    if con:
        ult = max(con)
        for e in c["periodos"][ult].get("corredores_fuera_de_lista", []):
            print(f"::notice::corredor {e['rut']} {e['razon_social']} reporta en {ult} y no está en la lista de entidades")
    escribir_manifiestos(c)
    actualizar_data_manifest()
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"publicados={hechos}\n")
    print(f"Trimestres escritos: {hechos}"
          + (f" · errores: {len(errores)}" if errores else "")
          + (f" · trimestres cerrados que no pasan las compuertas: {len(defectos)}" if defectos else ""))
    return 1 if errores and not hechos else 0


if __name__ == "__main__":
    sys.exit(main())
