"""Actualiza la cartera de inversiones de las compañías de seguros (CMF, Circular 1835).

Incremental: solo descarga los meses que faltan en docs/outputs/seguros/manifest.json.
Para cada mes baja el ZIP de vida y el de generales, lee cada archivo con las posiciones
oficiales (formato_1835.py) y valida antes de escribir nada:

  - cada línea tiene el largo exacto de la ficha técnica,
  - el período del encabezado es el mes pedido,
  - el registro de totales cuenta exactamente las líneas de detalle,
  - todos los campos numéricos y fechas se pueden leer.

Si algo falla, el mes no se publica y la corrida termina con error (fail-closed). Excepción: un
archivo defectuoso de UNA compañía (p. ej. a202505g.99017000 con una línea truncada) se excluye solo
a él, con aviso y registro en el manifiesto; si hay más de 2 archivos así y más del 5 % de los del
sector, se asume una lectura mal hecha y el mes no se publica.
Si el mes todavía no está en la CMF, la corrida termina sin cambios.

Salida (un archivo por tabla y año, así la web carga pocos archivos):
  docs/outputs/seguros/<tabla>/<año>.parquet
  docs/outputs/seguros/<tabla>/manifest.json   (lista de archivos, la usa la web)
  docs/outputs/seguros/aseguradoras.parquet    (compañías que reportan, con su primer y último mes)
  docs/outputs/seguros/manifest.json           (meses publicados y conteos)

Uso:
  python -m seguros.scripts.actualizar_carteras                      # meses pendientes
  python -m seguros.scripts.actualizar_carteras --max-periodos 12
  python -m seguros.scripts.actualizar_carteras --zip-dir carpeta/   # ZIP locales (pruebas)
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
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pipelines.auto import rut as rutmod
from pipelines.auto.rut import normalizar_dataframe
from pipelines.auto import privacidad
from seguros.scripts import metadatos_web
from seguros.scripts.vistas_1835 import RESUMENES_RELEVANTES
from seguros.scripts.formato_1835 import ENCABEZADO, LARGO, TIPO_TOTAL, campos, formato_de

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import estable  # noqa: E402
SALIDA = RAIZ / "docs" / "outputs" / "seguros"
URL = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
SECTORES = {"vida": "CSVID", "generales": "CSGEN"}
TABLAS = [
    # Registros, en el orden del manual Circular 1835, sección B.
    "renta_fija", "acciones", "fondos_mutuos", "bienes_raices", "extranjeros", "otras_inversiones",
    "derivados", "pactos", "control_inversiones", "tablas_descriptores", "tablas_desarrollo",
    "flujos_activos_elegibles", "prestamos", "bienes_raices_arriendo_morosidad", "garantias_derivados",
] + [config[0] for config in RESUMENES_RELEVANTES.values()]
# Primer mes publicado por tabla. La ficha "v2016" es la más antigua que tenemos; si un mes
# anterior no la cumple, la validación lo rechaza. Renta fija y bienes raíces pesan ~5 MB por
# mes (detalle por instrumento), por eso parten más tarde. Para extender una tabla basta con
# cambiar su fecha aquí: la próxima corrida completa solo lo que falta de esa tabla.
DESDE = "2016-11"
DESDE_TABLA = {"renta_fija": "2024-12", "bienes_raices": "2024-12",
               # Los registros que el anexo 2024 agregó no existen en el formato anterior.
               "otras_inversiones": "2024-12", "tablas_descriptores": "2024-12",
               "tablas_desarrollo": "2024-12", "flujos_activos_elegibles": "2024-12",
               "prestamos": "2024-12", "bienes_raices_arriendo_morosidad": "2024-12",
               "garantias_derivados": "2024-12"}
for _base, (_resumen, _titulo, _columnas) in RESUMENES_RELEVANTES.items():
    if _base in DESDE_TABLA:
        DESDE_TABLA[_resumen] = DESDE_TABLA[_base]
# Tablas grandes: un archivo por mes (se escribe una vez). Resto: un archivo por año.
POR_MES = {"renta_fija", "bienes_raices"}
# Orden dentro de cada archivo: el mismo instrumento queda en filas contiguas y comprime mejor.
ORDEN = {"renta_fija": ["tipo_instrumento", "nemotecnico", "serie", "fecha_compra"],
         "acciones": ["nemotecnico"], "fondos_mutuos": ["nemotecnico"],
         # bienes raíces ordena por property_id: el rol no se publica (privacidad).
         "bienes_raices": ["property_id"],
         "extranjeros": ["tipo_registro", "codigo_individualizacion_o_nemotecnico"],
         "derivados": ["tipo_registro", "folio_operacion"], "pactos": ["folio_operacion"],
         "control_inversiones": ["tipo_de_inversion"],
         "otras_inversiones": ["tipo_de_activo", "codigo_o_nombre_de_la_inversion"],
         "tablas_descriptores": ["codigo_nemotecnico"],
         "tablas_desarrollo": ["nemotecnico", "nro_cupon"],
         "flujos_activos_elegibles": ["tipo_de_informacion", "tipo_instrumento"],
         "prestamos": ["codigo_prestamo", "rut_deudor"],
         "bienes_raices_arriendo_morosidad": ["tipo_instrumento", "comuna"],
         "garantias_derivados": ["rut_contraparte_nacional", "identificador_garantia"],
         "renta_fija_relevante": ["tipo_instrumento", "nemotecnico", "serie", "fecha_compra"],
         "acciones_relevantes": ["nemotecnico"],
         "bienes_raices_relevantes": ["property_id"],
         "extranjeros_relevantes": ["tipo_registro", "codigo_individualizacion_o_nemotecnico"],
         "derivados_relevantes": ["tipo_registro", "folio_operacion"],
         "prestamos_relevantes": ["codigo_prestamo"],
         "bienes_raices_arriendo_morosidad_relevantes": ["property_id", "comuna"]}
ARCHIVOS = set("iafbxpcodetrvg")


class NoPublicado(Exception):
    pass


class ErrorValidacion(Exception):
    pass


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (monitor-financiero-chile)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def descargar(sector: str, periodo: str, zip_dir: Path | None, cache: Path | None = None) -> bytes:
    yyyymm = periodo.replace("-", "")
    if cache is not None and (cache / f"{SECTORES[sector]}_{yyyymm}.zip").exists():
        return (cache / f"{SECTORES[sector]}_{yyyymm}.zip").read_bytes()
    if zip_dir is not None:
        ruta = zip_dir / f"{SECTORES[sector]}_{yyyymm}.zip"
        if not ruta.exists():
            raise NoPublicado(f"{ruta} no existe")
        return ruta.read_bytes()
    ent = SECTORES[sector]
    for intento in range(1, 4):
        try:
            disp = _get(f"{URL}?tipoentidad={ent}&fnAjax=archi&peri={yyyymm}", 30).decode("latin-1").strip()
            if disp != "1":
                raise NoPublicado(f"{sector} {periodo}: la CMF aún no publica la cartera (archi={disp!r})")
            data = _get(f"{URL}?tipoentidad={ent}&fnAjax=descarga&peri={yyyymm}", 300)
            if not data.startswith(b"PK"):
                raise ErrorValidacion(f"{sector} {periodo}: la descarga no es un ZIP ({len(data)} bytes)")
            if cache is not None:
                cache.mkdir(parents=True, exist_ok=True)
                (cache / f"{ent}_{yyyymm}.zip").write_bytes(data)
            return data
        except (NoPublicado, ErrorValidacion):
            raise
        except Exception as e:  # red: reintentar
            if intento == 3:
                raise
            print(f"  reintento {intento} {sector} {periodo}: {e}")
            time.sleep(10 * intento)
    raise AssertionError


# ---------------------------------------------------------------------------
# Lectura de campos
# ---------------------------------------------------------------------------
def _decodificar(raw: bytes, largo: int) -> str:
    """Algunas compañías graban en UTF-8 y otras en Latin-1: se usa la que da el largo exacto."""
    try:
        s = raw.decode("utf-8")
        if len(s) == largo:
            return s
    except UnicodeDecodeError:
        pass
    return raw.decode("latin-1")


def _valor(txt: str, tipo: str, dec: int):
    if tipo == "t":
        return txt.strip() or None
    if tipo == "f":
        if txt.strip("0 ") == "":
            return None
        if not re.fullmatch(r"\d{8}", txt):
            raise ValueError(f"fecha {txt!r}")
        return f"{txt[:4]}-{txt[4:6]}-{txt[6:]}"
    if tipo == "r":
        cuerpo, dv = txt[:9], txt[9:10].strip().upper()
        if cuerpo.strip("0 ") == "":
            return None
        if not cuerpo.isdigit():
            raise ValueError(f"rut {txt!r}")
        # RUTs de 1 a 3 cifras son placeholders del origen ('1', '1-9'); se publican como cuerpo (C) sin DV
        if int(cuerpo) < 1000:
            return str(int(cuerpo))
        return f"{int(cuerpo)}-{dv}" if dv else str(int(cuerpo))
    # Números: el signo va en el primer carácter, pero algunas compañías lo escriben después de
    # ceros de relleno ("00-15500"); ambas formas se aceptan. Cualquier otro carácter es error.
    m = re.fullmatch(r"([ 0]*)([+-]?)(\d*) *", txt)
    if not m:
        # Algunas compañías escriben el punto decimal ("0379.2"): se toma el valor literal.
        d = re.fullmatch(r" *([+-]?) *(\d*)[.,](\d+) *", txt)
        if not d:
            raise ValueError(f"número {txt!r}")
        v = float(f"{d.group(2) or 0}.{d.group(3)}") * (-1 if d.group(1) == "-" else 1)
        return v if dec else int(round(v))
    if not (m.group(1) + m.group(3)).strip():
        return None
    v = int(m.group(3) or 0) * (-1 if m.group(2) == "-" else 1)
    return v / 10 ** dec if dec else v


def _dv(cuerpo: int) -> str:
    s, m = 0, 2
    for d in reversed(str(cuerpo)):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def _encabezado_desde_nombre(nombre: str):
    m = re.fullmatch(r"[a-z](\d{6,8})[vg]?\.(\d{6,9})", os.path.basename(nombre).lower())
    if not m:
        return None
    f, cuerpo = m.group(1), int(m.group(2))
    periodo = f"20{f[:4]}" if len(f) == 6 else f[:6]  # aammdd (v2016) o aaaamm (v2024)
    return {"rut_aseguradora": f"{cuerpo}-{_dv(cuerpo)}", "nombre_aseguradora": None, "periodo_archivo": periodo}


def leer_archivo(nombre: str, raw: bytes, formato: str, periodo: str, sector: str, mapa: dict, filas: dict,
                 errores: list, compania: dict, avisos: list, ilegibles: dict) -> None:
    letra = os.path.basename(nombre)[:1].lower()
    if letra not in ARCHIVOS:
        return
    largo = LARGO[formato][letra]
    lineas = [ln for ln in raw.split(b"\n") if ln.strip(b"\r\n\x1a ")]
    lineas = [_decodificar(ln.rstrip(b"\r"), largo) for ln in lineas]
    if not lineas:
        return
    malas = [i for i, ln in enumerate(lineas) if len(ln) != largo]
    if malas:
        errores.append(f"{nombre}: {len(malas)} líneas con largo distinto de {largo} "
                       f"(p. ej. línea {malas[0] + 1} con {len(lineas[malas[0]])})")
        return
    h = lineas[0]
    if h[:1] == "1":
        enc = {c: _valor(h[i:i + n], t, d) for c, i, n, t, d in ENCABEZADO}
        cuerpo = lineas[1:]
    else:
        # Algunas compañías omiten el encabezado: RUT y período salen del nombre del archivo
        # (p. ej. a240630v.96549050 o a202412.96549050); el nombre, de sus otros archivos.
        enc = _encabezado_desde_nombre(nombre)
        if enc is None:
            errores.append(f"{nombre}: sin encabezado y el nombre del archivo no trae RUT/período")
            return
        cuerpo = lineas
        avisos.append(f"{sector} {nombre}: sin encabezado (RUT tomado del nombre del archivo)")
    if enc["periodo_archivo"] != periodo.replace("-", ""):
        avisos.append(f"{sector} {nombre}: el encabezado dice {enc['periodo_archivo']} pero la CMF lo publica en {periodo}")
    rut = enc["rut_aseguradora"]
    if enc["nombre_aseguradora"]:
        compania[rut] = enc["nombre_aseguradora"]
    total = TIPO_TOTAL[letra]
    detalle = [ln for ln in cuerpo if ln[:1] != total]
    totales = [ln for ln in cuerpo if ln[:1] == total]
    # El registro de totales debería contar las líneas del archivo. Lo llena cada compañía y no
    # siempre cuadra: se deja como aviso (el dato publicado es el que la CMF entrega).
    if len(totales) != 1:
        avisos.append(f"{sector} {nombre}: {len(totales)} registros de totales")
    else:
        declarado = int(totales[0][1:7]) if totales[0][1:7].isdigit() else -1
        if declarado not in (len(lineas), len(detalle)):
            avisos.append(f"{sector} {nombre}: el total declara {declarado} líneas y el archivo tiene {len(lineas)}")
    for n, ln in enumerate(detalle, start=2):
        clave = (letra, ln[:1])
        if clave not in mapa:
            esperado = LARGO[formato][letra]
            errores.append(f"{nombre}: tipo de registro {ln[:1]!r} desconocido (línea {n}; "
                           f"largo {len(ln)}, esperado {esperado})")
            return
        tabla, subtipo, cols = mapa[clave]
        fila = {"periodo": periodo, "sector": sector, "rut_aseguradora": rut,
                "nombre_aseguradora": enc["nombre_aseguradora"]}
        if subtipo:
            fila["tipo_registro"] = subtipo
        malo = None
        for c, i, largo_c, t, d in cols:
            try:
                fila[c] = _valor(ln[i:i + largo_c], t, d)
            except ValueError as e:
                fila[c] = None
                malo = malo or f"{c} ({e})"
        if malo:
            ilegibles.setdefault(tabla, []).append(f"{sector} {nombre} línea {n}: {malo}")
        filas[tabla].append(fila)


def leer_zip(data: bytes, periodo: str, sector: str):
    formato = formato_de(periodo)
    mapa = campos(formato)
    filas = {t: [] for t in TABLAS}
    errores: list[str] = []
    avisos: list[str] = []
    ilegibles: dict[str, list[str]] = {}
    compania: dict[str, str] = {}
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise ErrorValidacion(f"{sector} {periodo}: ZIP inválido ({e})")
    excluidos: list[str] = []
    leidos = 0
    for nombre in sorted(z.namelist()):
        if nombre.endswith("/"):
            continue
        # Cada archivo se lee aparte: un archivo defectuoso de UNA compañía (línea truncada, tipo
        # de registro inválido) se excluye solo a él y el resto del mes se publica.
        propias = {t: [] for t in TABLAS}
        errs: list[str] = []
        ileg: dict[str, list[str]] = {}
        leer_archivo(nombre, z.read(nombre), formato, periodo, sector, mapa, propias, errs, compania, avisos, ileg)
        if os.path.basename(nombre)[:1].lower() in ARCHIVOS:
            leidos += 1
        if errs:
            excluidos += errs
            continue
        for t in TABLAS:
            filas[t].extend(propias[t])
        for t, lista in ileg.items():
            ilegibles.setdefault(t, []).extend(lista)
    # Tope: muchos archivos defectuosos a la vez indican una lectura mal hecha (no errores de las
    # compañías), así que el mes no se publica.
    if len(excluidos) > max(2, 0.05 * leidos):
        errores += [f"{len(excluidos)} de {leidos} archivos con problemas (tope: 2 o 5 %)"] + excluidos
    else:
        avisos += [f"{sector} ARCHIVO EXCLUIDO · {x}" for x in excluidos]
    for t in TABLAS:  # filas de archivos sin encabezado: nombre de la compañía desde sus otros archivos
        for fila in filas[t]:
            if fila["nombre_aseguradora"] is None:
                fila["nombre_aseguradora"] = compania.get(fila["rut_aseguradora"])
    # Doble reporte: la misma compañía trae dos valores distintos para el mismo tipo_inversion en
    # el mes (pasa en fusiones: la CMF publica los archivos C de ambas sociedades). Se publica
    # tal cual (es la fuente), pero se avisa: las agregaciones por compañía-mes suman ambos.
    valores: dict[tuple, set] = {}
    for fila in filas["control_inversiones"]:
        valores.setdefault((fila["rut_aseguradora"], fila["tipo_de_inversion"]), set()).add(fila["valor_final_m_clp"])
    for (rut, tipo), vals in sorted(valores.items()):
        if len(vals) > 1:
            avisos.append(f"{sector} {rut}: {len(vals)} valores distintos para tipo_de_inversion {tipo} "
                          f"(doble reporte de control en el mes)")
    # Campos ilegibles: quedan vacíos y se avisan; si superan el 1 % de las filas de una tabla,
    # lo más probable es que la lectura esté corrida y el mes no se publica.
    for tabla, lista in ilegibles.items():
        if len(lista) > max(0.01 * len(filas[tabla]), 0):
            errores += [f"{tabla}: {len(lista)} de {len(filas[tabla])} filas con campos ilegibles (más del 1 %)"] + lista[:10]
        else:
            avisos += [f"{tabla}: campo ilegible, queda vacío · {x}" for x in lista]
    if errores:
        raise ErrorValidacion(f"{sector} {periodo} ({formato}): {len(errores)} problemas:\n  - " +
                              "\n  - ".join(errores[:20]))
    if not compania:
        raise ErrorValidacion(f"{sector} {periodo}: el ZIP no trae archivos de cartera")
    if not filas["control_inversiones"]:
        raise ErrorValidacion(f"{sector} {periodo}: falta la información de control (archivos C)")
    return filas, compania, avisos, excluidos


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------
_ESQUEMAS: dict = {}


def _tipo_arrow(tipo: str, decimales: int) -> pa.DataType:
    return pa.string() if tipo in "tfr" else pa.float64() if decimales else pa.int64()


def _mas_ancho(a: pa.DataType | None, b: pa.DataType) -> pa.DataType:
    if a is None or a == b:
        return b
    if pa.types.is_string(a) or pa.types.is_string(b):
        return pa.string()
    if pa.types.is_floating(a) or pa.types.is_floating(b):
        return pa.float64()
    return pa.int64()


def esquema(tabla: str) -> pa.Schema:
    """Esquema fijo de una tabla completa o de su proyección analítica derivada."""
    if tabla not in _ESQUEMAS:
        origen_resumen = next((base for base, cfg in RESUMENES_RELEVANTES.items()
                               if cfg[0] == tabla), None)
        if origen_resumen:
            esquema_base = esquema(origen_resumen)
            columnas = RESUMENES_RELEVANTES[origen_resumen][2]
            faltan = [c for c in columnas if c not in esquema_base.names]
            if faltan:
                raise ValueError(f"{tabla}: columnas relevantes ausentes en {origen_resumen}: {faltan}")
            _ESQUEMAS[tabla] = pa.schema([esquema_base.field(c) for c in columnas])
            return _ESQUEMAS[tabla]
        cols = {"periodo": pa.string(), "sector": pa.string(), "rut_aseguradora": pa.string(),
                "nombre_aseguradora": pa.string()}
        for formato in ("v2016", "v2024"):
            for t, subtipo, campos_ in campos(formato).values():
                if t != tabla:
                    continue
                if subtipo:
                    cols.setdefault("tipo_registro", pa.string())
                for c, _, _, tipo, dec in campos_:
                    # Un mismo nombre puede declararse distinto en dos subtipos (p. ej. con y sin
                    # decimales): gana el tipo más ancho para que ningún mes quede fuera del
                    # esquema. Los nombres con sentidos distintos (texto vs número) se separan
                    # en el inventario, no aquí.
                    cols[c] = _mas_ancho(cols.get(c), _tipo_arrow(tipo, dec))
        if tabla in {"bienes_raices", "bienes_raices_arriendo_morosidad"}:
            # Rol y dirección se suprimen; el seudónimo permite seguimiento longitudinal.
            cols["property_id"] = pa.string()
        if tabla == "garantias_derivados":
            cols["contraparte_tipo"] = pa.string()
        _ESQUEMAS[tabla] = pa.schema(list(cols.items()))
    return _ESQUEMAS[tabla]


def _tabla_arrow(df: pd.DataFrame) -> pa.Table:
    return pa.Table.from_pandas(df, preserve_index=False)


def tablas_de(periodo: str) -> list[str]:
    return [t for t in TABLAS if periodo >= DESDE_TABLA.get(t, DESDE)]


def ruta_particion(tabla: str, periodo: str) -> Path:
    return SALIDA / tabla / (f"{periodo}.parquet" if tabla in POR_MES else f"{periodo[:4]}.parquet")


def _proteger_tabla(tabla: str, df: pd.DataFrame) -> pd.DataFrame:
    """Aplica privacidad a la tabla completa antes de escribir o proyectar."""
    if tabla == "bienes_raices":
        return privacidad.proteger_bienes_raices(df)
    if tabla == "prestamos":
        return privacidad.proteger_prestamos(df)
    if tabla == "bienes_raices_arriendo_morosidad":
        return privacidad.proteger_bienes_raices_arriendo(df)
    if tabla == "garantias_derivados":
        return privacidad.proteger_contrapartes(df)
    return df


def backfill_vistas_existentes(control: dict, escribir: bool = True) -> set[tuple[str, str]]:
    """Deriva vistas desde Parquet completos ya publicados, sin volver a bajar ZIP históricos.

    La fuente publicada ya pasó por privacidad; se proyectan sus filas intactas. Las vistas de
    B.12 y B.13 cuyo origen aún no está publicado se completan junto con el ZIP mensual.
    """
    cache_particiones: dict[Path, pd.DataFrame] = {}
    derivables: set[tuple[str, str]] = set()
    for base, (resumen, _titulo, columnas) in RESUMENES_RELEVANTES.items():
        for periodo, info in sorted(control["periodos"].items()):
            registros = info.setdefault("registros", {})
            if resumen in registros or base not in registros or periodo < DESDE_TABLA.get(resumen, DESDE):
                continue
            origen = ruta_particion(base, periodo)
            if not origen.exists():
                continue
            derivables.add((periodo, resumen))
            if not escribir:
                continue
            if origen not in cache_particiones:
                cache_particiones[origen] = pq.read_table(origen).to_pandas()
            fuente = cache_particiones[origen]
            filas_mes = fuente[fuente["periodo"].astype(str) == periodo].reindex(columns=columnas)
            registros[resumen] = len(filas_mes)
            if not len(filas_mes):
                continue
            destino = ruta_particion(resumen, periodo)
            destino.parent.mkdir(parents=True, exist_ok=True)
            partes = []
            if destino.exists():
                previo = pq.read_table(destino).to_pandas()
                partes.append(previo[previo["periodo"] != periodo])
            partes.append(filas_mes)
            df = pd.concat([x for x in partes if len(x)], ignore_index=True)
            df = df.reindex(columns=esquema(resumen).names)
            orden = ["sector", "rut_aseguradora"] + [c for c in ORDEN.get(resumen, []) if c in df.columns] + ["periodo"]
            df = normalizar_dataframe(df.sort_values(orden, kind="stable", na_position="first"))
            tmp = destino.with_suffix(".tmp")
            pq.write_table(pa.Table.from_pandas(df, schema=esquema(resumen), preserve_index=False), tmp,
                           compression="zstd", compression_level=9)
            os.replace(tmp, destino)
    if escribir and derivables:
        guardar_control(control)
        escribir_manifiestos(control)
        actualizar_data_manifest(control)
    return derivables


def escribir_periodo(periodo: str, filas: dict, tablas: list[str]) -> dict:
    """Escribe el mes en el archivo de cada tabla (si el mes ya estaba en ese archivo, lo reemplaza)."""
    conteo = {}
    fuentes_resumen = {config[0]: (base, config[2]) for base, config in RESUMENES_RELEVANTES.items()}
    for tabla in tablas:
        ruta = ruta_particion(tabla, periodo)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if tabla in fuentes_resumen:
            fuente, columnas = fuentes_resumen[tabla]
            nuevo = pd.DataFrame(filas[fuente])
        else:
            fuente, columnas = tabla, None
            nuevo = pd.DataFrame(filas[tabla])
        # Aplicar las reglas de privacidad tanto a los archivos completos como a su derivado
        # reducido, antes de seleccionar columnas, para no publicar PII en una variante.
        nuevo = _proteger_tabla(fuente, nuevo)
        if columnas:
            nuevo = nuevo.reindex(columns=columnas)
        conteo[tabla] = len(nuevo)
        partes = []
        if ruta.exists():
            viejo = pq.read_table(ruta).to_pandas()
            partes.append(viejo[viejo["periodo"] != periodo])
        if len(nuevo):
            partes.append(nuevo)
        partes = [p for p in partes if len(p)]
        if not partes:
            continue
        df = pd.concat(partes, ignore_index=True).reindex(columns=esquema(tabla).names)
        orden = ["sector", "rut_aseguradora"] + [c for c in ORDEN.get(tabla, []) if c in df.columns] + ["periodo"]
        df = df.sort_values(orden, kind="stable", na_position="first")
        df = normalizar_dataframe(df)  # convención de RUT (pipelines/auto/rut.py)
        tmp = ruta.with_suffix(".tmp")
        pq.write_table(pa.Table.from_pandas(df, schema=esquema(tabla), preserve_index=False), tmp,
                       compression="zstd", compression_level=9)
        os.replace(tmp, ruta)
    return conteo


def escribir_manifiestos(control: dict) -> None:
    for tabla in TABLAS:
        (SALIDA / tabla).mkdir(parents=True, exist_ok=True)
        rutas = sorted((SALIDA / tabla).glob("*.parquet"))
        registros = sum(pq.ParquetFile(r).metadata.num_rows for r in rutas)
        periodos = sorted(p for p, v in control["periodos"].items() if tabla in v.get("registros", {}))
        man = {"tabla": tabla, "files": [f"outputs/seguros/{tabla}/{r.name}" for r in rutas],
               "total_records": registros, "periodos": periodos,
               "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        estable.escribir_json((SALIDA / tabla / "manifest.json"), man)
    # Compañías que reportan: primer y último mes por sector.
    filas = []
    for (sector, rut), info in sorted(control["aseguradoras"].items()):
        filas.append({"sector": sector, "rut_aseguradora": rut, "nombre_aseguradora": info["nombre"],
                      "primer_periodo": info["primer"], "ultimo_periodo": info["ultimo"],
                      "meses_reportados": info["meses"]})
    df = pd.DataFrame(filas)
    if len(df):
        ultimo = max(control["periodos"])
        df["reporta_ultimo_mes"] = df["ultimo_periodo"] == ultimo
        df = normalizar_dataframe(df)  # convención de RUT (pipelines/auto/rut.py)
        pq.write_table(_tabla_arrow(df), SALIDA / "aseguradoras.parquet", compression="zstd")


def recalcular_maestro() -> None:
    """Recalcula aseguradoras.parquet desde las filas publicadas (--solo-maestro).

    El maestro publica una fila por compañía con al menos una fila publicada, con su primer y
    último mes, cuántos meses publicó y el nombre del último mes. Sirve para corregir la
    métrica sin re-descargar la fuente (los meses se cuentan por filas publicadas, no por
    archivos recibidos vacíos).
    """
    meses: dict[tuple, set] = {}
    nombres: dict[tuple, str] = {}
    for t in TABLAS:
        carpeta = SALIDA / t
        if not carpeta.is_dir():
            continue
        for a in sorted(carpeta.glob("*.parquet")):
            df = pq.read_table(a, columns=["periodo", "sector", "rut_aseguradora",
                                           "nombre_aseguradora"]).to_pandas()
            for clave, g in df.groupby(["sector", "rut_aseguradora"], sort=True):
                meses.setdefault(clave, set()).update(g["periodo"])
            con_nombre = df.dropna(subset=["nombre_aseguradora"])
            if len(con_nombre):
                ultimos = (con_nombre.sort_values("periodo")
                           .groupby(["sector", "rut_aseguradora"])["nombre_aseguradora"].last())
                nombres.update(ultimos.to_dict())
    filas = [{"sector": s, "rut_aseguradora": r, "nombre_aseguradora": nombres.get((s, r)),
              "primer_periodo": min(m), "ultimo_periodo": max(m), "meses_reportados": len(m)}
             for (s, r), m in sorted(meses.items()) if m]
    df = pd.DataFrame(filas)
    control = cargar_control()
    ultimo = max(control["periodos"]) if control["periodos"] else None
    df["reporta_ultimo_mes"] = df["ultimo_periodo"] == ultimo
    df = normalizar_dataframe(df)  # convención de RUT (pipelines/auto/rut.py)
    pq.write_table(_tabla_arrow(df), SALIDA / "aseguradoras.parquet", compression="zstd")
    control["aseguradoras"] = {(f["sector"], f["rut_aseguradora"]):
                               {"nombre": f["nombre_aseguradora"], "primer": f["primer_periodo"],
                                "ultimo": f["ultimo_periodo"], "meses": int(f["meses_reportados"])}
                               for f in filas}
    guardar_control(control)


def actualizar_data_manifest(control: dict) -> None:
    """Mantiene al día las entradas de seguros en data_manifest.json (registros, último mes, fecha)."""
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    hoy = date.today().isoformat()
    entradas = []
    for tabla, (nombre, descripcion) in metadatos_web.TABLAS.items():
        if tabla == "aseguradoras":
            archivo = "outputs/seguros/aseguradoras.parquet"
            registros = pq.ParquetFile(SALIDA / "aseguradoras.parquet").metadata.num_rows \
                if (SALIDA / "aseguradoras.parquet").exists() else 0
            periodos = sorted(control["periodos"])
        else:
            archivo = f"outputs/seguros/{tabla}/manifest.json"
            m = json.loads((SALIDA / tabla / "manifest.json").read_text())
            registros, periodos = m["total_records"], m["periodos"]
        corte = f"{periodos[0]} a {periodos[-1]}" if periodos else "sin meses publicados"
        vista = "seguros_maestro" if tabla == "aseguradoras" else f"seguros_{tabla}"
        entradas.append({
            "id": vista, "name": nombre, "view_name": vista,
            "sector": "seguros", "sector_label": "Seguros de Vida y Generales", "norma": "Circular CMF 1835",
            "corte": corte, "frescura": f"Último mes publicado: {periodos[-1]}" if periodos else "",
            "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
            "file_parquet": archivo, "registros_reales": registros, "descripcion": descripcion,
            "origen": metadatos_web.ORIGEN,
        })
    # Reemplaza in-place: conserva el orden histórico de cada tabla en el catálogo.
    por_id = {t["id"]: t for t in man["tables"]}
    nuevas = []
    for e in entradas:
        if e["id"] in por_id:
            por_id[e["id"]] = e
        else:
            nuevas.append(e)
    man["tables"] = [por_id[t["id"]] for t in man["tables"]] + nuevas
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    estable.escribir_json(ruta, man)


def cargar_control() -> dict:
    ruta = SALIDA / "manifest.json"
    if ruta.exists():
        c = json.loads(ruta.read_text())
        # Claves con el RUT en formato canónico (cuerpo sin DV), igual que aseguradoras.parquet.
        recibidas = c.get("aseguradoras", {})
        c["aseguradoras"] = {}
        for k, v in recibidas.items():
            s, r = k.split("|", 1)
            c["aseguradoras"][(s, rutmod.cuerpo(r) or r)] = v
        return c
    return {"periodos": {}, "aseguradoras": {}}


def guardar_control(control: dict) -> None:
    c = dict(control)
    c["aseguradoras"] = {f"{s}|{r}": v for (s, r), v in sorted(control["aseguradoras"].items())}
    c["periodos"] = dict(sorted(control["periodos"].items()))
    c["desde"] = {t: DESDE_TABLA.get(t, DESDE) for t in TABLAS}
    c["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estable.escribir_json((SALIDA / "manifest.json"), c)


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def meses(desde: str, hasta: str) -> list[str]:
    y, m = map(int, desde.split("-"))
    fin = tuple(map(int, hasta.split("-")))
    out = []
    while (y, m) <= fin:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def ultimo_mes_cerrado(hoy: date | None = None) -> str:
    hoy = hoy or date.today()
    y, m = (hoy.year - 1, 12) if hoy.month == 1 else (hoy.year, hoy.month - 1)
    return f"{y}-{m:02d}"


def contar_archivos_por_tipo(data: bytes) -> dict[str, int]:
    """Cuenta entradas ZIP por letra de archivo sin leer ni exponer sus contenidos o RUT."""
    conteos = {letra: 0 for letra in ARCHIVOS}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for nombre in z.namelist():
            if nombre.endswith("/"):
                continue
            letra = os.path.basename(nombre)[:1].lower()
            if letra in conteos:
                conteos[letra] += 1
    return conteos


def diagnostico(periodos: list[str], a) -> int:
    """Lee todos los meses sin escribir; distingue errores fatales de archivos excluidos."""
    malos, excluidos_total, revisados = 0, 0, 0
    gha = bool(os.environ.get("GITHUB_ACTIONS"))
    for periodo in periodos:
        try:
            datos = {s: descargar(s, periodo, a.zip_dir, a.cache) for s in SECTORES}
        except NoPublicado:
            break
        revisados += 1
        for sector, data in datos.items():
            try:
                filas, comp, avisos, excluidos = leer_zip(data, periodo, sector)
                raw = contar_archivos_por_tipo(data)
                excluidos_total += len(excluidos)
                b11_b14 = (f"B.11/e {raw['e']} archivos, {len(filas['flujos_activos_elegibles'])} filas; "
                           f"B.12/r {raw['r']} archivos, {len(filas['prestamos'])} filas; "
                           f"B.13/v {raw['v']} archivos, {len(filas['bienes_raices_arriendo_morosidad'])} filas; "
                           f"B.14/g {raw['g']} archivos, {len(filas['garantias_derivados'])} filas")
                print(f"{periodo} {sector}: OK · {len(comp)} compañías · {sum(map(len, filas.values()))} filas"
                      f" · {len(avisos)} avisos · {len(excluidos)} archivos excluidos · {b11_b14}")
            except ErrorValidacion as e:
                malos += 1
                print(f"{periodo} {sector}: PROBLEMA · {e}")
                if gha:
                    print(f"::warning title=Diagnóstico {periodo} {sector}::" + str(e).replace("\n", "%0A")[:1500])
    resumen = (f"{revisados} meses revisados, {malos} sectores con error fatal, "
               f"{excluidos_total} archivos excluidos con advertencia")
    print(f"Diagnóstico: {resumen}.")
    if gha:
        print(f"::notice title=Diagnóstico seguros::{resumen}")
    return 0


def meses_atras(periodo: str, n: int) -> str:
    y, m = int(periodo[:4]), int(periodo[5:])
    m -= n
    while m < 1:
        y, m = y - 1, m + 12
    return f"{y:04d}-{m:02d}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", default=DESDE)
    ap.add_argument("--hasta", default=None, help="último mes a considerar (por defecto, el último mes cerrado)")
    ap.add_argument("--minutos", type=float, default=270, help="tope de tiempo de la corrida (el progreso se conserva)")
    ap.add_argument("--max-periodos", type=int, default=0, help="máximo de cierres a revisar por corrida (0 = sin tope)")
    ap.add_argument("--zip-dir", type=Path, default=None, help="leer ZIP locales en vez de descargar (pruebas)")
    ap.add_argument("--cache", type=Path, default=None, help="guardar/reusar las descargas en esta carpeta")
    ap.add_argument("--diagnostico", action="store_true",
                    help="revisar todos los meses pendientes sin escribir nada y listar los problemas")
    ap.add_argument("--salida-github", default=os.environ.get("GITHUB_OUTPUT"))
    ap.add_argument("--solo-data-manifest", action="store_true",
                    help="solo recalcular las entradas de este sector en data_manifest.json")
    ap.add_argument("--solo-maestro", action="store_true",
                    help="solo recalcular aseguradoras.parquet desde las filas publicadas")
    ap.add_argument("--forzar", action="store_true",
                    help="volver a descargar y publicar todos los meses del rango, aunque ya "
                         "estén publicados (para reconstruir la historia tras cambiar el esquema)")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest(cargar_control())
        return 0
    if a.solo_maestro:
        recalcular_maestro()
        if (RAIZ / "data_manifest.json").exists():
            actualizar_data_manifest(cargar_control())
        return 0

    SALIDA.mkdir(parents=True, exist_ok=True)
    control = cargar_control()
    hasta = a.hasta or ultimo_mes_cerrado()
    desde = min([a.desde] + list(DESDE_TABLA.values())) if a.desde == DESDE else a.desde
    derivables = backfill_vistas_existentes(control, escribir=not a.diagnostico) if not a.forzar else set()
    pendientes = []
    for p in meses(desde, hasta):
        if a.forzar:  # reconstruir: el mes se vuelve a descargar y a escribir tal cual
            pendientes.append((p, tablas_de(p)))
            continue
        hechas = set(control["periodos"].get(p, {}).get("registros", {}))
        faltan = [t for t in tablas_de(p) if t not in hechas and (p, t) not in derivables]
        if faltan:
            pendientes.append((p, faltan))
    if a.forzar:
        print("--forzar: se vuelven a descargar y publicar los meses del rango")
    print(f"Meses publicados: {len(control['periodos'])}. Meses con tablas pendientes: {len(pendientes)}"
          + (f" ({pendientes[0][0]} .. {pendientes[-1][0]})" if pendientes else ""))
    if a.diagnostico:
        return diagnostico([p for p, _ in pendientes[:a.max_periodos if a.max_periodos > 0 else len(pendientes)]], a)
    hechos = []
    inicio = time.monotonic()
    for periodo, faltan in pendientes:
        if a.max_periodos > 0 and len(hechos) >= a.max_periodos:
            break
        if time.monotonic() - inicio > a.minutos * 60:
            print("Tiempo agotado; el resto sigue en la próxima corrida.")
            break
        t0 = time.time()
        try:
            datos = {s: descargar(s, periodo, a.zip_dir, a.cache) for s in SECTORES}
        except NoPublicado as e:
            if periodo >= meses_atras(hasta, 3):
                print(f"{periodo}: sin publicar todavía ({e}). Se retoma en la próxima corrida.")
                break
            # Mes antiguo que no se pudo bajar: se deja pendiente (se reintenta en la próxima
            # corrida) y se sigue con los demás, para que un hueco no frene toda la carga.
            print(f"::warning::{periodo}: no se pudo descargar ({e}); queda pendiente")
            continue
        filas = {t: [] for t in TABLAS}
        companias = {}
        avisos = []
        excluidos = []
        for sector, data in datos.items():
            f, comp, av, exc = leer_zip(data, periodo, sector)  # ErrorValidacion corta la corrida
            avisos += av
            excluidos += [f"{sector} {x}" for x in exc]
            for x in exc:
                print(f"::warning title=Seguros {periodo}: archivo excluido::{sector} {x}")
            for t in TABLAS:
                filas[t].extend(f[t])
            companias[sector] = comp
        conteo = escribir_periodo(periodo, filas, faltan)
        # Duplicados exactos: la fuente (compañía/CMF) a veces repite líneas idénticas; se publica
        # tal cual, pero se avisa (al agregar por instrumento o compañía, esos meses sobrestiman).
        for t in TABLAS:
            d = int(pd.DataFrame(filas[t]).duplicated().sum())
            if d:
                avisos.append(f"{t}: {d} filas 100% idénticas (duplicados de la fuente)")
        previo = control["periodos"].get(periodo)
        if previo is None:  # primera vez que se procesa el mes: registrar las compañías que reportan
            # Los meses se cuentan por filas publicadas: una compañía que solo envía archivos
            # vacíos (sin detalle) no suma meses en el maestro de entidades.
            con_filas = {s: {f["rut_aseguradora"] for t in TABLAS for f in filas[t]
                             if f["sector"] == s and f["rut_aseguradora"]} for s in SECTORES}
            for sector, comp in companias.items():
                for rut in con_filas[sector]:
                    nombre = comp.get(rut)
                    info = control["aseguradoras"].setdefault((sector, rutmod.cuerpo(rut) or rut),
                                                              {"nombre": nombre, "primer": periodo,
                                                               "ultimo": periodo, "meses": 0})
                    info["meses"] += 1
                    info["primer"] = min(info["primer"], periodo)
                    if periodo >= info["ultimo"]:
                        info["ultimo"], info["nombre"] = periodo, nombre
            previo = {"formato": formato_de(periodo), "companias": {s: len(c) for s, c in companias.items()},
                      "registros": {}, "avisos": len(avisos), "detalle_avisos": avisos[:40]}
            if excluidos:
                previo["archivos_excluidos"] = excluidos
        previo["registros"].update(conteo)
        # Las exclusiones de un archivo de compañía se registran también al reconstruir un
        # período ya existente (p. ej. al incorporar una tabla nueva), no sólo al primer proceso.
        if excluidos:
            previo["archivos_excluidos"] = sorted(set(previo.get("archivos_excluidos", [])) | set(excluidos))
        previo["avisos"] = len(avisos)
        previo["detalle_avisos"] = avisos[:40]
        # SHA-256 del ZIP que entregó la CMF por cada sector (vida / generales).
        previo.setdefault("sha256_origen", {}).update({s: hashlib.sha256(d).hexdigest() for s, d in datos.items()})
        control["periodos"][periodo] = previo
        guardar_control(control)
        hechos.append(periodo)
        print(f"{periodo} ({formato_de(periodo)}): " + ", ".join(f"{t} {n}" for t, n in conteo.items())
              + f" [{time.time() - t0:.0f}s]" + (f" · {len(avisos)} avisos de las compañías" if avisos else ""))
    dm = RAIZ / "data_manifest.json"
    falta_en_web = dm.exists() and '"seguros_renta_fija"' not in dm.read_text()
    if control["periodos"] and (hechos or falta_en_web):
        escribir_manifiestos(control)
        actualizar_data_manifest(control)
    if a.salida_github:
        with open(a.salida_github, "a") as fh:
            fh.write(f"publicados={len(hechos)}\n")
            fh.write(f"ultimo={hechos[-1] if hechos else ''}\n")
    print(f"Listo: {len(hechos)} meses nuevos.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErrorValidacion as e:
        print(f"ERROR DE VALIDACIÓN (no se publicó el mes): {e}", file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS"):  # visible en el resumen de la corrida
            print("::error title=Seguros 1835::" + str(e).replace("\n", "%0A")[:3000])
        sys.exit(2)
