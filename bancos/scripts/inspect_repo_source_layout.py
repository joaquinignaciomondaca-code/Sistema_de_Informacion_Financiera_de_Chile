"""Muestreo no publicador del formato real B1 en ZIP mensuales CMF.

Sólo imprime encabezado y cuentas REPO de hasta dos bancos de períodos dados.
No modifica datos publicados ni avanza checkpoints. Los montos son públicos.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import zipfile
from pathlib import Path

from bancos.scripts import probe_repos_zip_cmf as probe

CODES = {"1160000", "2160000", "141000000", "243000000"}


def sample(blob: bytes, period: str, url: str, wanted: tuple[str, ...] = ("001", "012")) -> dict:
    if not probe.trusted_zip(url) or len(blob) > probe.MAX_ZIP:
        raise ValueError("ZIP fuera del dominio CMF o excede límite")
    result = {"periodo": period, "url": url, "sha256": hashlib.sha256(blob).hexdigest(),
              "archivos": []}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for info in z.infolist():
            match = probe.BALANCE_TXT.fullmatch(Path(info.filename).name)
            if not match or match[4] not in wanted:
                continue
            if f"{match[2]}-{match[3]}" != period or info.file_size > probe.MAX_TXT:
                raise ValueError("Período o tamaño de TXT inválido")
            raw = z.read(info)
            lines = raw.decode("latin-1").splitlines()
            rows = [line for line in lines if line.split("\t", 1)[0].strip() in CODES]
            result["archivos"].append({"nombre": Path(info.filename).name,
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "primeras_lineas": lines[:3], "filas_repo": rows,
                "anchos_campos": dict(collections.Counter(len(line.split("\t")) for line in lines))})
    if not result["archivos"]:
        raise ValueError("Sin archivos B1/B2 de la muestra")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("periods", nargs="+", help="Meses AAAA-MM")
    args = parser.parse_args()
    found, conflicts = probe.resolve_links()
    for period in args.periods:
        if not probe.PERIOD.fullmatch(period) or period not in found or period in conflicts:
            raise ValueError(f"ZIP sin vínculo inequívoco: {period}")
        doc = sample(probe.read_public(found[period], probe.MAX_ZIP), period, found[period])
        print(json.dumps(doc, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
