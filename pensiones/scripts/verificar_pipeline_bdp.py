"""Auto-verificación punta a punta del pipeline BDP sin datos oficiales.

Ejercita el código real del repositorio —asistente de captura, descargador,
extractor, auditoría y gate— sobre fuentes sintéticas servidas por un transporte
HTTP inyectado. El único punto sustituido es el socket: la validación de host, el
registro saneado, el inventario ZIP/CRC, el SHA-256, los sidecars, los lotes con
checkpoint, la cuarentena, las revisiones y el gate son las funciones reales.

No requiere red, no contacta a la Superintendencia y no certifica nada sobre
datos reales. Sirve para comprobar que el procedimiento sigue funcionando.

    python -m pensiones.scripts.verificar_pipeline_bdp

Trabaja en `.local-data/pensiones/bdp-verificacion/` y se niega a correr si ya
existen originales o staging reales, para no pisar una ingesta en curso.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

try:
    from . import download_bdp_packages as dl
    from .bdp_common import COLUMNS, OFFICIAL_LANDING_PAGE, PRIVATE_ROOT, ROOT, atomic_json, sha256_file
    from .registrar_captura_bdp import build_capture
except ImportError:  # ejecución directa desde pensiones/scripts/
    import download_bdp_packages as dl  # type: ignore

    from bdp_common import (  # type: ignore
        COLUMNS, OFFICIAL_LANDING_PAGE, PRIVATE_ROOT, ROOT, atomic_json, sha256_file,
    )
    from registrar_captura_bdp import build_capture  # type: ignore

EVIDENCIA_REAL = PRIVATE_ROOT / "pensiones/bdp/evidencia"
ORIGINALES_REALES = PRIVATE_ROOT / "pensiones/bdp/originales"
STAGING_REAL = PRIVATE_ROOT / "pensiones/bdp/staging"
SALON = PRIVATE_ROOT / "pensiones/bdp-verificacion"
ORIG = SALON / "originales"
STAGE = SALON / "staging"
CATALOGO = SALON / "catalogo.json"
TS = "2026-10-07T12:00:00Z"
PAQUETES = {
    "historico_1996_2005": (1996, 2005),
    "historico_2006_2015": (2006, 2015),
    "historico_2016_actualidad": (2016, 2026),
}
# ZZZ9 no existe en el catálogo de familias: debe caer en cuarentena.
CODIGOS = ["WNMV", "BTU", "ACC", "DPF", "SNT", "CFMV", "ETFA", "ZZZ9"]

_ok: list[str] = []
_fallos: list[str] = []


def chk(condicion: bool, etiqueta: str, detalle: str = "") -> None:
    (_ok if condicion else _fallos).append(etiqueta)
    print(f"  {'OK ' if condicion else 'FALLO'} {etiqueta}" + (f" | {detalle}" if detalle else ""))


def cli(*args: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-m", *args], cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def json_de(texto: str) -> Any:
    return json.loads(texto[texto.index("{"):])


def fila(fecha: str, afp: str, fondo: str, code: str, marca: str = "") -> list[str]:
    r = [fecha, afp, fondo, code] + [""] * (len(COLUMNS) - 4)
    r[4], r[5], r[8], r[9], r[10] = "SERIE-001", marca or "Emisor ñ", "UF", "736,9", "-319862208,9"
    return r


def make_zip(years: range, marca: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for year in years:
            s = io.StringIO()
            w = csv.writer(s, delimiter=";")
            w.writerow(COLUMNS)
            for mes in (3, 6, 9, 12):
                for i, code in enumerate(CODIGOS):
                    w.writerow(fila(f"{year}-{mes:02d}-28", ["HAB", "PROVIDA", "CAPITAL"][i % 3],
                                    ["A", "B", "C"][i % 3], code, marca))
            z.writestr(f"cartera_{year}.csv", s.getvalue().encode("utf-8-sig"))
    return buf.getvalue()


class FakeResponse:
    def __init__(self, data: bytes = b"", status: int = 200, headers: dict | None = None, url: str = ""):
        self._data, self._pos, self.status = data, 0, status
        self.headers = headers or {}
        self._url = url or OFFICIAL_LANDING_PAGE
        self.closed = False

    def geturl(self) -> str:
        return self._url

    def close(self) -> None:
        self.closed = True

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._data) - self._pos
        end = min(len(self._data), self._pos + size)
        out = self._data[self._pos:end]
        self._pos = end
        return out


class FakeOpener:
    def __init__(self, responses: list[FakeResponse]):
        self.responses, self.requests = list(responses), []

    def open(self, request: Any, timeout: int = 0) -> FakeResponse:
        self.requests.append(request.get_method())
        if not self.responses:
            raise AssertionError("solicitud HTTP inesperada")
        return self.responses.pop(0)


def get_resp(zbytes: bytes, url: str, etag: str) -> FakeResponse:
    return FakeResponse(zbytes, 200, {
        "Content-Type": "application/zip", "Content-Length": str(len(zbytes)),
        "ETag": etag, "Last-Modified": "Wed, 01 Oct 2026 12:00:00 GMT",
    }, url)


def main() -> int:
    if ORIGINALES_REALES.exists() or STAGING_REAL.exists():
        print(
            "No se ejecuta: ya existen originales o staging reales bajo "
            f"{PRIVATE_ROOT / 'pensiones/bdp'}. Esta verificación es sólo para un "
            "entorno sin ingesta en curso.",
            file=sys.stderr,
        )
        return 1
    if SALON.exists():
        shutil.rmtree(SALON)
    creadas: list[Path] = []
    try:
        return _verificar(creadas)
    finally:
        shutil.rmtree(SALON, ignore_errors=True)
        for ruta in creadas:
            ruta.unlink(missing_ok=True)


def _verificar(creadas: list[Path]) -> int:
    print("=" * 76)
    print("PASO 0 — Catálogo real, sin tocar la red")
    print("=" * 76)
    rc, out = cli("pensiones.scripts.download_bdp_packages", "--check-only")
    d = json_de(out)
    chk(rc == 0 and d["ready"] is False, "check-only responde ready=false",
        f"estado={d['estado']}")

    print("\n" + "=" * 76)
    print("PASOS 1-2 — Evidencia saneada con el asistente real")
    print("=" * 76)
    zbytes = {pid: make_zip(range(y0, y1 + 1)) for pid, (y0, y1) in PAQUETES.items()}
    urls: dict[str, str] = {}
    paquetes: list[dict[str, Any]] = []
    for pid in PAQUETES:
        url = f"https://www.spensiones.cl/apps/bdp/descargas/{pid}.zip"
        urls[pid] = url
        captura = build_capture(package_id=pid, request_url=url,
                                response_filename=f"{pid}.zip", captured_at=TS)
        ruta = EVIDENCIA_REAL / f"verificacion_{pid}.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(ruta, captura)
        creadas.append(ruta)
        paquetes.append({
            "id": pid, "descripcion": pid, "download_url": url,
            "expected_filename": f"{pid}.zip",
            "expected_sha256": hashlib.sha256(zbytes[pid]).hexdigest(),
            "captured_from": OFFICIAL_LANDING_PAGE, "captured_at": TS,
            "capture_evidence": str(ruta.relative_to(ROOT)),
            "capture_sha256": sha256_file(ruta),
        })
    chk(len(creadas) == 3, "build_capture generó 3 registros saneados de 8 campos")

    rc, out = cli("pensiones.scripts.registrar_captura_bdp", "--package-id", "historico_1996_2005",
                  "--request-url", urls["historico_1996_2005"] + "?token=abc",
                  "--response-filename", "x.zip", "--captured-at", TS)
    chk(rc == 1 and "Captura rechazada" in out, "rechaza URL con token y no escribe")

    atomic_json(CATALOGO, {"version": 1, "source_page": OFFICIAL_LANDING_PAGE,
                           "estado": "listo", "packages": paquetes})

    print("\n" + "=" * 76)
    print("PASO 3 — Descargador real con transporte inyectado")
    print("=" * 76)
    opener = FakeOpener([get_resp(zbytes[p["id"]], p["download_url"], '"rev1"') for p in paquetes])
    records = dl.download_catalog(CATALOGO, ORIG, opener=opener)
    chk(len(records) == 3 and all(r["download_status"] == "verified" for r in records),
        "descarga y verifica los 3 paquetes")
    chk(all(r["sha256"] == r["expected_sha256"] for r in records), "SHA-256 cotejado con el catálogo")
    chk(all(len(r["zip_csv_members"]) == len(range(*PAQUETES[r["package_id"]])) + 1 for r in records),
        "inventario de miembros CSV",
        ", ".join(f"{r['package_id']}={len(r['zip_csv_members'])}" for r in records))
    chk(all(r["redistribution_status"] == "not_reviewed" for r in records),
        "sidecar declara redistribution_status=not_reviewed")
    chk(sorted(p.name for p in ORIG.iterdir()) ==
        sorted([f"{p}.zip" for p in PAQUETES] + [f"{p}.zip.source.json" for p in PAQUETES]),
        "originales/ guarda <id>.zip y <id>.zip.source.json")

    print("\n" + "=" * 76)
    print("PASO 4 — Backfill: checkpoint (2), reanudación (0), sin fuente (3)")
    print("=" * 76)
    base = ["pensiones.scripts.extraer_carteras_afp", "--scan",
            str(ORIG.relative_to(ROOT)), "--output", str(STAGE.relative_to(ROOT)),
            "--filas-por-lote", "10000", "--minutos", "300"]
    rc1, out1 = cli(*base, "--max-lotes", "1")
    j1 = json_de(out1)
    chk(rc1 == 2 and j1["status"] == "incomplete" and j1["paquetes_procesados"] == [],
        "corrida acotada sale 2 y no activa el paquete", f"pendientes={j1['paquetes_pendientes']}")
    rc2, out2 = cli(*base, "--max-lotes", "0")
    j2 = json_de(out2)
    chk(rc2 == 0 and j2["status"] == "staging_complete", "reanudar completa",
        f"filas={j2['filas_activas']} miembros={j2['miembros_procesados_en_corrida']}")
    chk(j2["publicable"] is False, "el extractor nunca marca publicable")
    rc3, _ = cli(*base, "--max-lotes", "0")
    chk(rc3 == 0, "reingesta idempotente")
    rc4, _ = cli("pensiones.scripts.extraer_carteras_afp", "--scan", str(SALON / "vacio"),
                 "--output", str(SALON / "staging2"), "--max-lotes", "0", "--minutos", "1")
    chk(rc4 == 3, "sin originales sale 3, no 2", f"rc={rc4}")

    print("\n" + "=" * 76)
    print("PASO 5 — Auditoría")
    print("=" * 76)
    stage_rel = str(STAGE.relative_to(ROOT))
    rc, out = cli("pensiones.scripts.audit_carteras_afp", stage_rel)
    chk(rc == 1 and "cuarentena" in out, "falla sin --allow-quarantine (fail-closed)", f"rc={rc}")
    rc, out = cli("pensiones.scripts.audit_carteras_afp", stage_rel, "--allow-quarantine")
    a = json_de(out)
    chk(rc == 0 and a["estado"] == "cuarentena", "con el flag permite inspeccionar")
    chk(a["historico_completo_por_paquetes"] is True, "los 3 IDs están activos")
    chk(a["cobertura_historica_certificada"] is False, "la cobertura no se autocertifica")
    chk(a["publicable"] is False and a["publicacion_bloqueada"] is True, "publicable=False forzado")
    chk(sorted(a["paquetes_oficiales_verificados"]) == sorted(PAQUETES),
        "los 3 tienen sidecar oficial verificado")
    chk(a["codigos_no_clasificados"].get("ZZZ9") == 124,
        "código desconocido va a cuarentena, no se descarta",
        f"ZZZ9={a['codigos_no_clasificados'].get('ZZZ9')} filas")
    chk(a["cobertura"]["cortes_fuente_distintos"] == 124, "cobertura observada",
        json.dumps(a["cobertura"], ensure_ascii=False))

    print("\n" + "=" * 76)
    print("PASO 6 — Gate con staging auditado")
    print("=" * 76)
    rc, out = cli("pensiones.scripts.check_publicacion_bdp", "--staging", stage_rel)
    g = json_de(out)
    chk(g["ready"] is False, "el gate sigue bloqueado con todo el pipeline funcionando")
    chk(not any("sidecar" in r for r in g["razones"]),
        "ya no bloquea por sidecar; quedan sólo los criterios humanos", f"{len(g['razones'])} razones")
    chk(sum("Criterio pendiente" in r for r in g["razones"]) == 5, "los 5 criterios siguen pendientes")
    chk(g["publicacion_de_datos"] == "no ejecutada", "no se publicó nada")

    print("\n" + "=" * 76)
    print("EXTRA — Paquete revisado: HEAD, revisión previa e incremental")
    print("=" * 76)
    nuevo = make_zip(range(2006, 2016), marca="Emisor revisión 2")
    zbytes["historico_2006_2015"] = nuevo
    for p in paquetes:
        if p["id"] == "historico_2006_2015":
            p["expected_sha256"] = None  # SP no siempre publica hash
    atomic_json(CATALOGO, {"version": 1, "source_page": OFFICIAL_LANDING_PAGE,
                           "estado": "listo", "packages": paquetes})
    opener2 = FakeOpener([
        FakeResponse(b"", 304, {}, paquetes[0]["download_url"]),
        FakeResponse(b"", 200, {"Content-Type": "application/zip", "ETag": '"rev2"',
                                "Content-Length": "999999"}, paquetes[1]["download_url"]),
        get_resp(nuevo, paquetes[1]["download_url"], '"rev2"'),
        FakeResponse(b"", 304, {}, paquetes[2]["download_url"]),
    ])
    records2 = dl.download_catalog(CATALOGO, ORIG, opener=opener2)
    chk(opener2.requests.count("HEAD") == 3, "revalida con HEAD antes de re-descargar")
    chk(records2[0]["sha256"] == records[0]["sha256"], "el paquete sin cambios no se re-descarga")
    chk(records2[1]["sha256"] == hashlib.sha256(nuevo).hexdigest(), "el revisado se re-descarga")
    chk(bool(records2[1]["previous_archive"]) and (ORIG / "revisions").is_dir(),
        "conserva la revisión anterior", str(records2[1]["previous_archive"]))

    rc, out = cli(*base, "--max-lotes", "0", "--incremental")
    ji = json_de(out)
    chk(rc == 0 and ji["filas_activas"] == 992, "incremental no duplica filas",
        f"filas={ji['filas_activas']}")
    chk(sorted(ji["paquetes_procesados"]) == sorted(PAQUETES),
        "'paquetes_procesados' lista los activos, no los de la corrida")
    rc, out = cli("pensiones.scripts.extraer_carteras_afp",
                  str((ORIG / "historico_2006_2015.zip").relative_to(ROOT)),
                  "--output", stage_rel, "--filas-por-lote", "10000",
                  "--max-lotes", "0", "--minutos", "300", "--incremental")
    jo = json_de(out)
    chk(jo["miembros_procesados_en_corrida"] == 0,
        "reingestar la misma fuente no reprocesa miembros",
        f"miembros_en_corrida={jo['miembros_procesados_en_corrida']}")
    rc, out = cli("pensiones.scripts.audit_carteras_afp", stage_rel, "--allow-quarantine")
    af = json_de(out)
    chk(af["revisiones_auditadas"] == 41, "revisiones registradas por miembro",
        f"{af['revisiones_auditadas']} = 31 iniciales + 10 del paquete revisado")

    print("\n" + "=" * 76)
    print("AISLAMIENTO")
    print("=" * 76)
    chk(not (ROOT / "docs/outputs/pensiones/bdp").exists(), "no existe docs/outputs/pensiones/bdp")
    rc, _ = cli("pensiones.scripts.publish_bdp", "--staging", stage_rel)
    chk(rc != 0 and not (ROOT / "docs/outputs/pensiones/bdp").exists(),
        "publish_bdp se niega con el gate cerrado", f"rc={rc}")
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    lineas = [x for x in st.splitlines() if x.strip()]
    fugas = [x for x in lineas if ".local-data" in x or "docs/outputs/pensiones/bdp" in x
             or x.lower().endswith((".zip", ".parquet", ".csv"))]
    chk(not fugas, "Git no ve datos: ni .local-data ni ZIP/Parquet/CSV",
        f"{len(lineas)} cambios de código, 0 de datos")
    chk("bdp" not in (ROOT / "data_manifest.json").read_text(encoding="utf-8").lower(),
        "data_manifest.json sin referencias BDP")

    print("\n" + "=" * 76)
    print(f"RESULTADO: {len(_ok)} verificaciones OK, {len(_fallos)} fallos")
    for f in _fallos:
        print("  FALLÓ:", f)
    print("=" * 76)
    return 1 if _fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
