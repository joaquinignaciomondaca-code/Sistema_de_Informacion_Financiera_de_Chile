"""Diagnóstico incremental NO PUBLICADOR de ZIP de balances bancarios CMF.

Los ZIP de MB1/MB2 se enlazan públicamente desde la CMF; no requieren
USER_CMF/PASSWORD_CMF ni API key. Descubre enlaces, descarga solo los meses
pendientes desde un checkpoint y extrae líneas crudas B1 de un banco.
NO interpreta cuentas, unidades, RUT ni convierte a USD. Nunca toca docs/outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = "https://www.cmfchile.cl/portal/estadisticas/626/w4-propertyvalue-32901.html"
CATALOG = ROOT / "bancos/scripts/cmf_bancos_packages.json"
LEGACY = ROOT / "docs/outputs/bancos/bancos_repos_saldos_series.json"
CHECKPOINT = ROOT / ".local-data/checkpoint/bancos-repo-probe/last_period.json"
REPORT = ROOT / ".local-data/review/bancos/repo_zip_probe.json"
MONTHS = {m: n for n, m in enumerate(("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"), 1)}
MONTHS["setiembre"] = 9
MAX_ZIP = 8_000_000
MAX_TXT = 2_000_000
MAX_MONTHS = 12
PERIOD = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
BALANCE_TXT = re.compile(r"^(b[12])(\d{4})(\d{2})(\d{3})\.txt$", re.I)
# Son pistas extraídas del script V2 facilitado por el usuario, NO validación
# de que esas cuentas representen el rubro REPO en cada plan contable.
CANDIDATES = {"1160000", "2160000", "141000000", "243000000"}


CONTEXT_CHARS = 300


def clean(value: str) -> str:
    """Colapsa espacios y elimina etiquetas/entidades antes de cualquier salida."""
    text = re.sub(r"<[^>]*>", " ", value)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    return re.sub(r"\s+", " ", text).strip()


class ZipLinks(HTMLParser):
    """Recolecta anclas con varias señales de período, en orden documental.

    La página CMF real no siempre rotula el mes dentro del `<a>` del ZIP: puede
    dejarlo en el atributo `title`, en el `alt` de un ícono anidado, o sólo en
    el encabezado que acompaña al enlace (a menudo dentro de otra ancla). Por
    eso se conserva un flujo ordenado de anclas y textos, y el período se
    resuelve después sin inventarlo a partir del id del artículo.
    """

    def __init__(self):
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.stream: list[tuple[str, object]] = []
        self.current: dict[str, str] | None = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a":
            self.current = {"href": attributes.get("href") or "", "texto": "", "atributos": ""}
            parts = [attributes[key] for key in ("title", "aria-label", "aria-labelledby") if attributes.get(key)]
            self.current["atributos"] = " ".join(parts)
        elif self.current is not None and tag in ("img", "span", "svg", "use"):
            parts = [attributes[key] for key in ("alt", "title", "aria-label") if attributes.get(key)]
            if parts:
                self.current["atributos"] = " ".join([self.current["atributos"], *parts]).strip()

    def handle_data(self, data):
        if self.current is not None:
            self.current["texto"] = " ".join([self.current["texto"], data]).strip()
        else:
            self.stream.append(("t", data))

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.stream.append(("a", self.current))
            self.current = None


def context_for(stream: list[tuple[str, object]], anchor: dict, limit: int = CONTEXT_CHARS) -> str:
    """Texto posterior al enlace hasta el próximo enlace ZIP (su encabezado)."""
    start = next((i for i, (kind, item) in enumerate(stream) if kind == "a" and item is anchor), None)
    if start is None:
        return ""
    parts: list[str] = []
    size = 0
    for kind, item in stream[start + 1:]:
        if kind == "a":
            other = item
            assert isinstance(other, dict)
            if trusted_zip(urllib.parse.urljoin(INDEX, str(other.get("href") or ""))):
                break
            text = clean(f"{other.get('texto') or ''} {other.get('atributos') or ''}")
        else:
            text = clean(str(item))
        if not text:
            continue
        parts.append(text)
        size += len(text)
        if size >= limit:
            break
    return " ".join(parts)[:limit]


def trusted_zip(url: str) -> bool:
    p = urllib.parse.urlsplit(url)
    return p.scheme == "https" and p.hostname == "www.cmfchile.cl" and p.path.startswith("/portal/estadisticas/626/") and p.path.endswith(".zip")


def read_public(url: str, limit: int) -> bytes:
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname != "www.cmfchile.cl":
        raise ValueError("Enlace fuera del dominio CMF permitido")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 MonitorFinancieroChile/1.0", "Accept": "text/html,application/zip"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError(f"CMF HTTP {response.status}")
                data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("Respuesta excede el límite de tamaño permitido")
            return data
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"CMF HTTP {exc.code}; URL {p.path}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            # Nunca tratar un error de red como mes sin datos ni escribir un
            # checkpoint de éxito. No hay credenciales en estas URLs.
            raise RuntimeError(f"Error de conexión CMF ({type(exc).__name__}); URL {p.path}") from None
    raise RuntimeError("Descarga CMF inconclusa")


MONTH_PATTERN = re.compile(r"(" + "|".join(MONTHS) + r")\.?\s*(?:de\s+)?(20\d{2})", re.I)


def period_of(link: dict, stream: list[tuple[str, object]]) -> tuple[str, str] | None:
    """Devuelve (período, señal usada) sin inventar meses.

    Orden de precedencia: rótulo del enlace -> atributos (`title`, `alt`) del
    ancla o de su ícono -> encabezado que sigue al enlace. Nunca se deduce el
    mes desde el id del artículo, la fecha de publicación ni el nombre del
    archivo del href.
    """
    for signal in ("texto", "atributos"):
        raw = link.get(signal)
        if not raw:
            continue
        match = MONTH_PATTERN.search(clean(str(raw)))
        if match:
            return f"{int(match.group(2)):04d}-{MONTHS[match.group(1).lower()]:02d}", signal
    for signal in ("contexto",):
        raw = context_for(stream, link)
        if not raw:
            continue
        match = MONTH_PATTERN.search(clean(str(raw)))
        if match:
            return f"{int(match.group(2)):04d}-{MONTHS[match.group(1).lower()]:02d}", signal
    return None


def discover(html: str, strict: bool = True, conflicts_out: set[str] | None = None) -> dict[str, str]:
    parser = ZipLinks()
    parser.feed(html)
    found: dict[str, str] = {}
    conflicts: set[str] = set()
    zip_links = []
    for link in parser.links:
        href = link.get("href")
        if not href:
            continue
        url = urllib.parse.urljoin(INDEX, str(href))
        if not trusted_zip(url):
            continue
        zip_links.append((url, link))
        resolved = period_of(link, parser.stream)
        if not resolved:
            continue
        # El índice CMF contiene un enlace de marzo 2019 cuyo atributo de
        # descarga dice erróneamente «Marzo 2020». Si el encabezado de la ficha
        # contradice el rótulo, NO asignar este ZIP a ninguno de los dos meses.
        # Una fecha de publicación puede diferir del período y no se usa aquí.
        heading = re.search(r"Balance y Estado de (?:Situaci[oó]n|Resultados) Bancos\s+"
                            r"(" + "|".join(MONTHS) + r")\s+(20\d{2})",
                            context_for(parser.stream, link), re.I)
        if heading:
            heading_period = f"{int(heading.group(2)):04d}-{MONTHS[heading.group(1).lower()]:02d}"
            if heading_period != resolved[0]:
                continue
        period = resolved[0]
        if period in found and found[period] != url:
            conflicts.add(period)
            found.pop(period)
        elif period not in conflicts:
            found[period] = url
    if conflicts_out is not None:
        conflicts_out.update(conflicts)
    if conflicts and strict:
        raise ValueError(f"Dos ZIP diferentes para {sorted(conflicts)}; requiere revisión")
    if not found:
        # Diagnóstico sin volcar HTML potencialmente dinámico ni URLs externas.
        # Puede ser una página de protección, un redirect, o un cambio de
        # formato. Sólo registrar metadatos estructurales para revisar la causa.
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        clean_title = clean(title.group(1))[:100] if title else "(sin título)"
        # Señales ya limpias (sin etiquetas) de algunas anclas ZIP: permiten
        # corregir el parser sin descargar el HTML ni publicar datos.
        muestra = [{"ruta": urllib.parse.urlsplit(url).path,
                    "texto": clean(str(link.get("texto") or ""))[:80],
                    "atributos": clean(str(link.get("atributos") or ""))[:80],
                    "contexto": context_for(parser.stream, link)[:120]}
                   for url, link in zip_links[:5]]
        raise ValueError(f"No se pudieron descubrir ZIP mensuales en índice CMF; "
                         f"título={clean_title!r}, caracteres={len(html)}, "
                         f"enlaces={len(parser.links)}, ZIP={len(zip_links)}, "
                         f"muestra={json.dumps(muestra, ensure_ascii=False)}, "
                         f"sha256={hashlib.sha256(html.encode('utf-8')).hexdigest()[:16]}")
    return found


def last_complete(today: date) -> str:
    y, m = today.year, today.month - 1
    if m == 0:
        y, m = y - 1, 12
    return f"{y:04d}-{m:02d}"


def select(found: dict[str, str], published_last: str, checkpoint_last: str | None, today: date, manual: str | None) -> list[str]:
    if manual:
        if not PERIOD.fullmatch(manual) or manual > last_complete(today):
            raise ValueError("Mes manual inválido o aún incompleto (AAAA-MM)")
        if manual not in found:
            raise ValueError(f"No hay URL CMF para {manual} en el índice ni catálogo")
        return [manual]
    start = max(published_last, checkpoint_last or published_last)
    periods = sorted(p for p in found if start <= p <= last_complete(today))
    if not periods:
        # El cron diario no debe fallar solo porque la CMF no publicó un mes
        # nuevo. Reexaminar la última versión conocida, sin mover el avance.
        if start in found and start <= last_complete(today):
            periods = [start]
        else:
            raise ValueError(f"No hay ZIP publicados desde {start} en el índice actual")
    # Un vacío intermedio puede significar que el índice no recogió un enlace.
    # No saltar meses ni adelantar el checkpoint ante ese caso.
    expected = []
    year, month = map(int, start.split("-"))
    while f"{year:04d}-{month:02d}" <= periods[-1]:
        expected.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    if periods != expected:
        raise ValueError(f"Faltan ZIP entre {start} y {periods[-1]}; no avanzar checkpoint")
    if len(periods) > MAX_MONTHS:
        raise ValueError(f"{len(periods)} ZIP pendientes exceden el límite {MAX_MONTHS}; revisar catálogo/checkpoint")
    return periods


def inspect_zip(blob: bytes, period: str, bank: str, url: str) -> dict:
    """Conserva cuentas crudas candidatas B1/B2 sin convertir ni sumar nada."""
    if not trusted_zip(url):
        raise ValueError("ZIP de origen no confiable")
    if not re.fullmatch(r"\d{3}", bank):
        raise ValueError("Código de banco inválido")
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        raise ValueError(f"ZIP inválido para {period}") from None
    files = []
    with z:
        for info in z.infolist():
            match = BALANCE_TXT.fullmatch(Path(info.filename).name)
            if not match or f"{match[2]}-{match[3]}" != period or match[4] != bank:
                continue
            if info.file_size > MAX_TXT or info.file_size == 0:
                raise ValueError(f"Balance {info.filename} vacío o excesivamente grande")
            # z.read verifica el CRC; no se descomprime en disco.
            try:
                lines = z.read(info).decode("latin-1").splitlines()
            except (RuntimeError, zipfile.BadZipFile) as exc:
                raise ValueError(f"No se pudo verificar balance {info.filename}: {type(exc).__name__}") from None
            entries = []
            for line in lines:
                cols = line.split("\t")
                code = cols[0].strip() if cols else ""
                # Además del nivel principal, incluir subcuentas para estudiar
                # composición; esos prefijos NO son sumables entre sí.
                if code in CANDIDATES or re.fullmatch(r"(?:116|216)\d{4,6}|(?:141|243)\d{6}", code):
                    entries.append({"codigo_cuenta": code, "campos_crudos": [c.strip() for c in cols[1:]]})
            files.append({"archivo": Path(info.filename).name, "filas": len(lines), "cuentas_candidatas": entries})
    if not files:
        raise ValueError(f"Sin B1/B2 para banco {bank} mes {period}; no guardar checkpoint")
    # Un archivo por formato y banco. No elegir arbitrariamente una versión.
    if len({f["archivo"][:2].lower() for f in files}) != len(files):
        raise ValueError(f"B1/B2 duplicados para {bank} en {period}; revisar ZIP")
    return {"periodo": period, "url_zip": url, "sha256_zip": hashlib.sha256(blob).hexdigest(),
            "archivos_balance": sorted(files, key=lambda f: f["archivo"])}


def resolve_links() -> tuple[dict[str, str], set[str]]:
    """Cruza índice actual y catálogo histórico; no decide entre versiones dudosas."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    found = {}
    ambiguous = set()
    for x in catalog:
        if not PERIOD.fullmatch(x["period"]) or not trusted_zip(x["url"]):
            continue
        period = x["period"]
        if period in found and found[period] != x["url"]:
            # El catálogo tiene versiones duplicadas; exigir que la página
            # oficial resuelva el conflicto antes de consultar ese mes.
            ambiguous.add(period)
            found.pop(period)
        elif period not in ambiguous:
            found[period] = x["url"]
    index_conflicts: set[str] = set()
    html = read_public(INDEX, 4_000_000).decode("utf-8", errors="replace")
    try:
        current = discover(html, strict=False, conflicts_out=index_conflicts)
    except ValueError as exc:
        # Página CMF pudo cambiar, responder una portada vacía, o renderizar
        # enlaces sólo con JS. No sustituir por URL supuesta ni marcar mes vacío.
        raise ValueError("Índice CMF accesible pero sin enlaces ZIP reconocibles; "
                         f"{exc}") from None
    for conflict in index_conflicts:
        found.pop(conflict, None)
    found.update(current)
    unresolved = (ambiguous - current.keys()) | index_conflicts
    return found, unresolved


