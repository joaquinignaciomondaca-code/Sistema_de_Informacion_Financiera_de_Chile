"""Revisión de cobertura FIRES/FINRE, de solo lectura sobre los datos publicados.

Distingue padrón histórico de vigencia actual y fondos con EEFF en un cierre.
Con --red coteja las cuatro listas CMF, consulta cada ausencia en ambos tipos,
comprueba VI/NV para los no vigentes y lee las fechas de los faltantes vigentes.
No descarga XML, no elude negativas de descarga, no publica ni modifica Parquet.
Toda respuesta ambigua/error de red queda pendiente, nunca como ausencia.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from fi.scripts import eeff_xml as xml
from fi.scripts.actualizar_eeff import url_ficha

TIPOS_FONDO = {
    "FINRE": "Fondo de Inversión No Rescatable",
    "FIRES": "Fondo de Inversión Rescatable",
}
URL_LISTA = "https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado={estado}&entidad={tipo}"
ESTADOS = ("ok", "sin_informacion", "rechazado", "pendiente")
IDENTIFICACION = (
    "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={run}"
    "&tipoentidad={tipo}&vig={vig}&control=svs&pestania=1"
)


def normalizar(texto):
    return (
        " ".join(
            "".join(
                c
                for c in unicodedata.normalize("NFKD", texto.lower())
                if not unicodedata.combining(c)
            ).split()
        )
        .strip()
        .rstrip(":")
        .strip()
    )


def tipo_de(texto):
    # Comparación exacta: «No Rescatable» también contiene «Rescatable».
    return {"rescatable": "FIRES", "no rescatable": "FINRE"}.get(normalizar(texto))


def fecha_de(texto):
    if not texto.strip():
        return None
    try:
        d, m, y = (int(x) for x in texto.strip().split("/"))
        return date(y, m, d).isoformat()
    except ValueError as e:
        raise xml.ErrorTransitorio(
            f"fecha de identificación inválida: {texto!r}"
        ) from e


def leer_identificacion(raw, run):
    soup = BeautifulSoup(xml.decodificar(raw), "html.parser")
    valores = {}
    for tr in soup.select("table tr"):
        celdas = tr.find_all(["td", "th"], recursive=False)
        if len(celdas) == 2:
            valores[normalizar(celdas[0].get_text(" ", strip=True))] = celdas[
                1
            ].get_text(" ", strip=True)
    rut = valores.get("r.u.n. del fondo", "").replace(".", "").upper()
    if not re.fullmatch(rf"{re.escape(run)}-[0-9K]", rut):
        raise xml.ErrorTransitorio("la identificación no declara el RUN solicitado")
    tipo = tipo_de(valores.get("tipo de fondo de inversion", ""))
    if tipo is None:
        raise xml.ErrorTransitorio("la identificación no declara un tipo FI reconocido")
    return {
        "run": run,
        "tipo_declarado": tipo,
        "nombre": valores.get("nombre fondo inversion"),
        "vigencia_declarada": valores.get("vigencia"),
        "estado_liquidacion": valores.get("estado (indica si fondo esta liquidado)"),
        "fecha_reglamento": fecha_de(
            valores.get(
                "fecha resolucion de aprobacion del reglamento interno del fondo", ""
            )
        ),
        "fecha_inicio_operaciones": fecha_de(
            valores.get("fecha inicio operaciones", "")
        ),
        "fecha_termino_operaciones": fecha_de(
            valores.get("fecha termino operaciones", "")
        ),
    }


def leer_lista(raw, tipo, vig):
    if tipo not in TIPOS_FONDO or vig not in ("VI", "NV"):
        raise ValueError("tipo/vigencia de lista inválidos")
    soup = BeautifulSoup(xml.decodificar(raw), "html.parser")
    tablas = {
        id(th.find_parent("table")): th.find_parent("table")
        for th in soup.find_all("th")
        if th.get_text(" ", strip=True) == "R.U.T."
        and th.find_parent("table") is not None
    }
    if len(tablas) != 1:
        raise xml.ErrorTransitorio(f"lista {tipo}/{vig} no contiene la tabla esperada")
    tabla = next(iter(tablas.values()))
    filas, vistos = [], set()
    estado = "Vigente" if vig == "VI" else "No Vigente"
    for tr in tabla.find_all("tr"):
        celdas = tr.find_all("td", recursive=False)
        if not celdas:
            continue
        f = [c.get_text(" ", strip=True) for c in celdas]
        if len(f) != 4 or not re.fullmatch(r"\d+-[0-9kK]", f[0].strip()):
            raise xml.ErrorTransitorio(
                f"fila incompleta/inesperada en lista {tipo}/{vig}"
            )
        run = f[0].split("-")[0]
        if run in vistos or f[3].strip() != estado:
            raise xml.ErrorTransitorio(
                f"lista {tipo}/{vig}: RUN duplicado o vigencia contradictoria"
            )
        vistos.add(run)
        filas.append(
            {
                "run_fondo": run,
                "rut_fondo_dv": f[0].strip().upper(),
                "nombre_fondo": f[1],
                "administradora": f[2],
                "tipo_entidad": tipo,
                "estado_vigencia": estado,
            }
        )
    if not filas:
        raise xml.ErrorTransitorio(f"lista {tipo}/{vig} vacía")
    return filas


def clasificar_sondeo(raw, run, periodo):
    soup = BeautifulSoup(xml.decodificar(raw), "html.parser")
    # La ficha del tipo incorrecto puede responder únicamente «Sin información.».
    # Eso significa sin ficha para esa categoría, no ausencia de EEFF del cierre.
    if (
        any(
            normalizar(h.get_text(" ", strip=True)).rstrip(".") == "sin informacion"
            for h in soup.select("h4")
        )
        and soup.select_one("#datos_ent") is None
    ):
        return {"estado": "sin_ficha"}
    estado, archivo = xml.clasificar_ficha(raw, periodo)
    datos = soup.select_one("#datos_ent")
    texto = datos.get_text(" ", strip=True) if datos is not None else ""
    rut = re.search(
        r"(?:R\.?U\.?T\.?|R\.?U\.?N\.?)\s*:?\s*(\d+)-([0-9kK])\b", texto, re.IGNORECASE
    )
    if rut is not None and rut.group(1) != run:
        raise xml.ErrorTransitorio("la ficha financiera identifica otro RUN")
    if archivo is not None and not archivo.endswith(f"_{run}.xml"):
        raise xml.ErrorTransitorio("el enlace FIEF corresponde a otro RUN")
    if estado == "sin_enlace":
        raise xml.ErrorTransitorio("ficha financiera sin enlace ni ausencia fechada")
    if estado == "sin_informacion" and rut is None:
        # Ocurre al pedir un no vigente con vig=VI. No equivale a una ausencia
        # identificada: se contrasta también NV y la otra categoría.
        return {"estado": "sin_identificacion", "ausencia_fechada_en_respuesta": True}
    return {
        "estado": estado,
        "archivo": archivo,
        "run_encabezado": rut.group(1) if rut else None,
    }


def cobertura_local(docs, periodo):
    xml.fin_periodo(periodo)
    registro = json.loads(
        (docs / "fi_registro_fondos_universo.json").read_text(encoding="utf-8")
    )
    todos = json.loads((docs / "fi_eeff_control.json").read_text(encoding="utf-8"))[
        "periodos"
    ]
    control = todos[periodo]
    regs = control["registros"]
    indice = {r["run_fondo"]: r for r in registro}
    if len(indice) != len(registro):
        raise ValueError("padrón local con RUN duplicados")
    if set(regs) != set(indice):
        raise ValueError(
            "el censo publicado y el padrón local no contienen los mismos RUN"
        )
    filas = []
    for run, f in sorted(indice.items(), key=lambda kv: int(kv[0])):
        r = regs[run]
        if (
            f["tipo_entidad"] not in TIPOS_FONDO
            or r["tipo_entidad"] != f["tipo_entidad"]
        ):
            raise ValueError(
                f"{run}: tipo no reconocido o distinto entre padrón y control"
            )
        if r["estado"] not in ESTADOS or f["estado_vigencia"] not in (
            "Vigente",
            "No Vigente",
        ):
            raise ValueError(f"{run}: estado/vigencia desconocidos")
        filas.append(
            {**f, "estado_eeff": r["estado"], "motivo_exclusion": r.get("motivo")}
        )
    aceptados = {r["run_fondo"] for r in filas if r["estado_eeff"] == "ok"}
    for tabla in ("balance", "resultados"):
        actuales = pq.read_table(
            docs / f"fi_{tabla}/{periodo}.parquet",
            columns=["run_fondo", "tipo_entidad", "contexto"],
        ).to_pylist()
        tipos = {
            (f["run_fondo"], f["tipo_entidad"])
            for f in actuales
            if f["contexto"] == "PeriodoActual"
        }
        if {run for run, tipo in tipos} != aceptados:
            raise ValueError(f"{tabla}: fondos actuales distintos del censo aceptado")
        if any(tipo != indice[run]["tipo_entidad"] for run, tipo in tipos):
            raise ValueError(f"{tabla}: tipo incorrecto en los datos publicados")
    tabla = []
    for tipo in TIPOS_FONDO:
        for vig in ("Vigente", "No Vigente"):
            fs = [
                f
                for f in filas
                if (f["tipo_entidad"], f["estado_vigencia"]) == (tipo, vig)
            ]
            conteos = Counter(f["estado_eeff"] for f in fs)
            tabla.append(
                {
                    "tipo_entidad": tipo,
                    "vigencia_actual": vig,
                    "censados": len(fs),
                    **{e: conteos[e] for e in ESTADOS},
                }
            )
    return {
        "periodo": periodo,
        "alcance": "fondos públicos FIRES/FINRE, no fondos privados no reportantes",
        "advertencia_vigencia": "El padrón indica vigencia actual, no vigencia histórica al cierre.",
        "cierre_historico_completo": False,
        "periodos_publicados": sorted(todos),
        "entradas_sha256": {
            str(p.relative_to(docs)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                docs / "fi_registro_fondos_universo.json",
                docs / "fi_eeff_control.json",
                docs / f"fi_balance/{periodo}.parquet",
                docs / f"fi_resultados/{periodo}.parquet",
            )
        },
        "resumen_local": tabla,
        "fondos": filas,
    }


def motivo_temporal(identificacion, periodo):
    fin = xml.fin_periodo(periodo).isoformat()
    inicio = identificacion.get("fecha_inicio_operaciones")
    termino = identificacion.get("fecha_termino_operaciones")
    if inicio and inicio > fin:
        return "inicio_posterior_al_cierre"
    if termino and termino < fin:
        return "termino_anterior_al_cierre"
    if "liquidacion" in normalizar(identificacion.get("nombre") or "") or normalizar(
        identificacion.get("estado_liquidacion") or ""
    ) in ("liquidado", "en liquidacion"):
        return "en_liquidacion_sin_eeff_del_cierre"
    if not inicio:
        return "fecha_inicio_no_informada"
    return "inicio_anterior_al_cierre_sin_eeff"


class Fuentes:
    def __init__(self, destino, deadline, fetcher=None, previo=None):
        self.destino, self.deadline = destino, deadline
        self.fetcher = fetcher or self.descargar
        self.previas = {}
        if previo:
            red = previo.get("revision_cmf", {})
            fuentes = list(red.get("listas", []))
            for r in red.get("revisiones", []):
                fuentes.extend(r["sondeos"])
                if "identificacion" in r:
                    fuentes.append(r["identificacion"])
            self.previas = {
                r["url"]: r
                for r in fuentes
                if r.get("sha256") and r.get("estado") != "pendiente"
            }
        (destino / "fuentes").mkdir(parents=True, exist_ok=True)

    def descargar(self, url):
        ultimo = None
        for intento in range(2):
            if time.monotonic() >= self.deadline:
                raise TimeoutError("tiempo de revisión agotado")
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; SIFChile/1.0)",
                        "Accept-Encoding": "identity",
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read(xml.MAX_XML + 1)
                if not raw or len(raw) > xml.MAX_XML:
                    raise xml.ErrorTransitorio("respuesta vacía o demasiado grande")
                return raw
            except (OSError, xml.ErrorTransitorio) as e:
                ultimo = e
                if intento == 0:
                    time.sleep(1)
        raise xml.ErrorTransitorio(str(ultimo))

    def consultar(self, url, parser):
        meta = {
            "url": url,
            "revisado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        try:
            if time.monotonic() >= self.deadline:
                raise TimeoutError("tiempo de revisión agotado")
            ruta = (
                self.destino
                / "fuentes"
                / (hashlib.sha256(url.encode()).hexdigest() + ".html")
            )
            anterior = self.previas.get(url)
            raw = ruta.read_bytes() if anterior and ruta.exists() else None
            if (
                raw is not None
                and hashlib.sha256(raw).hexdigest() == anterior["sha256"]
            ):
                meta["revisado_utc"] = anterior["revisado_utc"]
                meta["cache_sha256_verificado"] = True
            else:
                raw = self.fetcher(url)
            meta["sha256"] = hashlib.sha256(raw).hexdigest()
            meta["bytes"] = len(raw)
            (
                self.destino
                / "fuentes"
                / (hashlib.sha256(url.encode()).hexdigest() + ".html")
            ).write_bytes(raw)
            return {**meta, **parser(raw)}
        except (OSError, ValueError) as e:
            return {**meta, "estado": "pendiente", "error": str(e)}


def cotejar_registro(locales, nuevos):
    por_run = defaultdict(list)
    for f in nuevos:
        por_run[f["run_fondo"]].append(f)
    local = {r["run_fondo"]: r for r in locales}
    # Un mismo RUN puede figurar en VI y NV simultáneamente (9251, muestra real).
    # Contarlo una sola vez no autoriza a elegir una vigencia arbitraria.
    univocos = {run: fs[0] for run, fs in por_run.items() if len(fs) == 1}
    ambiguos = [
        {"run": run, "registros": fs}
        for run, fs in sorted(por_run.items(), key=lambda kv: int(kv[0]))
        if len(fs) > 1
    ]
    tipos_ambiguos = [
        r["run"]
        for r in ambiguos
        if len({f["tipo_entidad"] for f in r["registros"]}) > 1
    ]
    compartidos = sorted(set(local) & set(por_run), key=int)
    return {
        "filas_listas_cmf": len(nuevos),
        "fondos_cmf": len(por_run),
        "registros_ambiguos": ambiguos,
        "tipos_ambiguos": tipos_ambiguos,
        "altas_fuera_del_padron_local": [
            univocos[r] for r in sorted(set(univocos) - set(local), key=int)
        ],
        "altas_ambiguas": [r for r in ambiguos if r["run"] not in local],
        "ausentes_del_registro_actual": sorted(set(local) - set(por_run), key=int),
        "cambios_tipo": [
            {
                "run": run,
                "local": local[run]["tipo_entidad"],
                "cmf": fs[0]["tipo_entidad"],
            }
            for run in compartidos
            if (fs := por_run[run])
            and len({f["tipo_entidad"] for f in fs}) == 1
            and local[run]["tipo_entidad"] != fs[0]["tipo_entidad"]
        ],
        "cambios_vigencia": [
            {
                "run": run,
                "local": local[run]["estado_vigencia"],
                "cmf": univocos[run]["estado_vigencia"],
            }
            for run in compartidos
            if run in univocos
            and local[run]["estado_vigencia"] != univocos[run]["estado_vigencia"]
        ],
    }


def revisar_red(
    informe,
    destino,
    minutos=30,
    hilos=6,
    solo_vigentes=False,
    fetcher=None,
    previo=None,
):
    fuente = Fuentes(destino, time.monotonic() + minutos * 60, fetcher, previo)
    locales = informe["fondos"]
    listas, nuevas = [], []
    for tipo in TIPOS_FONDO:
        for vig in ("VI", "NV"):
            url = URL_LISTA.format(tipo=tipo, estado=vig)
            r = fuente.consultar(
                url,
                lambda raw, t=tipo, v=vig: {
                    "estado": "ok",
                    "fondos": leer_lista(raw, t, v),
                },
            )
            fs = r.pop("fondos", [])
            anterior = sum(
                f["tipo_entidad"] == tipo
                and f["estado_vigencia"] == ("Vigente" if vig == "VI" else "No Vigente")
                for f in locales
            )
            if r["estado"] == "ok" and len(fs) < anterior * 0.9:
                r.update(
                    estado="pendiente",
                    error="lista oficial reducida >10%; no se acepta como censo completo",
                )
            r.update(tipo_entidad=tipo, vigencia=vig, fondos=len(fs))
            listas.append(r)
            nuevas.extend(fs)
    registro = None
    if all(r["estado"] == "ok" for r in listas):
        try:
            registro = cotejar_registro(locales, nuevas)
        except ValueError as e:
            registro = {"error": str(e)}
    extras = registro.get("altas_fuera_del_padron_local", []) if registro else []
    objetivo = [
        f
        for f in locales
        if f["estado_eeff"] == "sin_informacion"
        and (not solo_vigentes or f["estado_vigencia"] == "Vigente")
    ]
    objetivo += [{**f, "estado_eeff": "fuera_del_padron_local"} for f in extras]
    periodo = informe["periodo"]

    def revisar(f):
        run, tipo = f["run_fondo"], f["tipo_entidad"]
        vig = "VI" if f["estado_vigencia"] == "Vigente" else "NV"
        otro = "FIRES" if tipo == "FINRE" else "FINRE"
        consultas = [(tipo, "VI"), (otro, "VI")]
        if vig == "NV":
            consultas.extend(((tipo, "NV"), (otro, "NV")))
        probes = []
        for t, v in consultas:
            url = url_ficha(run, t, periodo, v)
            r = fuente.consultar(url, lambda raw: clasificar_sondeo(raw, run, periodo))
            probes.append({**r, "tipo_consultado": t, "vig_consultada": v})
        r = {
            "run": run,
            "tipo_padron": tipo,
            "vigencia_actual": f["estado_vigencia"],
            "estado_publicado": f["estado_eeff"],
            "sondeos": probes,
        }
        if vig == "VI":
            url = IDENTIFICACION.format(run=run, tipo=tipo, vig=vig)
            ident = fuente.consultar(
                url, lambda raw: {"estado": "ok", **leer_identificacion(raw, run)}
            )
            r["identificacion"] = ident
            if ident["estado"] == "ok":
                r["situacion_temporal_declarada"] = motivo_temporal(ident, periodo)
                r["tipo_coincide_identificacion"] = ident["tipo_declarado"] == tipo
        return r

    revisiones = []
    with ThreadPoolExecutor(max_workers=hilos) as pool:
        futuros = [pool.submit(revisar, f) for f in objetivo]
        for fut in as_completed(futuros):
            revisiones.append(fut.result())
            if len(revisiones) % 50 == 0:
                print(
                    f"Cobertura: {len(revisiones)}/{len(objetivo)} fondos contrastados",
                    flush=True,
                )
    revisiones.sort(key=lambda r: int(r["run"]))
    pendientes = []
    auxiliares_pendientes = []
    for r in revisiones:
        vig_correcta = "VI" if r["vigencia_actual"] == "Vigente" else "NV"
        relevantes = [p for p in r["sondeos"] if p["vig_consultada"] == vig_correcta]
        primaria = next(
            p for p in relevantes if p["tipo_consultado"] == r["tipo_padron"]
        )
        if (
            any(p["estado"] == "pendiente" for p in relevantes)
            or primaria["estado"] not in ("sin_informacion", "xml")
            or r.get("identificacion", {}).get("estado") == "pendiente"
        ):
            pendientes.append(r["run"])
        auxiliares_pendientes.extend(
            {"run": r["run"], **p}
            for p in r["sondeos"]
            if p["vig_consultada"] != vig_correcta and p["estado"] == "pendiente"
        )
    enlaces_otro = [
        r["run"]
        for r in revisiones
        if any(
            p["estado"] == "xml" and p["tipo_consultado"] != r["tipo_padron"]
            for p in r["sondeos"]
        )
    ]
    enlaces_propio = [
        r["run"]
        for r in revisiones
        if any(
            p["estado"] == "xml" and p["tipo_consultado"] == r["tipo_padron"]
            for p in r["sondeos"]
        )
    ]
    enlaces_nv = [
        r["run"]
        for r in revisiones
        if r["sondeos"][0]["estado"] != "xml"
        and any(
            p["estado"] == "xml" and p["vig_consultada"] == "NV" for p in r["sondeos"]
        )
    ]
    informe["revision_cmf"] = {
        "alcance": "solo ausencias vigentes y altas"
        if solo_vigentes
        else "todas las ausencias del censo y altas",
        "listas": listas,
        "cotejo_registro": registro,
        "fondos_contrastados": len(revisiones),
        "revision_completa": not pendientes
        and all(r["estado"] == "ok" for r in listas)
        and registro is not None
        and not registro.get("error")
        and not registro.get("tipos_ambiguos")
        and not registro.get("altas_ambiguas"),
        "fondos_pendientes": pendientes,
        "consultas_auxiliares_pendientes": auxiliares_pendientes,
        "enlace_en_otro_tipo": enlaces_otro,
        "enlace_en_tipo_del_padron": enlaces_propio,
        "enlace_solo_cambiando_vigencia": enlaces_nv,
        "tipos_identificacion_discrepantes": [
            r["run"]
            for r in revisiones
            if r.get("tipo_coincide_identificacion") is False
        ],
        "situacion_faltantes_vigentes": dict(
            sorted(
                Counter(
                    r.get("situacion_temporal_declarada", "identificacion_pendiente")
                    for r in revisiones
                    if r["vigencia_actual"] == "Vigente"
                    and r["estado_publicado"] != "fuera_del_padron_local"
                ).items()
            )
        ),
        "revisiones": revisiones,
    }
    return informe


def markdown(informe):
    periodo = informe["periodo"]
    lineas = [
        f"# Revisión de cobertura de fondos de inversión — {periodo}",
        "",
        "## Rescatables y no rescatables",
        "",
        "Los datos publicados incluyen **FIRES (rescatables)** y **FINRE (no rescatables)**.",
        "El padrón incluye fondos vigentes y no vigentes. Estar registrado no implica tener un envío en cada cierre.",
        "",
        "| Tipo | Vigencia actual | Padrón | Con EEFF | Sin información del cierre | Excluidos | Pendientes |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in informe["resumen_local"]:
        lineas.append(
            f"| {r['tipo_entidad']} | {r['vigencia_actual']} | {r['censados']} | {r['ok']} | {r['sin_informacion']} | {r['rechazado']} | {r['pendiente']} |"
        )
    lineas += [
        "",
        "**Vigencia actual, no histórica:** esta tabla no afirma cuáles estaban activos al cierre.",
        (
            "Solo está cargado el cierre indicado; falta completar la serie histórica."
            if len(informe.get("periodos_publicados", [periodo])) == 1
            else "Esta revisión se limita al cierre indicado, no certifica la completitud de toda la historia."
        )
        + " No se deben fabricar filas de cero para fondos sin envío.",
        "",
    ]
    red = informe.get("revision_cmf")
    if red:
        lineas += [
            "## Contraste directo con la CMF",
            "",
            f"- Alcance: {red['alcance']}; **{red['fondos_contrastados']}** fondos.",
            f"- Revisión completa: **{'sí' if red['revision_completa'] else 'no; existen consultas o listas pendientes'}**.",
            f"- Fondos con consultas pendientes en su vigencia correcta: **{len(red['fondos_pendientes'])}**.",
            f"- Consultas auxiliares (vigencia incorrecta) pendientes: **{len(red.get('consultas_auxiliares_pendientes', []))}**; se conservan como tales, no como ausencias.",
            f"- Ausencias/altas con enlace FIEF en el otro tipo: **{len(red['enlace_en_otro_tipo'])}**.",
            f"- Ausencias/altas con enlace en su tipo: **{len(red['enlace_en_tipo_del_padron'])}**.",
            f"- Enlaces recuperables al cambiar VI por NV: **{len(red['enlace_solo_cambiando_vigencia'])}**.",
            f"- Identificaciones cuyo tipo difiere del padrón: **{len(red['tipos_identificacion_discrepantes'])}**.",
            "",
        ]
        reg = red.get("cotejo_registro")
        if reg and "error" not in reg:
            lineas += [
                (
                    f"Registro CMF cotejado: **{reg['fondos_cmf']}** RUN únicos en **{reg.get('filas_listas_cmf', reg['fondos_cmf'])}** filas; "
                    f"**{len(reg['altas_fuera_del_padron_local'])}** altas fuera del padrón local y "
                    f"**{len(reg['cambios_tipo'])}** cambios de tipo."
                ),
                "",
            ]
        if reg and "error" not in reg:
            if reg.get("registros_ambiguos"):
                lineas += [
                    "**Ambigüedad de vigencia en el registro oficial:** "
                    + ", ".join(r["run"] for r in reg["registros_ambiguos"])
                    + ". Cada RUN se cuenta una sola vez, sin asignarle una vigencia arbitraria.",
                    "",
                ]
            if reg.get("altas_fuera_del_padron_local"):
                lineas += ["### Fondos fuera de la copia local del padrón", ""]
                por_run = {r["run"]: r for r in red["revisiones"]}
                for f in reg["altas_fuera_del_padron_local"]:
                    i = por_run.get(f["run_fondo"], {}).get("identificacion", {})
                    lineas.append(
                        f"- **{f['run_fondo']} ({f['tipo_entidad']}) — {f['nombre_fondo']}**. Inicio declarado: {i.get('fecha_inicio_operaciones') or 'no informado'}. La incorporación al padrón no supone publicar cifras sin un XML validado."
                    )
                lineas.append("")
        if (
            red["revision_completa"]
            and not red["enlace_en_otro_tipo"]
            and not red["tipos_identificacion_discrepantes"]
            and reg
            and not reg.get("cambios_tipo")
        ):
            lineas += [
                "**Resultado del contraste:** en el alcance revisado no se recuperan fondos por intercambiar rescatable/no rescatable. No se está omitiendo una de las dos categorías.",
                "",
            ]
        lineas += [
            "### Fechas y situación declaradas de los faltantes vigentes",
            "",
            "| Situación declarada | Fondos |",
            "|---|---:|",
        ]
        for motivo, n in red["situacion_faltantes_vigentes"].items():
            lineas.append(f"| {motivo} | {n} |")
        lineas += [
            "",
            "Una fecha de inicio vacía significa **no informada**, no prueba que el fondo nunca haya operado. Estar en liquidación o haber terminado operaciones no prueba por sí solo una exención de reportar.",
            "",
            "### Detalle de faltantes vigentes",
            "",
            "| RUN | Tipo | Fondo | Inicio declarado | Término declarado | Situación |",
            "|---|---|---|---|---|---|",
        ]
        nombres = {r["run_fondo"]: r["nombre_fondo"] for r in informe["fondos"]}
        for r in red["revisiones"]:
            if (
                r["vigencia_actual"] != "Vigente"
                or r["estado_publicado"] == "fuera_del_padron_local"
            ):
                continue
            i = r.get("identificacion", {})
            nombre = (i.get("nombre") or nombres.get(r["run"], "")).replace("|", "\\|")
            lineas.append(
                f"| {r['run']} | {r['tipo_padron']} | {nombre} | {i.get('fecha_inicio_operaciones') or 'No informada'} | {i.get('fecha_termino_operaciones') or 'No informada'} | {r.get('situacion_temporal_declarada', 'Pendiente')} |"
            )
    else:
        lineas += [
            "**Alcance:** cruce local de padrón, control y ambos Parquet. Todavía no hay un contraste de todas las ausencias en ambos tipos contra la CMF.",
            "",
        ]
    lineas += ["", "## Exclusiones conocidas", ""]
    for r in informe["fondos"]:
        if r["estado_eeff"] == "rechazado":
            lineas.append(
                f"- **{r['run_fondo']} ({r['tipo_entidad']})**: {r.get('motivo_exclusion') or 'Ver control publicado'}."
            )
    lineas += [
        "",
        "## Trazabilidad y límites",
        "",
        "- Esta revisión no modifica estados financieros, no convierte moneda, no rellena ceros y no descarga XML rechazados.",
        "- El JSON adjunto conserva las URL, fecha y SHA-256 de cada respuesta revisada. Los originales quedan en staging/artifact, fuera de los datos publicados.",
        "- `sin_ficha` en la categoría alternativa no equivale a `sin_informacion` del cierre. Desafíos, cortes y errores quedan pendientes.",
        "- La vida observada de carteras no se usa como prueba de vida legal ni para omitir fondos de las consultas.",
        "- Prioridad pendiente: completar el histórico, mantener actualizado el padrón y resolver las exclusiones y las ausencias con inicio anterior al cierre sin inventar cifras.",
        "",
    ]
    return "\n".join(lineas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docs", type=Path, default=ROOT / "docs/outputs/fi")
    ap.add_argument("--periodo", default="2026-06")
    ap.add_argument("--out", type=Path, default=ROOT / ".local-data/fi_eeff_cobertura")
    ap.add_argument("--red", action="store_true")
    ap.add_argument(
        "--reanudar",
        action="store_true",
        help="reusar respuestas previas de staging solo si su SHA-256 coincide",
    )
    ap.add_argument("--solo-vigentes", action="store_true")
    ap.add_argument("--minutos", type=float, default=30)
    ap.add_argument("--hilos", type=int, choices=range(1, 9), default=6)
    ap.add_argument(
        "--exportar-log",
        action="store_true",
        help="exportar JSON comprimido en bloques para recuperación del artifact",
    )
    args = ap.parse_args(argv)
    if args.minutos <= 0:
        ap.error("--minutos debe ser positivo")
    informe = cobertura_local(args.docs, args.periodo)
    informe["revisado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    args.out.mkdir(parents=True, exist_ok=True)
    if args.red:
        anterior = (
            json.loads((args.out / "revision.json").read_text())
            if args.reanudar and (args.out / "revision.json").exists()
            else None
        )
        if anterior and anterior.get("periodo") != args.periodo:
            ap.error("el cierre del staging no coincide con --periodo")
        revisar_red(
            informe,
            args.out,
            args.minutos,
            args.hilos,
            args.solo_vigentes,
            previo=anterior,
        )
    serializado = json.dumps(informe, ensure_ascii=False, indent=2) + "\n"
    (args.out / "revision.json").write_text(serializado, encoding="utf-8")
    (args.out / "revision.md").write_text(markdown(informe), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in informe.items() if k not in ("fondos", "revision_cmf")},
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.red:
        print(
            json.dumps(
                {k: v for k, v in informe["revision_cmf"].items() if k != "revisiones"},
                ensure_ascii=False,
                indent=2,
            )
        )
    if args.exportar_log:
        b64 = base64.b64encode(gzip.compress(serializado.encode(), mtime=0)).decode()
        for n in range(0, len(b64), 4000):
            print(f"FI_COBERTURA_B64 {n // 4000:04d} {b64[n : n + 4000]}", flush=True)
    return 1 if args.red and not informe["revision_cmf"]["revision_completa"] else 0


if __name__ == "__main__":
    sys.exit(main())
