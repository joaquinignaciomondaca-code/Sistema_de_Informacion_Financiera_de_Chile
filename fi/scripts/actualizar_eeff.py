"""Balance y resultados de FIRES/FINRE desde XML FIEF de la CMF.

Independiente de las carteras. Un XML por fondo/cierre, desde 2010-12 por defecto.
Valida cuentas, identidades y contextos, y coteja con la ficha antes de publicar.
Los comparativos inválidos se excluyen con motivo explícito; nunca se inventan
ceros. Una reedición defectuosa/no disponible conserva TODO el documento previo.
Caché por trimestre, reanudable sin guardar los XML masivos en Git.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from fi.scripts import eeff_xml as xml
from fi.scripts.cotejo_eeff import cotejar
from pipelines.auto import estable

DESDE = "2010-12"
TABLAS = ("fi_balance", "fi_resultados")
TIPOS = ("FINRE", "FIRES")
DIAS_ESPERA = {3: 75, 6: 75, 9: 75, 12: 100}
MAX_RECHAZADOS = 0.02
VUELTAS = 36
UA = {
    "User-Agent": "Mozilla/5.0 (compatible; SIFChile/1.0)",
    "Accept-Encoding": "identity",
}
FICHA = (
    "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={run}&tipoentidad={tipo}"
    "&vig=VI&control=svs&pestania=29&mm={mes}&aa={anio}&tipo=I&tipo_norma=IFRS"
)
ARCHIVO = (
    "https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo={archivo}"
    "&&rut={run}&&periodo={periodo}&&path=/web/ifrs_xml/fiifr/xml/&&desc_archivo=Estados_financieros_"
)
ESQUEMA = pa.schema(
    [
        (
            c,
            pa.int64()
            if c == "valor_miles_mf"
            else pa.int32()
            if c == "orden"
            else pa.string(),
        )
        for c in xml.COLUMNAS
    ]
)


@dataclass(frozen=True)
class Config:
    raiz: Path = RAIZ
    salida: Path | None = None
    local: Path | None = None

    @property
    def docs(self):
        return self.salida if self.salida is not None else self.raiz / "docs/outputs/fi"

    @property
    def cache(self):
        return (
            self.local if self.local is not None else self.raiz / ".local-data/fi_eeff"
        )

    @property
    def control(self):
        return self.docs / "fi_eeff_control.json"


def _hoy():
    return datetime.now(ZoneInfo("America/Santiago")).date()


def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get(url):
    ultimo = None
    for i in range(3):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=45
            ) as r:
                raw = r.read(xml.MAX_XML + 1)
            if not raw or len(raw) > xml.MAX_XML:
                raise xml.ErrorTransitorio("respuesta vacía o demasiado grande")
            return raw
        except (OSError, urllib.error.HTTPError, xml.ErrorTransitorio) as e:
            ultimo = e
            if i < 2:
                time.sleep((3, 8)[i])
    raise xml.ErrorTransitorio(str(ultimo))


def trimestres(desde, hasta):
    xml.fin_periodo(desde)
    xml.fin_periodo(hasta)
    if desde > hasta:
        raise ValueError("desde es posterior a hasta")
    y, m = map(int, desde.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= hasta:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 3) if m == 12 else (y, m + 3)
    return out


def ultimo_disponible(hoy):
    y, m = hoy.year, (hoy.month - 1) // 3 * 3
    if m == 0:
        y, m = y - 1, 12
    while xml.fin_periodo(f"{y:04d}-{m:02d}") + timedelta(days=DIAS_ESPERA[m]) > hoy:
        y, m = (y - 1, 12) if m == 3 else (y, m - 3)
    return f"{y:04d}-{m:02d}"


def cargar_registro(cfg):
    ruta = cfg.docs / "fi_registro_fondos_universo.json"
    filas = json.loads(ruta.read_text(encoding="utf-8"))
    out = {}
    for r in filas:
        run, tipo = str(r.get("run_fondo") or ""), r.get("tipo_entidad")
        if not run.isdigit() or tipo not in TIPOS:
            raise ValueError("identidad/tipo inválidos en el registro FI")
        if run in out:
            raise ValueError(f"RUN duplicado en el registro FI: {run}")
        vigencia = r.get("estado_vigencia")
        if vigencia not in ("Vigente", "No Vigente"):
            raise ValueError(
                f"vigencia inválida o no declarada en el registro FI: {run}"
            )
        out[run] = {
            "run": run,
            "tipo_entidad": tipo,
            "vig": "VI" if vigencia == "Vigente" else "NV",
        }
    if not out:
        raise ValueError("registro FI vacío")
    # No usar vida observada de cartera como vida legal: omitiría los FI sin cartera.
    return out


def url_ficha(run, tipo, periodo, vig="VI"):
    if tipo not in TIPOS or vig not in ("VI", "NV"):
        raise ValueError("tipo/vigencia de ficha FI inválidos")
    xml.fin_periodo(periodo)
    return FICHA.format(run=run, tipo=tipo, anio=periodo[:4], mes=periodo[5:]).replace(
        "&vig=VI&", f"&vig={vig}&"
    )


def leer_json(ruta, defecto=None):
    return (
        json.loads(ruta.read_text(encoding="utf-8"))
        if ruta.exists()
        else ({} if defecto is None else defecto)
    )


def json_atomico(ruta, obj):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        try:
            if estable.sin_volatiles(leer_json(ruta)) == estable.sin_volatiles(obj):
                return False
        except ValueError:
            pass
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, ruta)
    return True


def _digest(r):
    limpio = estable.sin_volatiles(
        {k: v for k, v in r.items() if k != "sha256_registro"}
    )
    return hashlib.sha256(
        json.dumps(
            limpio, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def guardar_progreso(cfg, periodo, regs):
    carpeta = cfg.cache / "progreso"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{periodo}.jsonl.gz"
    tmp = ruta.with_suffix(".gz.tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        for run, r in sorted(regs.items(), key=lambda p: int(p[0])):
            f.write(
                json.dumps(
                    {**r, "sha256_registro": _digest(r)},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
    os.replace(tmp, ruta)


def cargar_progreso(cfg, periodo):
    ruta = cfg.cache / "progreso" / f"{periodo}.jsonl.gz"
    if not ruta.exists():
        return {}
    try:
        with gzip.open(ruta, "rt", encoding="utf-8") as f:
            rs = [json.loads(linea) for linea in f]
        if any(
            r.get("periodo") != periodo or r.get("sha256_registro") != _digest(r)
            for r in rs
        ):
            raise ValueError("checksum/período de la caché no coincide")
        return {
            r["run"]: {k: v for k, v in r.items() if k != "sha256_registro"} for r in rs
        }
    except (OSError, ValueError, KeyError) as e:
        print(
            f"::warning::FI {periodo}: caché inválida ({e}); se reconstruye desde lo publicado"
        )
        return {}


def registros_publicados(cfg, periodo, control):
    meta = control.get("periodos", {}).get(periodo, {}).get("registros", {})
    out = {run: dict(r) for run, r in meta.items() if r.get("estado") != "ok"}
    for tabla in ("balance", "resultados"):
        ruta = cfg.docs / f"fi_{tabla}" / f"{periodo}.parquet"
        if not ruta.exists():
            continue
        for f in pq.read_table(ruta).to_pylist():
            run = f["run_fondo"]
            r = out.setdefault(
                run,
                {
                    **meta.get(run, {}),
                    "estado": "ok",
                    "run": run,
                    "periodo": periodo,
                    "nombre": f["nombre_fondo"],
                    "tipo_entidad": f["tipo_entidad"],
                    "rut_agf": f["rut_agf"],
                    "agf": f["razon_social_agf"],
                    "dv_fondo_fuente": f["dv_fondo_fuente"],
                    "moneda": f["moneda"],
                    "moneda_cmf": f["moneda_cmf"],
                    "archivo": f["fuente_archivo"],
                    "sha256": f["sha256_archivo"],
                    "enviado": f["enviado_cmf"],
                    "contextos": {},
                    "tablas": {"balance": {}, "resultados": {}},
                    "notas": {},
                },
            )
            ctx, cod = f["contexto"], f["codigo_cuenta"]
            r["tablas"][tabla].setdefault(ctx, {})[cod] = f["valor_miles_mf"]
            r["contextos"][ctx] = {
                "inicio": f["fecha_inicio_contexto"],
                "termino": f["fecha_fin_contexto"],
            }
            if f["nota"]:
                r["notas"].setdefault(ctx, {})[cod] = f["nota"]
    return out


def cargar_estado(cfg, periodo, control):
    estado = registros_publicados(cfg, periodo, control)
    for run, r in cargar_progreso(cfg, periodo).items():
        previo = estado.get(run)
        if previo is None or r.get("ultima_revision_utc", "") >= previo.get(
            "ultima_revision_utc", ""
        ):
            # Una caché pendiente/rechazada jamás borra datos válidos.
            if previo and previo.get("estado") == "ok" and r.get("estado") != "ok":
                continue
            estado[run] = r
    return estado


def sondeados_sin_datos(cfg):
    """Cargar la lista de trimestres sondeados sin datos desde el control."""
    control = leer_json(cfg.control, {"periodos": {}})
    return set(control.get("sondeados_sin_datos", []))


def guardar_sondeados(cfg, sondeados):
    """Persistir la lista de trimestres sondeados sin datos."""
    control = leer_json(cfg.control, {"periodos": {}})
    control["sondeados_sin_datos"] = sorted(sondeados)
    json_atomico(cfg.control, control)


def trimestres_reintentables(cfg):
    """Trimestres sondeados sin datos que deben reintentarse.
    
    Regla: reintentar TODOS los sondeados_sin_datos, sin importar si son anteriores
    o posteriores al primer dato publicado. La CMF puede completar datos históricos
    o subir data nueva en cualquier momento. La única excepción son los ya publicados
    (que sí tienen datos y no necesitan reintentarse).
    """
    control = leer_json(cfg.control, {"periodos": {}})
    return set(control.get("sondeados_sin_datos", []))


def claves_reg(r):
    return {
        (t, ctx, cod)
        for t, cs in r.get("tablas", {}).items()
        for ctx, cuentas in cs.items()
        for cod in cuentas
    }


def _conservar(previo, base, motivo, archivo=None):
    if previo and previo.get("estado") == "ok":
        return {
            **previo,
            "ultima_revision_utc": base["ultima_revision_utc"],
            "actualizacion_rechazada": {"archivo": archivo, "motivo": motivo},
        }, "conservado"
    return None


def pedir_validado(url, parser, fetcher):
    for intento in range(3):
        raw = fetcher(url)
        try:
            return raw, parser(raw)
        except xml.ErrorTransitorio:
            if intento == 2:
                raise
            time.sleep((2, 5)[intento])


def resolver(run, tipo, periodo, previo, fetcher=_get, forzar=False, vig="VI"):
    base = {
        "run": run,
        "tipo_entidad": tipo,
        "vigencia_consultada": vig,
        "periodo": periodo,
        "ultima_revision_utc": _ahora(),
        "version_parser": xml.VERSION_PARSER,
    }
    archivo = None
    try:
        ficha_url = url_ficha(run, tipo, periodo, vig)
        ficha, (estado, archivo) = pedir_validado(
            ficha_url, lambda b: xml.clasificar_ficha(b, periodo), fetcher
        )
        if estado == "sin_informacion":
            return _conservar(previo, base, "la ficha ya no muestra el envío") or (
                {**base, "estado": "sin_informacion"},
                "sin_informacion",
            )
        if estado == "sin_enlace":
            raise xml.ErrorTransitorio("la ficha no enlaza FIEF")
        if (
            previo
            and previo.get("estado") == "ok"
            and previo.get("archivo") == archivo
            and previo.get("version_parser") == xml.VERSION_PARSER
            and previo.get("tipo_entidad") == tipo
            and previo.get("fuente_ficha") == ficha_url
            and not forzar
        ):
            return {
                **previo,
                "ultima_revision_utc": base["ultima_revision_utc"],
            }, "sin_cambios"
        url = ARCHIVO.format(run=run, archivo=archivo, periodo=periodo.replace("-", ""))
        _raw, datos = pedir_validado(
            url, lambda b: xml.extraer(b, run, periodo), fetcher
        )
        datos["cotejo"] = cotejar(ficha, datos)
        reg = {
            **base,
            **datos,
            "estado": "ok",
            "archivo": archivo,
            "enviado": xml.enviado_de(archivo),
            "fuente_ficha": ficha_url,
        }
        if (
            previo
            and previo.get("estado") == "ok"
            and not claves_reg(previo) <= claves_reg(reg)
        ):
            return _conservar(
                previo,
                base,
                "la reedición pierde cuentas o contextos validados",
                archivo,
            )
        return reg, "reedicion" if previo and previo.get("estado") == "ok" else "nuevo"
    except xml.ErrorTransitorio as e:
        return _conservar(previo, base, str(e), archivo) or (
            {**base, "estado": "pendiente", "motivo": str(e), "archivo": archivo},
            "pendiente",
        )
    except xml.ErrorFuente as e:
        return _conservar(previo, base, str(e), archivo) or (
            {**base, "estado": "rechazado", "motivo": str(e), "archivo": archivo},
            "rechazado",
        )


def toca_refresco(run, periodo, hoy, ultimo, forzar=False):
    recientes = trimestres(DESDE, ultimo)[-2:] if ultimo >= DESDE else []
    if forzar or periodo in recientes:
        return True
    vuelta = (hoy.month - 1) * 3 + min((hoy.day - 1) // 10, 2)
    return (
        int(hashlib.sha256(f"{run}|{periodo}".encode()).hexdigest()[:8], 16) % VUELTAS
        == vuelta
    )


class Frenazo:
    def __init__(self):
        self.lock, self.malos, self.activo = threading.Lock(), 0, False

    def contar(self, fallo):
        with self.lock:
            self.malos = self.malos + 1 if fallo else 0
            self.activo = self.activo or self.malos >= 12


def procesar(registro, estado, periodo, hoy, ultimo, deadline, hilos, fetcher, forzar):
    def necesita(run):
        r = estado.get(run, {})
        if (
            r.get("estado") in (None, "pendiente", "rechazado")
            or r.get("version_parser") != xml.VERSION_PARSER
            or r.get("tipo_entidad") != registro[run]["tipo_entidad"]
            or r.get("vigencia_consultada", "VI") != registro[run].get("vig", "VI")
        ):
            return True
        if forzar:
            return True
        # Reanudar/depurar en el mismo día no exige volver a descargar un censo
        # que acaba de resolverse. --refrescar-todo ignora esta caché diaria.
        try:
            revision = (
                datetime.fromisoformat(r.get("ultima_revision_utc", ""))
                .astimezone(ZoneInfo("America/Santiago"))
                .date()
            )
        except ValueError:
            revision = None
        return revision != hoy and toca_refresco(run, periodo, hoy, ultimo)

    pedir = [
        (run, r["tipo_entidad"], r.get("vig", "VI"))
        for run, r in sorted(registro.items(), key=lambda p: int(p[0]))
        if necesita(run)
    ]
    freno, cuenta = Frenazo(), Counter()

    def tarea(t):
        run, tipo, vig = t
        if time.monotonic() >= deadline or freno.activo:
            return run, None, "sin_tiempo"
        try:
            r, evento = resolver(
                run, tipo, periodo, estado.get(run), fetcher, forzar, vig
            )
        except (OSError, ValueError) as e:
            r, evento = (
                {
                    "run": run,
                    "tipo_entidad": tipo,
                    "periodo": periodo,
                    "estado": "pendiente",
                    "motivo": str(e),
                    "ultima_revision_utc": _ahora(),
                    "version_parser": xml.VERSION_PARSER,
                },
                "pendiente",
            )
            if estado.get(run, {}).get("estado") == "ok":
                r, evento = _conservar(estado[run], r, str(e))
        freno.contar(evento == "pendiente")
        return run, r, evento

    with ThreadPoolExecutor(max_workers=hilos) as ex:
        futuros = [ex.submit(tarea, t) for t in pedir]
        for fut in as_completed(futuros):
            run, r, evento = fut.result()
            cuenta[evento] += 1
            if r is not None:
                estado[run] = r
    # Una segunda vuelta acotada a los transitorios aislados: nunca resuelve
    # ausencias por agotamiento de intentos ni vuelve a bajar el censo completo.
    pendientes = [
        (run, r["tipo_entidad"], r.get("vig", "VI"))
        for run, r in registro.items()
        if estado.get(run, {}).get("estado") == "pendiente"
    ]
    if pendientes and not freno.activo and time.monotonic() + 15 < deadline:
        with ThreadPoolExecutor(max_workers=min(hilos, 3)) as ex:
            for run, r, evento in ex.map(tarea, pendientes):
                cuenta[f"reintento_{evento}"] += 1
                if r is not None:
                    estado[run] = r
    return dict(cuenta), freno.activo


def evaluar(estado, registro):
    faltan = sorted(
        run
        for run in set(registro) | set(estado)
        if estado.get(run, {}).get("estado") in (None, "pendiente")
    )
    ok = [r for r in estado.values() if r["estado"] == "ok"]
    malos = [r for r in estado.values() if r["estado"] == "rechazado"]
    conocidos = len(ok) + len(malos)
    motivo = ""
    if conocidos and len(malos) > MAX_RECHAZADOS * conocidos:
        motivo = f"{len(malos)} de {conocidos} documentos con XML rechazados (> {MAX_RECHAZADOS:.0%})"
    return {
        "pendientes": faltan,
        "ok": len(ok),
        "rechazados": len(malos),
        "motivo_error": motivo,
        "puede_publicar": bool(ok) and not faltan and not motivo,
    }


def _metadata(r):
    return {
        k: v
        for k, v in r.items()
        if k
        not in (
            "tablas",
            "contextos",
            "notas",
            "nombre",
            "rut_agf",
            "agf",
            "moneda",
            "moneda_cmf",
            "dv_fondo_fuente",
        )
    }


def publicar_periodo(cfg, periodo, estado, control, registro):
    from fi.scripts.auditar_eeff import verificar_tablas

    filas = {t: [] for t in ("balance", "resultados")}
    for r in sorted(estado.values(), key=lambda r: int(r["run"])):
        if r["estado"] != "ok":
            continue
        for t, fs in xml.filas(r).items():
            filas[t].extend(fs)
    auditoria = verificar_tablas(filas)
    if auditoria["errores"]:
        raise xml.ErrorFuente("no se publica: " + "; ".join(auditoria["errores"][:5]))
    nuevas = {t: pa.Table.from_pylist(fs, schema=ESQUEMA) for t, fs in filas.items()}
    # Claves por entidad/tabla/contexto: no basta que el total de filas haya crecido.
    for t in nuevas:
        ruta = cfg.docs / f"fi_{t}" / f"{periodo}.parquet"
        if ruta.exists():
            prev = pq.read_table(ruta).to_pylist()
            claves = lambda fs: {
                (f["run_fondo"], f["contexto"], f["codigo_cuenta"]) for f in fs
            }
            if not claves(prev) <= claves(filas[t]):
                raise xml.ErrorFuente(
                    f"{periodo}/{t}: no se permite perder claves ya publicadas"
                )
    rutas = [cfg.docs / f"fi_{t}" / f"{periodo}.parquet" for t in nuevas]
    rutas += [cfg.control, *[cfg.docs / f"fi_{t}/manifest.json" for t in nuevas]]
    backups = {r: r.read_bytes() if r.exists() else None for r in rutas}
    control_anterior = copy.deepcopy(control)
    cambio = False
    try:
        for t, table in nuevas.items():
            ruta = cfg.docs / f"fi_{t}" / f"{periodo}.parquet"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            if ruta.exists() and pq.read_table(ruta).equals(table):
                continue
            tmp = ruta.with_suffix(".parquet.tmp")
            pq.write_table(table, tmp, compression="zstd", compression_level=9)
            if not pq.read_table(tmp).equals(table):
                raise xml.ErrorFuente("el roundtrip Parquet no coincide")
            os.replace(tmp, ruta)
            cambio = True
        p = {
            "candidatos": len(registro),
            "con_estados": sum(r["estado"] == "ok" for r in estado.values()),
            "filas": {t: len(filas[t]) for t in filas},
            "reglas_verificadas": auditoria["reglas"],
            "sha256_parquet": {
                t: hashlib.sha256(
                    (cfg.docs / f"fi_{t}" / f"{periodo}.parquet").read_bytes()
                ).hexdigest()
                for t in filas
            },
            "registros": {
                run: _metadata(r)
                for run, r in sorted(estado.items(), key=lambda p: int(p[0]))
            },
        }
        control.setdefault("periodos", {})[periodo] = p
        control.update(
            tabla="fi_eeff", version_parser=xml.VERSION_PARSER, updated_at=_ahora()
        )
        cambio = json_atomico(cfg.control, control) or cambio
        escribir_manifiestos(cfg, control)
    except Exception:
        control.clear()
        control.update(control_anterior)
        for ruta, antes in backups.items():
            if antes is None:
                ruta.unlink(missing_ok=True)
            else:
                ruta.write_bytes(antes)
        for t in nuevas:
            (cfg.docs / f"fi_{t}" / f"{periodo}.parquet.tmp").unlink(missing_ok=True)
        raise
    return cambio


def escribir_manifiestos(cfg, control):
    for t in ("balance", "resultados"):
        carpeta = cfg.docs / f"fi_{t}"
        rutas = sorted(
            p for p in carpeta.glob("*.parquet") if p.name != "_vacio.parquet"
        )
        m = {
            "tabla": f"fi_{t}",
            "files": [p.relative_to(cfg.raiz / "docs").as_posix() for p in rutas],
            "periodos": [p.stem for p in rutas],
            "total_records": sum(pq.ParquetFile(p).metadata.num_rows for p in rutas),
            "updated_at": _ahora(),
            "nota": "Filtrar contexto = 'PeriodoActual' para el cierre/acumulado actual; no sumar contextos ni monedas.",
            "contextos_excluidos": [
                {
                    "periodo": per,
                    "run_fondo": run,
                    "contexto": ctx,
                    "errores": v["errores"],
                }
                for per, p in sorted(control.get("periodos", {}).items())
                for run, r in p["registros"].items()
                for ctx, v in r.get("validacion", {}).get(t, {}).items()
                if v["estado"] == "rechazado"
            ],
        }
        json_atomico(carpeta / "manifest.json", m)
        if rutas:
            (carpeta / "_vacio.parquet").unlink(missing_ok=True)


def descubrir_primer_trimestre(registro, hilos=8, fetcher=_get):
    """Descubre automáticamente el trimestre más antiguo con EEFF en la CMF.
    
    Prueba TODOS los fondos del registro para cada trimestre, caminando hacia atrás
    desde DESDE. Un trimestre es válido si al menos un fondo tiene estado financiero
    (ok o ausencia). Si 2+ trimestres consecutivos no tienen ningún dato, se asume
    que se alcanzó el límite histórico.
    
    Retorna una tupla (primer_trimestre, lista_trimestres_sin_datos).
    """
    runs = list(registro.keys())
    print(f"Descubriendo primer trimestre EEFF con {len(runs)} fondos del registro...")
    
    def probar_fondo(run, periodo):
        """Retorna el estado del fondo para ese periodo: 'ok', 'sin_informacion', o None."""
        tipo = registro[run]["tipo_entidad"]
        vig = registro[run].get("vig", "VI")
        try:
            r, evento = resolver(run, tipo, periodo, None, fetcher, forzar=False, vig=vig)
            if r.get("estado") in ("ok", "sin_informacion"):
                return r["estado"]
            return None
        except Exception:
            return None
    
    y, m = int(DESDE[:4]), int(DESDE[5:])
    trimestre_valido = DESDE
    trimestres_sin_datos = []
    trimestres_consecutivos_sin_datos = 0
    
    while True:
        y, m = (y - 1, 12) if m == 3 else (y, m - 3)
        
        # Límite razonable: antes de 2008 no había IFRS para FI en Chile
        if y < 2008:
            print(f"  Límite 2008 alcanzado sin encontrar corte.")
            break
        
        periodo = f"{y:04d}-{m:02d}"
        fondos_con_datos = 0
        fondos_sin_info = 0
        
        with ThreadPoolExecutor(max_workers=min(hilos, 8)) as ex:
            futuros = [ex.submit(probar_fondo, run, periodo) for run in runs]
            for fut in futuros:
                resultado = fut.result()
                if resultado == "ok":
                    fondos_con_datos += 1
                elif resultado == "sin_informacion":
                    fondos_sin_info += 1
        
        total = fondos_con_datos + fondos_sin_info
        if fondos_con_datos > 0:
            trimestre_valido = periodo
            print(f"  {periodo}: {fondos_con_datos} fondos con EEFF + {fondos_sin_info} sin info ({total}/{len(runs)}) ✓")
            trimestres_consecutivos_sin_datos = 0
        elif fondos_sin_info > 0:
            # Hay fondos que reportan ausencia: la CMF ya operaba
            trimestre_valido = periodo
            print(f"  {periodo}: 0 con EEFF + {fondos_sin_info} sin info ({total}/{len(runs)}) ✓")
            trimestres_consecutivos_sin_datos = 0
        else:
            trimestres_sin_datos.append(periodo)
            trimestres_consecutivos_sin_datos += 1
            print(f"  {periodo}: 0/{len(runs)} fondos con datos")
            if trimestres_consecutivos_sin_datos >= 2:
                print(f"  Dos trimestres consecutivos sin datos. Límite detectado.")
                break
    
    print(f"→ Primer trimestre EEFF disponible: {trimestre_valido}")
    print(f"→ Trimestres sondeados sin datos: {len(trimestres_sin_datos)}")
    return trimestre_valido, trimestres_sin_datos


def correr(
    cfg=None,
    minutos=270,
    hilos=8,
    desde=None,
    hasta=None,
    max_periodos=0,
    forzar=False,
    publicar=True,
    registro=None,
    fetcher=_get,
):
    cfg = cfg or Config()
    if minutos <= 0 or not 1 <= hilos <= 32 or max_periodos < 0:
        raise ValueError("minutos/hilos/max-periodos inválidos")
    hoy, deadline = _hoy(), time.monotonic() + minutos * 60
    ultimo = ultimo_disponible(hoy)
    hasta = hasta or ultimo
    if hasta > ultimo:
        raise ValueError(
            f"el último trimestre admisible por plazo de publicación es {ultimo}"
        )
    registro = cargar_registro(cfg) if registro is None else registro
    if not registro:
        raise ValueError("registro FI vacío")
    control = leer_json(cfg.control, {"periodos": {}})
    control.setdefault("sondeados_sin_datos", [])
    # Determinar el primer trimestre
    if desde:
        primer_trimestre = desde
    elif control.get("periodos"):
        # Ya hay datos publicados: usar el más antiguo
        primer_trimestre = min(control["periodos"].keys())
    else:
        # Primera corrida: descubrir automáticamente
        primer_trimestre, nuevos_sin_datos = descubrir_primer_trimestre(registro, hilos, fetcher)
        # Agregar a la lista de sondeados sin datos (no persistir aún; se guarda al publicar)
        control["sondeados_sin_datos"] = sorted(
            set(control.get("sondeados_sin_datos", [])) | set(nuevos_sin_datos)
        )
    # Periodos a procesar: no publicados + reintentables (huecos posteriores al primer dato)
    publicados = set(control.get("periodos", {}).keys())
    reintentables = trimestres_reintentables(cfg)
    todos = set(trimestres(primer_trimestre, hasta))
    if forzar:
        # Con forzar=True, reprocesar todo (incluye periodos ya publicados)
        periodos_set = todos
    else:
        periodos_set = (todos - publicados) | (reintentables & todos)
    periodos = sorted(periodos_set, reverse=True)
    if max_periodos:
        periodos = periodos[:max_periodos]
    print(f"Periodos publicados: {len(publicados)}. "
          f"A procesar: {len(periodos)} ({len(reintentables)} reintentables).")
    resumen = {
        "desde": primer_trimestre,
        "hasta": hasta,
        "publicados": [],
        "periodos": {},
        "errores": [],
    }
    for periodo in periodos:
        if time.monotonic() >= deadline:
            break
        estado = cargar_estado(cfg, periodo, control)
        cuenta, freno = procesar(
            registro, estado, periodo, hoy, ultimo, deadline, hilos, fetcher, forzar
        )
        guardar_progreso(cfg, periodo, estado)
        ev = evaluar(estado, registro)
        rechazados = [r for r in estado.values() if r["estado"] == "rechazado"]
        diagnostico = {
            "motivos_rechazo": dict(
                Counter(r.get("motivo", "")[:120] for r in rechazados).most_common(5)
            ),
            "ejemplos_pendientes": [
                {"run": r["run"], "motivo": r.get("motivo", "")[:220]}
                for r in estado.values()
                if r["estado"] == "pendiente"
            ][:8],
            "ejemplos_rechazo": [
                {"run": r["run"], "motivo": r.get("motivo", "")[:220]}
                for r in rechazados[:3]
            ],
        }
        resumen["periodos"][periodo] = {
            **ev,
            "cuenta": cuenta,
            "pendientes": len(ev["pendientes"]),
            **diagnostico,
        }
        if ev["puede_publicar"] and publicar:
            try:
                if publicar_periodo(cfg, periodo, estado, control, registro):
                    resumen["publicados"].append(periodo)
                    # Publicado con éxito: remover de sondeados_sin_datos
                    if periodo in control.get("sondeados_sin_datos", []):
                        control["sondeados_sin_datos"].remove(periodo)
                        json_atomico(cfg.control, control)
            except (OSError, ValueError) as e:
                resumen["errores"].append(f"{periodo}: {e}")
        elif ev["motivo_error"]:
            resumen["errores"].append(f"{periodo}: {ev['motivo_error']}")
        elif not ev["puede_publicar"] and not ev["ok"]:
            # No se puede publicar y no hay fondos ok: marcar como sondeado sin datos
            if periodo not in control.get("sondeados_sin_datos", []):
                control.setdefault("sondeados_sin_datos", []).append(periodo)
                # Solo persistir si el control ya existe (hay datos publicados)
                if cfg.control.exists():
                    json_atomico(cfg.control, control)
        print(
            f"::notice title=FI EEFF::{periodo}: {ev['ok']} fondos validados, {ev['rechazados']} rechazados, "
            f"{len(ev['pendientes'])} pendientes; eventos {json.dumps(cuenta, ensure_ascii=False)}; "
            f"diagnóstico {json.dumps(diagnostico, ensure_ascii=False)}",
            flush=True,
        )
        if freno or time.monotonic() >= deadline:
            break
    if publicar and control.get("periodos"):
        from fi.scripts.catalogos_eeff import actualizar_catalogos

        actualizar_catalogos(cfg.raiz, cfg.docs)
    json_atomico(cfg.cache / "resumen.json", resumen)
    return resumen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desde", default=None, help="primer cierre (AAAA-MM); default: autodescubre el más antiguo disponible en CMF")
    ap.add_argument("--hasta")
    ap.add_argument("--minutos", type=float, default=270)
    ap.add_argument("--hilos", type=int, default=16, help="descargas simultáneas (máx 32)")
    ap.add_argument("--max-periodos", type=int, default=0)
    ap.add_argument("--refrescar-todo", action="store_true")
    ap.add_argument("--sin-publicar", action="store_true")
    ap.add_argument("--solo-catalogos", action="store_true")
    args = ap.parse_args(argv)
    if args.solo_catalogos:
        from fi.scripts.catalogos_eeff import actualizar_catalogos

        actualizar_catalogos(RAIZ, Config().docs)
        return 0
    res = correr(
        minutos=args.minutos,
        hilos=args.hilos,
        desde=args.desde,
        hasta=args.hasta,
        max_periodos=args.max_periodos,
        forzar=args.refrescar_todo,
        publicar=not args.sin_publicar,
    )
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"publicado={'true' if res['publicados'] else 'false'}\n")
    for e in res["errores"]:
        print(f"::error title=FI EEFF::{e}")
    # Un fallo posterior no borra cierres ya validados; el auditor de salida sigue siendo obligatorio.
    return 1 if res["errores"] and not res["publicados"] else 0


if __name__ == "__main__":
    sys.exit(main())
