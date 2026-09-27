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


class ZipLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.text)))
            self.href = None
            self.text = []


def trusted_zip(url: str) -> bool:
    p = urllib.parse.urlsplit(url)
    return p.scheme == "https" and p.hostname == "www.cmfchile.cl" and p.path.startswith("/portal/estadisticas/626/") and p.path.endswith(".zip")


def read_public(url: str, limit: int) -> bytes:
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname != "www.cmfchile.cl":
        raise ValueError("Enlace fuera del dominio CMF permitido")
    req = urllib.request.Request(url, headers={"User-Agent": "MonitorFinancieroChile/1.0", "Accept": "text/html,application/zip"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"CMF HTTP {response.status}")
            data = response.read(limit + 1)
    except Exception as exc:
        # No hay credenciales en estas URLs; evitar logs extensos del servidor.
        raise RuntimeError(f"Error al descargar desde CMF ({type(exc).__name__})") from None
    if len(data) > limit:
        raise ValueError("Respuesta excede el límite de tamaño permitido")
    return data


def discover(html: str, strict: bool = True, conflicts_out: set[str] | None = None) -> dict[str, str]:
    parser = ZipLinks()
    parser.feed(html)
    found: dict[str, str] = {}
    conflicts: set[str] = set()
    for href, text in parser.links:
        url = urllib.parse.urljoin(INDEX, href)
        if not trusted_zip(url):
            continue
        match = re.search(r"(?:Descargar\s+)?(" + "|".join(MONTHS) + r")\s+(20\d{2})", text, re.I)
        if match:
            period = f"{int(match.group(2)):04d}-{MONTHS[match.group(1).lower()]:02d}"
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
        raise ValueError("No se pudieron descubrir ZIP mensuales en índice CMF")
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
    current = discover(read_public(INDEX, 4_000_000).decode("utf-8", errors="replace"),
                       strict=False, conflicts_out=index_conflicts)
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