def run(manual: str | None = None, bank: str = "001", output: Path = REPORT, checkpoint: Path = CHECKPOINT, today: date | None = None) -> list[dict]:
    today = today or date.today()
    found, unresolved = resolve_links()
    published = json.loads(LEGACY.read_text(encoding="utf-8"))
    latest = max(r["periodo"] for r in published)
    saved = json.loads(checkpoint.read_text(encoding="utf-8"))["periodo"] if checkpoint.exists() else None
    if saved is not None and not PERIOD.fullmatch(saved):
        raise ValueError("Checkpoint de diagnóstico inválido")
    periods = select(found, latest, saved, today, manual)
    if manual in unresolved or (not manual and any(latest <= p <= last_complete(today) for p in unresolved)):
        raise ValueError(f"Catálogo ZIP ambiguo para meses {sorted(unresolved)}; revisar versiones antes de continuar")
    reference = {r["periodo"]: r for r in published if r["codigo_institucion"] == bank}
    results = []
    for period in periods:
        url = found[period]
        report = inspect_zip(read_public(url, MAX_ZIP), period, bank, url)
        old = reference.get(period)
        report["referencia_legacy_mm_clp"] = ({"activo": old["repo_activo_mm_clp"],
                                                "pasivo": old["repo_pasivo_mm_clp"]} if old else None)
        results.append(report)
    # Se escribe sólo si TODAS las descargas y parsers tuvieron éxito.
    document = {"estado": "diagnostico_no_validado", "origen": INDEX,
                "nota": "Prefijos de cuentas exploratorios; NO son saldos REPO certificados ni sustituyen Parquet.",
                "banco": bank, "periodos": results}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not manual:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps({"periodo": periods[-1]}) + "\n", encoding="utf-8")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", help="Mes de calibración histórico, ej. 2021-12")
    parser.add_argument("--bank", default="001")
    args = parser.parse_args()
    try:
        results = run(args.period, args.bank)
    except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Diagnóstico ZIP incompleto: {exc}", file=sys.stderr)
        return 1
    print(f"ZIP revisados: {len(results)}; sin cambios en datos publicados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
