#!/usr/bin/env python3
"""Estados financieros IFRS de AGF, securitizadoras y cajas de compensación (CMF).

Fuente única: el archivo TXT trimestral de la CMF «Estados financieros bajo estándar
IFRS» (estadisticas_ifrs.php → ver_archivo.php?inicio=AAAAMM&termino=AAAAMM). Cada
archivo trae, para todas las sociedades que envían sus estados financieros IFRS
(XBRL, columna «taxonomía»), las cuentas del estado de situación (ESF) y del estado
de resultados (ER) por RUT. Un solo archivo por trimestre alimenta los tres sectores.

Incremental:
  * docs/outputs/ifrs_sectores/manifest.json guarda los trimestres ya procesados.
  * Un trimestre «cerrado» (más de DIAS_CIERRE días desde el fin del trimestre) no se
    vuelve a descargar nunca.
  * Los trimestres recientes se vuelven a leer en cada corrida hasta que se cierran,
    para recoger a las sociedades que presentan tarde. Solo se reescribe el archivo
    anual de ese año.

Selección de entidades por sector: RUT de la lista de entidades del sector, o nombre
reportado que calza con el patrón del sector (así aparecen solas las entidades nuevas,
que quedan marcadas en_lista_entidades = false y se informan en el manifiesto).

Altas automáticas en listas sin registro CMF propio: una sociedad que en el último trimestre
reporta con nombre de caja de compensación (CCAF) o de factoring/leasing y no está en la
lista respectiva se agrega a esa lista (docs/outputs/entidades/novedades_ifrs.json deja el
evento). Solo el último trimestre: una sociedad que dejó de existir no reaparece. Para
factoring/leasing el archivo solo se usa para detectar; sus tablas las publica
factoring_leasing/scripts/backfill_ifrs.py con esa misma lista.

Montos: el entero literal del archivo, en unidades de la moneda informada (moneda =
CLP o USD). No se convierte, no se suma ni se redondea. Si un valor no es entero se
deja nulo y el texto original queda en valor_no_numerico.

El reconocimiento del archivo, el reparto por estado, el tratamiento del importe y el
conteo de `orden`/`repeticion` viven en `pipelines/auto/ifrs_txt.py`, compartido con el
backfill de factoring y leasing: los dos leen este mismo TXT y no pueden interpretarlo
distinto. La cuadratura contable, en `pipelines/auto/cuadratura.py`.

Salidas por sector y tabla (balance, resultados):
  docs/outputs/<carpeta>/<prefijo>_<tabla>/<AAAA>.parquet  +  manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import cuadratura, estable, ifrs_txt  # noqa: E402
DOCS = RAIZ / "docs" / "outputs"
CONTROL = DOCS / "ifrs_sectores" / "manifest.json"
# Fichas del diccionario de la web: allí se publica la cobertura de cada sector.
RUTA_DICCIONARIO = RAIZ / "docs" / "js" / "data_dictionary.js"
INDICE = "https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php"
ARCHIVO = "https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={0}&termino={1}"
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)", "Accept": "text/plain,text/html,*/*"}
DIAS_CIERRE = 150

SECTORES = {
    "agf": {
        "carpeta": "agf", "prefijo": "agf", "etiqueta": "Administradoras Generales de Fondos",
        "lista": "agf/agf_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"ADMINISTRADORA\s+GENERAL\s+DE\s+FONDOS|\bA\.?\s?G\.?\s?F\.?(\s|$)"),
    },
    "securitizadoras": {
        "carpeta": "securitizadoras", "prefijo": "securitizadoras", "etiqueta": "Securitizadoras",
        "lista": "securitizadoras/securitizadoras_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"SECURITIZADORA"),
    },
    "cajas_compensacion": {
        "carpeta": "cajas_compensacion", "prefijo": "ccaf", "etiqueta": "Cajas de Compensación",
        "lista": "cajas_compensacion/ccaf_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"CAJA\s+DE\s+COMPENSACI"),
        "alta": lambda c, d, nombre: {
            "rut": int(c), "dv": d, "rut_completo": f"{int(c):,}".replace(",", ".") + f"-{d}", "razon_social": nombre,
            "nombre_fantasia": nombre, "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833", "regulador_primario": "SUSESO", "emisor_valores_cmf": False,
            "estado_vigencia": "Vigente", "lineas_deuda_registradas": False,
            "observaciones": "Agregada automáticamente: reporta estados financieros IFRS a la CMF."},
    },
}
# Listas que solo se completan con este archivo (sin tablas propias aquí).
SOLO_LISTA = {
    "factoring_leasing": {
        "lista": "factoring_leasing/factoring_leasing_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"\bFACTORING\b|\bLEASING\b"), "excluir": re.compile(r"^BANCO\b|SEGUROS"),
        "alta": lambda c, d, nombre: {
            "rut": f"{c}-{d}", "rut_formateado": f"{int(c):,}".replace(",", ".") + f"-{d}", "razon_social": nombre,
            "nombre_fantasia": nombre, "tipo_sociedad": "Factoring" if "FACTORING" in nombre.upper() else "Leasing",
            "segmento": "Factoring" if "FACTORING" in nombre.upper() else "Leasing",
            "registro_cmf": "Estados financieros IFRS (CMF)", "vigencia_cmf": "Vigente", "vigente": 1, "estado": "Activo",
            "es_factoring": int("FACTORING" in nombre.upper()),
            # El nombre no dice si el leasing es financiero u habitacional: solo se marca lo explícito.
            "es_leasing_habitacional": 1 if "HABITACIONAL" in nombre.upper() else None,
            "eeff_ifrs_en_cmf": "Sí (IFRS)", "fuente_eeff": "CMF > Estados financieros IFRS (TXT)",
            "observaciones": "Agregada automáticamente: reporta estados financieros IFRS a la CMF con giro factoring/leasing."},
    },
}
NOVEDADES = DOCS / "entidades" / "novedades_ifrs.json"
# Ventana en que una ausencia se considera novedad y no historia: 8 trimestres = 2 años.
TRIMESTRES_NOVEDAD = 8
MAX_ALTAS = 10
# Entidades que entran solo porque su NOMBRE calza con el giro (sin estar en la lista).
# Unas pocas son altas reales; muchas de golpe indican un patrón demasiado amplio, y eso
# mete sociedades de otro giro en la tabla del sector: se avisa para revisar el patrón.
MAX_FUERA_DE_LISTA = 5
# Un solo lugar define qué prefijo de estado va a cada tabla y cómo se traduce el
# tipo de balance: son las mismas reglas que usa el backfill de factoring y leasing.
TABLAS = ifrs_txt.TABLAS
TIPO_BALANCE = ifrs_txt.TIPO_BALANCE

ESQUEMA = pa.schema([
    ("periodo", pa.string()), ("rut", pa.string()), ("rut_dv", pa.string()),
    ("razon_social", pa.string()), ("tipo_balance", pa.string()), ("moneda", pa.string()),
    ("estado_financiero", pa.string()), ("orden", pa.int32()), ("cuenta", pa.string()),
    ("valor", pa.int64()), ("valor_no_numerico", pa.string()), ("repeticion", pa.int16()),
    ("taxonomia", pa.string()), ("en_lista_entidades", pa.bool_()),
])


class ErrorFuente(Exception):
    pass


class ErrorContenido(ErrorFuente):
    """La descarga vino completa pero su contenido no sirve (guardas de filas/sociedades).

    Se separa de ErrorFuente para poder distinguir un archivo histórico defectuoso —p. ej.
    201003, que la CMF solo publica con 4 sociedades— de un problema de red o de fuente.
    """
    pass


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs).get("href") or "")


def _get(url: str, timeout: int = 180) -> bytes:
    ultimo = None
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:  # red inestable de la CMF
            ultimo = e
            time.sleep(5 * (intento + 1))
    raise ErrorFuente(f"{url}: {ultimo}")


def dv(cuerpo: str) -> str:
    s, m = 0, 2
    for c in reversed(cuerpo):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def periodos_indice(raw: bytes) -> tuple[list[str], dict[str, str]]:
    """Trimestres del índice y, para cada uno, el enlace anual que lo contiene (respaldo)."""
    if b"<html" not in raw[:2000].lower():
        raise ErrorFuente("el índice CMF no es HTML")
    p = _Links()
    p.feed(raw.decode("utf-8", errors="replace"))
    periodos, anual = set(), {}
    for link in p.links:
        m = re.search(r"inicio=(\d{6})&(?:amp;)?termino=(\d{6})", link)
        if not m or "ver_archivo" not in link:
            continue
        a, b = m.groups()
        if a > b or a[4:] not in ("03", "06", "09", "12") or b[4:] not in ("03", "06", "09", "12"):
            continue
        y, mm = int(a[:4]), int(a[4:])
        while f"{y:04d}{mm:02d}" <= b:
            per = f"{y:04d}{mm:02d}"
            periodos.add(per)
            if a != b:
                anual[per] = (a, b)
            mm += 3
            if mm > 12:
                y, mm = y + 1, 3
    if not periodos:
        raise ErrorFuente("índice CMF sin trimestres")
    return sorted(periodos), anual


def cerrado(periodo: str, hoy: date) -> bool:
    y, m = int(periodo[:4]), int(periodo[4:])
    fin = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (hoy - fin).days > DIAS_CIERRE


def es_txt(raw: bytes) -> bool:
    return ifrs_txt.es_txt(raw)


def decodificar(raw: bytes) -> str:
    return ifrs_txt.decodificar(raw)


def _norm(s: str) -> str:
    return ifrs_txt.normalizar(s)


def cargar_listas() -> dict[str, dict[str, str]]:
    listas = {}
    for sec, cfg in {**SECTORES, **SOLO_LISTA}.items():
        filas = json.loads((DOCS / cfg["lista"]).read_text(encoding="utf-8"))
        ruts = {}
        for f in filas:
            cuerpo = str(f[cfg["clave_rut"]]).replace(".", "").split("-")[0].strip()
            if cuerpo.isdigit():
                ruts[cuerpo] = str(f.get("razon_social") or f.get("nombre_empresa") or "")
        if not ruts:
            raise ErrorFuente(f"lista de entidades vacía: {cfg['lista']}")
        listas[sec] = ruts
    return listas


def leer_archivo(raw: bytes, periodo: str, listas: dict[str, dict[str, str]]):
    """Devuelve {sector: {tabla: [filas]}}, estadísticas y avisos."""
    if not es_txt(raw):
        raise ErrorFuente("la descarga no es el TXT de la CMF")
    datos = {s: {t: [] for t in TABLAS} for s in SECTORES}
    avisos: list[str] = []
    entidades_archivo = set()
    lineas_periodo = 0
    contextos = ifrs_txt.Contextos()
    asignacion: dict[str, str | None] = {}
    candidatos: dict[str, dict[str, str]] = {s: {} for s in SOLO_LISTA}
    for n, c in ifrs_txt.lineas(raw):
        if len(c) < 9:
            if len(c) > 2 and c[0] == periodo:
                avisos.append(f"línea {n}: {len(c)} campos")
            continue
        per, cuerpo, nombre, tipo, moneda, cuenta, valor, tax, estado = c[:9]
        if per != periodo:
            continue  # el archivo anual trae otros trimestres
        lineas_periodo += 1
        entidades_archivo.add(cuerpo)
        if cuerpo not in asignacion:
            nn = ifrs_txt.normalizar(nombre)
            asignacion[cuerpo] = next((s for s in SECTORES if cuerpo in listas[s]), None) or \
                next((s for s, cfg in SECTORES.items() if cfg["patron"].search(nn)), None)
        sec = asignacion[cuerpo]
        if sec is None:
            for s, cfg in SOLO_LISTA.items():
                nn = ifrs_txt.normalizar(nombre)
                if cuerpo.isdigit() and cuerpo not in listas[s] and cfg["patron"].search(nn) and not cfg["excluir"].search(nn):
                    candidatos[s][f"{cuerpo}-{dv(cuerpo)}"] = nombre
            continue
        tabla = ifrs_txt.tabla_de(estado)
        if tabla is None:
            continue  # flujos de efectivo y otros estados: no se publican
        if len(c) != 9 or tipo not in TIPO_BALANCE or not cuenta:
            avisos.append(f"línea {n}: esquema inesperado ({cuerpo})")
            continue
        # `orden` y `repeticion` salen del contador compartido (la taxonomía entra en la
        # llave: dos taxonomías del mismo estado no deben intercalar sus cuentas).
        clave_estado = contextos.clave_estado(per, cuerpo, tipo, moneda, tax, estado)
        orden, repeticion = contextos.agregar(clave_estado, cuenta)
        valor_entero, valor_texto = ifrs_txt.valor_y_texto(valor)
        datos[sec][tabla].append({
            "periodo": f"{per[:4]}-{per[4:]}", "rut": cuerpo, "rut_dv": f"{cuerpo}-{dv(cuerpo)}" if cuerpo.isdigit() else cuerpo,
            "razon_social": nombre, "tipo_balance": TIPO_BALANCE[tipo], "moneda": moneda,
            "estado_financiero": estado, "orden": orden, "cuenta": cuenta,
            "valor": valor_entero, "valor_no_numerico": valor_texto,
            "repeticion": repeticion, "taxonomia": tax, "en_lista_entidades": cuerpo in listas[sec],
        })
    if lineas_periodo == 0:
        raise ErrorContenido(f"el archivo no trae filas de {periodo}")
    if len(entidades_archivo) < 50:
        raise ErrorContenido(f"el archivo trae solo {len(entidades_archivo)} sociedades")
    return datos, {"lineas": lineas_periodo, "sociedades": len(entidades_archivo),
                   "solo_lista_fuera": {s: [{"rut": r, "razon_social": n} for r, n in sorted(v.items())]
                                        for s, v in candidatos.items()}}, avisos


def ruta_tabla(sec: str, tabla: str) -> Path:
    cfg = SECTORES[sec]
    return DOCS / cfg["carpeta"] / f"{cfg['prefijo']}_{tabla}"


def escribir(sec: str, tabla: str, periodo: str, filas: list[dict]) -> None:
    carpeta = ruta_tabla(sec, tabla)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{periodo[:4]}.parquet"
    per = f"{periodo[:4]}-{periodo[4:]}"
    partes = []
    if ruta.exists():
        viejo = pq.read_table(ruta).to_pandas()
        partes.append(viejo[viejo["periodo"] != per])
    partes.append(pd.DataFrame(filas, columns=ESQUEMA.names))
    partes = [p for p in partes if len(p)]
    if not partes:
        ruta.unlink(missing_ok=True)
        return
    df = pd.concat(partes, ignore_index=True)
    df = df.sort_values(["periodo", "rut", "tipo_balance", "estado_financiero", "orden"], kind="stable")
    for col, tipo in (("orden", "int32"), ("repeticion", "int16")):
        df[col] = df[col].astype(tipo)
    df["valor"] = df["valor"].astype("Int64")
    tmp = ruta.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pandas(df, schema=ESQUEMA, preserve_index=False), tmp,
                   compression="zstd", compression_level=9)
    os.replace(tmp, ruta)


def refrescar_marcas(listas: dict[str, dict[str, str]], control: dict) -> int:
    """Recalcula en_lista_entidades de todo lo publicado contra la lista vigente (la lista crece
    con pipelines/entidades); reescribe solo los años que cambian. Devuelve archivos reescritos."""
    cambios = 0
    for sec in SECTORES:
        for tabla in TABLAS:
            for ruta in sorted(ruta_tabla(sec, tabla).glob("*.parquet")):
                t = pq.read_table(ruta)
                ruts = t.column("rut").to_pylist()
                nueva = [r in listas[sec] for r in ruts]
                if nueva == t.column("en_lista_entidades").to_pylist():
                    continue
                t = t.set_column(t.schema.get_field_index("en_lista_entidades"), "en_lista_entidades",
                                 pa.array(nueva, pa.bool_()))
                tmp = ruta.with_suffix(".tmp")
                pq.write_table(t, tmp, compression="zstd", compression_level=9)
                os.replace(tmp, ruta)
                cambios += 1
    for per in control["periodos"].values():
        for sec, r in per.get("sectores", {}).items():
            if "fuera_de_lista" in r:
                r["fuera_de_lista"] = [e for e in r["fuera_de_lista"] if e["rut"].split("-")[0] not in listas[sec]]
        for sec, lst in per.get("solo_lista_fuera", {}).items():
            per["solo_lista_fuera"][sec] = [e for e in lst if e["rut"].split("-")[0] not in listas.get(sec, {})]
    if cambios:
        print(f"Marca en_lista_entidades actualizada en {cambios} archivos")
    return cambios


def periodo_anterior(control: dict, periodo: str) -> str | None:
    """Trimestre publicado inmediatamente anterior a `periodo` (o None si no hay)."""
    anteriores = [p for p in sorted(control.get("periodos", {})) if p < periodo]
    return anteriores[-1] if anteriores else None


def dejaron_de_informar(control: dict, periodo: str, sec: str, presentes: set[str]) -> list[str]:
    """RUT que informaban en el trimestre anterior y en este no aparecen.

    La fuente no avisa de las ausencias: una entidad que se fusiona, se disuelve o
    simplemente deja de enviar su XBRL desaparece del archivo sin más. Comparar contra
    el trimestre anterior convierte ese silencio en un aviso con nombre y RUT.
    """
    ant = periodo_anterior(control, periodo)
    if not ant:
        return []
    ruts_antes = control["periodos"].get(ant, {}).get("ruts", {})
    if not ruts_antes:
        return []
    antes = ruts_antes.get(sec) or []
    return sorted(set(antes) - set(presentes))


def publicar_sector(sec: str, datos: dict, previo: dict, listas: dict, control: dict,
                    periodo: str) -> tuple[dict, list[str], list[str]]:
    """Publica un sector de un trimestre, o conserva lo ya publicado si la relectura empeora.

    Devuelve `(resumen, ruts, avisos)`. La guarda mira **entidades y filas por tabla**: una
    relectura que trae las mismas sociedades pero pierde las filas de una de las dos tablas
    (p. ej. un cambio de glosas que manda todo al `avisos`) no puede sobrescribir el trimestre
    con una tabla vacía, que es lo que borraría el dato del Parquet publicado sin avisar.
    """
    avisos: list[str] = []
    ents = sorted({f["rut"] for t in TABLAS for f in datos[sec][t]})
    antes = previo.get(sec, {}).get("entidades", 0)
    filas_antes = previo.get(sec, {}).get("filas", {}) or {}
    pierde = [t for t in TABLAS if len(datos[sec][t]) < int(filas_antes.get(t, 0) or 0)]
    if len(ents) < antes or pierde:
        avisos.append(
            f"{sec}: la relectura trae {len(ents)} entidades (antes {antes})"
            + (f" y pierde filas en {', '.join(pierde)}" if pierde else "")
            + "; se mantiene lo anterior")
        # Si se conserva lo publicado, se conserva también el conjunto de RUT: registrar los
        # de la relectura haría aparecer como «dejaron de informar» a entidades que siguen
        # estando en los Parquet.
        return previo[sec], (control["periodos"].get(periodo, {}).get("ruts") or {}).get(sec, ents), avisos
    for tabla in TABLAS:
        escribir(sec, tabla, periodo, datos[sec][tabla])
    fuera = sorted({(f["rut_dv"], f["razon_social"]) for t in TABLAS for f in datos[sec][t]
                    if not f["en_lista_entidades"]})
    if len(fuera) > MAX_FUERA_DE_LISTA:
        avisos.append(f"{sec}: {len(fuera)} entidades entran solo por su nombre")
        print(f"::warning::{sec}: {len(fuera)} sociedades calzan con el patrón del nombre "
              f"y no están en la lista de entidades (más de {MAX_FUERA_DE_LISTA} sugiere un "
              f"patrón demasiado amplio); se publican con en_lista_entidades = false")
    # Cobertura silenciosa: quién falta y quién dejó de informar. Sin esto, una entidad que
    # desaparece del archivo no se nota hasta que alguien la busca.
    sin_datos = sorted(set(listas[sec]) - set(ents))
    resumen = {"entidades": len(ents),
               "filas": {t: len(datos[sec][t]) for t in TABLAS},
               "lista_sin_datos": len(sin_datos),
               "lista_total": len(listas[sec]),
               "dejaron_de_informar": dejaron_de_informar(control, periodo, sec, set(ents)),
               "fuera_de_lista": [{"rut": r, "razon_social": n} for r, n in fuera]}
    if resumen["dejaron_de_informar"]:
        avisos.append(f"{sec}: dejaron de informar {', '.join(resumen['dejaron_de_informar'][:5])}")
        for e in resumen["dejaron_de_informar"]:
            print(f"::notice::{sec}: {e} informaba hasta el trimestre anterior y no aparece en {periodo}")
    if sin_datos:
        print(f"::notice::{sec}: {len(sin_datos)} de {len(listas[sec])} entidades de la lista "
              f"no informan en {periodo}")
    return resumen, ents, avisos


def _indice(periodo: str) -> int:
    """Orden natural de un trimestre 'AAAA-MM' (para comparar y restar trimestres)."""
    return int(periodo[:4]) * 4 + (int(periodo[5:]) - 1) // 3


def _periodo(indice: int) -> str:
    return f"{indice // 4}-{indice % 4 * 3 + 3:02d}"


def ultimo_periodo_por_rut(sec: str, tabla: str = "balance") -> tuple[dict[str, str], dict[str, str]]:
    """Último trimestre publicado de cada RUT, y el nombre con que se publicó.

    Se leen solo tres columnas de todos los años: es la forma más barata de saber quién
    dejó de informar sin depender de la memoria del pipeline (un `control.json` viejo no
    trae el historial de RUT y, si se pierde, esta información se reconstruye completa).
    """
    ultimos: dict[str, str] = {}
    nombres: dict[str, str] = {}
    for ruta in sorted(ruta_tabla(sec, tabla).glob("*.parquet")):
        t = pq.read_table(ruta, columns=["periodo", "rut", "razon_social"])
        for per, rut, nombre in zip(t.column("periodo").to_pylist(), t.column("rut").to_pylist(),
                                    t.column("razon_social").to_pylist()):
            if not rut:
                continue
            if rut not in ultimos or per > ultimos[rut]:
                ultimos[rut] = per
                nombres[rut] = nombre or ""
    return ultimos, nombres


def cobertura(listas: dict[str, dict[str, str]], max_sin_datos: int = 12) -> dict[str, dict]:
    """Quién informa y quién no en el último trimestre publicado de cada sector.

    La fuente no avisa de las ausencias: una sociedad que se fusiona o deja de enviar su
    archivo simplemente desaparece. Aquí el silencio se convierte en un dato publicado.
    """
    out: dict[str, dict] = {}
    for sec in SECTORES:
        ultimos, nombres = ultimo_periodo_por_rut(sec)
        if not ultimos:
            continue
        per = max(ultimos.values())
        presentes = {r for r, p in ultimos.items() if p == per}
        catalogo = listas.get(sec) or {}
        sin_datos = [{"rut": r, "razon_social": nombres.get(r) or nombre, "ultimo_periodo": ultimos.get(r)}
                     for r, nombre in sorted(catalogo.items()) if r not in presentes]
        # «Dejaron de informar» = venían informando hace poco y ya no. Lo que se fue antes
        # de esa ventana queda como ausencia histórica, no como novedad del trimestre; igual
        # se publica en `sin_datos`, con el último trimestre en que apareció.
        desde = _periodo(_indice(per) - TRIMESTRES_NOVEDAD)
        dejaron = [{"rut": r, "razon_social": nombres.get(r) or catalogo.get(r, ""),
                    "ultimo_periodo": ultimos[r]}
                   for r, p in sorted(ultimos.items(), key=lambda kv: kv[1], reverse=True)
                   if p >= desde and r not in presentes]
        out[sec] = {"ultimo_periodo": per, "entidades": len(presentes), "lista_total": len(catalogo),
                    "sin_datos": sin_datos[:max_sin_datos], "sin_datos_total": len(sin_datos),
                    "dejaron_de_informar": dejaron}
    return out


def texto_cobertura(cob: dict, cuantos: int = 4) -> str:
    """Una frase para la web con la cobertura del último trimestre."""
    if not cob:
        return ""
    partes = [f"Cobertura {cob['ultimo_periodo']}: informan {cob['entidades']} de las "
              f"{cob['lista_total']} entidades del catálogo del sector."]
    if cob["dejaron_de_informar"]:
        nombres = [f"{(d['razon_social'] or d['rut']).strip()} (último {d['ultimo_periodo']})"
                   for d in cob["dejaron_de_informar"][:cuantos]]
        mas = len(cob["dejaron_de_informar"]) - len(nombres)
        partes.append("Dejaron de informar: " + "; ".join(nombres) + (f" y {mas} más." if mas > 0 else "."))
    if cob["sin_datos_total"]:
        muestra = [f["razon_social"] or f["rut"] for f in cob["sin_datos"][:3]]
        partes.append(f"Sin dato en {cob['ultimo_periodo']}: {cob['sin_datos_total']} entidades"
                      + (f" ({', '.join(muestra)}…)" if muestra else "") + ".")
    return " ".join(partes)


def escribir_cobertura_web(cob: dict[str, dict]) -> bool:
    """Escribe la cobertura en las fichas del diccionario de la web; True si algo cambió."""
    lineas = RUTA_DICCIONARIO.read_text(encoding="utf-8").split("\n")
    ids = {f"{cfg['prefijo']}_{t}": sec for sec, cfg in SECTORES.items() for t in TABLAS}
    cambiado = False
    for i, linea in enumerate(lineas):
        t = linea.strip().rstrip(",")
        if not t.startswith('{"id": "') or not t.endswith("}"):
            continue
        try:
            obj = json.loads(t)
        except ValueError:
            continue
        sec = ids.get(obj.get("id"))
        if sec is None or sec not in cob:
            continue
        texto = texto_cobertura(cob[sec])
        if obj.get("cobertura") == texto:
            continue
        obj["cobertura"] = texto
        lineas[i] = "  " + json.dumps(obj, ensure_ascii=False) + ","
        cambiado = True
    if cambiado:
        RUTA_DICCIONARIO.write_text("\n".join(lineas), encoding="utf-8")
    return cambiado


def escribir_manifiestos(control: dict, coberturas: dict | None = None) -> None:
    periodos = sorted(control["periodos"])
    for sec, cfg in SECTORES.items():
        for tabla in TABLAS:
            carpeta = ruta_tabla(sec, tabla)
            carpeta.mkdir(parents=True, exist_ok=True)
            rutas = sorted(carpeta.glob("*.parquet"))
            con = [p for p in periodos if control["periodos"][p]["sectores"][sec]["entidades"]]
            man = {"tabla": f"{cfg['prefijo']}_{tabla}",
                   "files": [f"outputs/{cfg['carpeta']}/{carpeta.name}/{r.name}" for r in rutas],
                   "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas),
                   "periodos": [f"{p[:4]}-{p[4:]}" for p in con],
                   "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            # Cobertura del último trimestre: quién informa, quién falta y quién se fue.
            # Viaja con los datos para que cualquier descarga sepa qué le falta.
            if coberturas and sec in coberturas:
                man["cobertura"] = coberturas[sec]
            estable.escribir_json((carpeta / "manifest.json"), man)


def cargar_control() -> dict:
    return json.loads(CONTROL.read_text()) if CONTROL.exists() else {"periodos": {}}


def guardar_control(control: dict) -> None:
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    control["periodos"] = dict(sorted(control["periodos"].items()))
    control["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estable.escribir_json(CONTROL, control)


ORIGEN = ("CMF — Estados financieros bajo estándar IFRS (TXT trimestral con todas las sociedades que envían "
          "estados financieros XBRL): https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php")
DESCRIPCION = {
    "balance": "Estado de situación financiera (ESF) de cada {q}, cuenta por cuenta, tal como lo publica la CMF. "
               "Montos en unidades de la moneda informada (CLP o USD), sin conversión.",
    "resultados": "Estado de resultados (ER, por función o naturaleza e integral) de cada {q}, cuenta por cuenta. "
                  "Montos acumulados del ejercicio a la fecha del trimestre, en unidades de la moneda informada.",
}
QUIEN = {"agf": "administradora general de fondos", "securitizadoras": "sociedad securitizadora",
         "cajas_compensacion": "caja de compensación de asignación familiar"}


def actualizar_data_manifest(control: dict) -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    hoy = date.today().isoformat()
    nuevas = []
    for sec, cfg in SECTORES.items():
        for tabla in TABLAS:
            carpeta = ruta_tabla(sec, tabla)
            m = carpeta / "manifest.json"
            if not m.exists():
                continue
            mm = json.loads(m.read_text())
            per = mm["periodos"]
            vista = f"{cfg['prefijo']}_{tabla}"
            nuevas.append({
                "id": vista, "name": f"{cfg['prefijo']}.{tabla}", "view_name": vista, "sector": sec,
                "sector_label": cfg["etiqueta"], "norma": "IFRS · archivo TXT de estados financieros CMF",
                "corte": f"{per[0]} a {per[-1]}" if per else "sin trimestres",
                "frescura": f"Último trimestre publicado: {per[-1]}" if per else "",
                "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
                "file_parquet": f"outputs/{cfg['carpeta']}/{carpeta.name}/manifest.json",
                "registros_reales": mm["total_records"],
                "descripcion": DESCRIPCION[tabla].format(q=QUIEN[sec]), "origen": ORIGEN,
            })
    ids = {e["id"] for e in nuevas} | {"securitizadoras_balance_resumen", "ccaf_caratula_totales"}
    man["tables"] = [t for t in man["tables"] if t["id"] not in ids] + nuevas
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    estable.escribir_json(ruta, man)


def guardar_lista(rel: str, filas: list[dict]) -> None:
    js = DOCS / rel
    js.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pqt = js.with_suffix(".parquet")
    if pqt.exists():
        esquema = pq.read_schema(pqt)
        df = pd.DataFrame(filas).reindex(columns=esquema.names)
        for campo in esquema:
            if pa.types.is_integer(campo.type):
                df[campo.name] = pd.to_numeric(df[campo.name], errors="coerce").astype("Int64")
            elif pa.types.is_boolean(campo.type):
                df[campo.name] = df[campo.name].fillna(False).astype(bool)
        pq.write_table(pa.Table.from_pandas(df, schema=esquema.remove_metadata(), preserve_index=False), pqt)


def agregar_altas(fuera: dict[str, list[dict]], periodo: str) -> int:
    """Agrega a la lista las sociedades del último trimestre que calzan con el giro y no están."""
    eventos = []
    for s, lst in fuera.items():
        cfg = SECTORES.get(s) or SOLO_LISTA.get(s)
        if not cfg or "alta" not in cfg or not lst:
            continue
        filas = json.loads((DOCS / cfg["lista"]).read_text(encoding="utf-8"))
        ya = {str(f[cfg["clave_rut"]]).replace(".", "").split("-")[0] for f in filas}
        columnas = list(filas[0].keys())
        pendientes = [e for e in lst if e["rut"].split("-")[0] not in ya]
        if len(pendientes) > MAX_ALTAS:
            print(f"::warning::{s}: {len(pendientes)} sociedades calzan con el giro y no están en la lista; "
                  f"más de {MAX_ALTAS} en una corrida sugiere un patrón demasiado amplio: no se agrega ninguna")
            continue
        for e in lst:
            c, d = e["rut"].split("-")
            if c in ya or not c.isdigit():
                continue
            alta = cfg["alta"](c, d, e["razon_social"])
            filas.append({k: alta.get(k) for k in columnas})
            ya.add(c)
            eventos.append({"fecha": date.today().isoformat(), "sector": s, "lista": cfg["lista"].removesuffix(".json"),
                            "rut": e["rut"], "razon_social": e["razon_social"], "evento": "alta",
                            "antes": None, "ahora": f"reporta IFRS en {periodo}"})
            print(f"::notice::{s}: alta {e['rut']} {e['razon_social']} (reporta IFRS en {periodo})")
        if any(ev["sector"] == s for ev in eventos):
            guardar_lista(cfg["lista"], filas)
    if eventos:
        NOVEDADES.parent.mkdir(parents=True, exist_ok=True)
        hist = json.loads(NOVEDADES.read_text()) if NOVEDADES.exists() else {"eventos": []}
        hist["eventos"] = hist["eventos"] + eventos
        NOVEDADES.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n")
    return len(eventos)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--minutos", type=float, default=40)
    ap.add_argument("--max-periodos", type=int, default=200)
    ap.add_argument("--solo-data-manifest", action="store_true")
    a = ap.parse_args(argv)
    control = cargar_control()
    if a.solo_data_manifest:
        actualizar_data_manifest(control)
        return 0
    inicio = time.monotonic()
    hoy = date.today()
    listas = cargar_listas()
    indice = _get(INDICE)
    periodos, anual = periodos_indice(indice)
    pendientes = [p for p in periodos if p not in control["periodos"] or not control["periodos"][p].get("cerrado")]
    print(f"Índice CMF: {len(periodos)} trimestres ({periodos[0]}..{periodos[-1]}). "
          f"Procesados y cerrados: {len(periodos) - len(pendientes)}. A leer ahora: {len(pendientes)}")
    cache_anual: dict[tuple, bytes] = {}
    hechos, errores, defectos = 0, [], []
    for periodo in pendientes[:a.max_periodos]:
        if time.monotonic() - inicio > a.minutos * 60:
            print(f"Tiempo agotado ({a.minutos:.0f} min); el resto sigue en la próxima corrida.")
            break
        url = ARCHIVO.format(periodo, periodo)
        try:
            try:
                raw = _get(url)
                datos, est, avisos = leer_archivo(raw, periodo, listas)
            except ErrorFuente as e:
                if periodo not in anual:
                    raise
                par = anual[periodo]
                url = ARCHIVO.format(*par)
                if par not in cache_anual:
                    cache_anual[par] = _get(url)
                raw = cache_anual[par]
                datos, est, avisos = leer_archivo(raw, periodo, listas)
                avisos.insert(0, f"trimestre leído del archivo anual ({e})")
        except ErrorContenido as e:
            if cerrado(periodo, hoy):
                # Trimestre histórico cerrado cuyo archivo de la CMF trae contenido incompleto
                # (p. ej. 201003 con solo 4 sociedades): no se publica, se reintenta ante cada
                # cambio de la fuente y no debe dejar la corrida en rojo cuando no hay nada
                # nuevo que publicar.
                defectos.append(f"{periodo}: {e}")
                print(f"::warning::{periodo}: {e} — archivo histórico incompleto; no publica "
                      f"ni falla la corrida")
                continue
            errores.append(f"{periodo}: {e}")
            print(f"::warning::{periodo}: {e}")
            continue
        except ErrorFuente as e:
            errores.append(f"{periodo}: {e}")
            print(f"::warning::{periodo}: {e}")
            continue
        # Misma fuente que la última lectura: no hay nada nuevo que escribir ni desplegar. Los
        # trimestres abiertos se releen en cada corrida (la CMF reenvía cifras hasta ~150 días), pero
        # casi siempre el TXT es idéntico; solo se registra si el trimestre pasó a cerrado.
        sha = hashlib.sha256(raw).hexdigest()
        anterior = control["periodos"].get(periodo)
        if anterior and anterior.get("sha256") == sha:
            ahora_cerrado = cerrado(periodo, hoy)
            if anterior.get("cerrado") != ahora_cerrado:
                anterior["cerrado"] = ahora_cerrado
                guardar_control(control)
            print(f"{periodo}: sin cambios en la fuente")
            continue
        # Cuadratura contable (README §4): activos = pasivos + patrimonio sobre el balance, y
        # dos identidades del estado de resultados (el resultado integral arrastra la misma
        # ganancia del ejercicio, y ganancia bruta = ingresos − costo de ventas).
        # Un caso aislado queda como aviso; si la lectura falla en bloque (≥3 y más del 5 %),
        # o si de pronto casi ningún balance trae los tres totales conocidos —señal de que
        # cambiaron las glosas y la compuerta se quedó ciega—, el trimestre no se publica.
        verificados, descuadres, balances_totales = 0, [], 0
        verificaciones, divergencias = 0, []
        for sec in SECTORES:
            filas_balance = datos[sec]["balance"]
            balances_totales += cuadratura.contar_grupos(filas_balance, cuadratura.CLAVES_IFRS)
            v, malos = cuadratura.verificar_ifrs(filas_balance)
            verificados += v
            descuadres += [f"{sec} {m}" for m in malos]
            vr, mr = cuadratura.verificar_resultados_ifrs(datos[sec]["resultados"])
            verificaciones += vr
            divergencias += [f"{sec} {m}" for m in mr]
        motivo = cuadratura.motivo_detener(verificados, descuadres, balances_totales)
        if motivo:
            errores.append(f"{periodo}: {motivo}")
            print(f"::warning::{periodo}: {motivo}; no se publica")
            continue
        motivo_res = cuadratura.motivo_detener(verificaciones, divergencias)
        if motivo_res:
            errores.append(f"{periodo}: estado de resultados · {motivo_res}")
            print(f"::warning::{periodo}: {len(divergencias)} de {verificaciones} identidades del "
                  f"estado de resultados no se cumplen; no se publica. Ej.: {divergencias[0]}")
            continue
        avisos += [f"balance no cuadra: {m}" for m in descuadres]
        avisos += [f"resultados: {m}" for m in divergencias[:10]]
        est["balances_verificados"], est["balances_descuadrados"] = verificados, len(descuadres)
        est["balances_totales"] = balances_totales
        est["resultados_verificaciones"] = verificaciones
        est["resultados_divergencias"] = len(divergencias)
        previo = control["periodos"].get(periodo, {}).get("sectores", {})
        resumen = {}
        ruts_periodo = {}
        for sec in SECTORES:
            resumen[sec], ruts_periodo[sec], avisos_sec = publicar_sector(
                sec, datos, previo, listas, control, periodo)
            avisos += avisos_sec
        control["periodos"][periodo] = {
            "cerrado": cerrado(periodo, hoy), "leido_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fuente": url, "sha256": sha, **est,
            "sectores": resumen, "avisos": avisos[:20],
            # RUT por sector: la comparación del trimestre siguiente (dejaron_de_informar)
            # necesita los nombres, no solo la cantidad.
            "ruts": ruts_periodo,
        }
        guardar_control(control)
        hechos += 1
        print(f"{periodo}: {est['sociedades']} sociedades · " +
              " · ".join(f"{s} {r['entidades']} ent. ({r['filas']['balance']}+{r['filas']['resultados']} filas)"
                         for s, r in resumen.items()) + (f" · {len(avisos)} avisos" if avisos else ""))
    hechos += refrescar_marcas(listas, control)
    # Entidades del giro presentes en el último trimestre que no están en la lista: las CCAF y
    # factoring/leasing se agregan solas; AGF y securitizadoras entran por el registro CMF
    # (pipelines/entidades), aquí solo se avisan.
    if control["periodos"]:
        ult = max(control["periodos"])
        fuera = {s: r.get("fuera_de_lista", []) for s, r in control["periodos"][ult]["sectores"].items()}
        fuera.update(control["periodos"][ult].get("solo_lista_fuera", {}))
        if agregar_altas(fuera, ult):
            listas = cargar_listas()
            hechos += 1 + refrescar_marcas(listas, control)
        nuevas = {s: r.get("fuera_de_lista", []) for s, r in control["periodos"][ult]["sectores"].items()}
        control["entidades_fuera_de_lista_ultimo_trimestre"] = {"periodo": ult, **nuevas}
        for s, lst in nuevas.items():
            for e in lst:
                print(f"::notice::{s}: {e['rut']} {e['razon_social']} reporta en {ult} y no está en la lista de entidades")
        guardar_control(control)
    cobs = cobertura(listas)
    escribir_manifiestos(control, cobs)
    if escribir_cobertura_web(cobs):
        print("Cobertura publicada en el diccionario de la web")
    actualizar_data_manifest(control)
    print(f"Trimestres leídos en esta corrida: {hechos}. Errores: {len(errores)}"
          + (f" · archivos históricos incompletos: {len(defectos)}" if defectos else ""))
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"publicados={hechos}\n")
    return 1 if errores and not hechos else 0


if __name__ == "__main__":
    sys.exit(main())
