"""Lee un estado financiero en Markdown (conversión de PDF o transcripción).

No rellena notas con porcentajes. Si el documento no trae la tabla, la fila
no existe.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipelines.eeff.canon import clase_cuenta, familia_nota, parse_monto_chileno

_NOTA_HEAD = re.compile(
    r"(?:^|\n)#{0,3}\s*(?:nota|NOTA)\s+(\d{1,2})\s*[.\-–:]?\s*([^\n|]{3,140})",
    re.IGNORECASE,
)
_TOC = re.compile(
    r"Nota\s+(\d{1,2})\s*[.\-–]\s*(.+?)\s{2,}(\d{1,3})\s*$",
    re.IGNORECASE,
)
_PIPE_ROW = re.compile(r"^\s*[^|#].*\|.*$")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c)


def parse_documento(text: str, meta: dict) -> dict:
    """Devuelve balance, resultados, indice de notas y lineas de notas."""
    balance = _parse_pipe_block(text, "BALANCE", "balance", meta)
    resultados = _parse_pipe_block(text, "RESULTADOS", "resultado", meta)
    if not balance:
        balance = _parse_tablas_crudas(text, "balance", meta)
    if not resultados:
        resultados = _parse_tablas_crudas(text, "resultado", meta)
    indice = _parse_indice(text, meta)
    notas = _parse_nota_tablas(text, meta)
    return {
        "balance": balance,
        "resultados": resultados,
        "indice": indice,
        "notas": notas,
    }


def _parse_pipe_block(text: str, titulo: str, estado: str, meta: dict) -> list[dict]:
    match = re.search(rf"^##\s+{titulo}\s*$", text, re.MULTILINE)
    if not match:
        return []
    resto = text[match.end():]
    corte = re.search(r"^##\s+", resto, re.MULTILINE)
    bloque = resto[: corte.start()] if corte else resto
    filas = []
    headers = None
    for line in bloque.splitlines():
        if "|" not in line or line.strip().startswith("#"):
            continue
        cells = _cells(line)
        if _is_separator(cells):
            continue
        if headers is None:
            headers = [c.lower() for c in cells]
            continue
        row = dict(zip(headers, cells))
        nombre = row.get("nombre") or row.get("nombre_cuenta") or ""
        if not nombre:
            continue
        monto = parse_monto_chileno(row.get("monto_miles") or row.get("monto") or "")
        comp = parse_monto_chileno(row.get("comparativo_miles") or row.get("comparativo") or "")
        if monto is None:
            continue
        filas.append(_linea_estado(meta, estado, nombre, row.get("nota") or "", row.get("clase") or clase_cuenta(nombre, estado), monto, comp))
    return filas


def _linea_estado(meta, estado, nombre, nota, clase, monto, comp):
    nota_ref = re.sub(r"[^\d]", "", str(nota or "")) or ""
    return {
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta["periodo"],
        "fecha_corte": meta.get("fecha_corte", ""),
        "tipo_eeff": meta.get("tipo_eeff", ""),
        "estado": estado,
        "nombre_cuenta": nombre.strip(),
        "nota_ref": nota_ref,
        "clase": clase or clase_cuenta(nombre, estado),
        "monto_miles_clp": round(float(monto), 2),
        "monto_m_clp": round(float(monto) / 1000.0, 2),
        "monto_comparativo_miles_clp": None if comp is None else round(float(comp), 2),
        "fuente": meta.get("fuente", "EEFF PDF/MD"),
    }


def _parse_tablas_crudas(text: str, estado: str, meta: dict) -> list[dict]:
    """Respaldo para un MD salido de pymupdf, sin bloque pipe."""
    claves = ("situacion financiera", "situación financiera") if estado == "balance" else ("resultado",)
    lines = text.splitlines()
    filas = []
    activo = False
    for i, line in enumerate(lines):
        folded = line.lower()
        if any(k in folded for k in claves) and ("estado" in folded or line.startswith("#")):
            activo = True
            continue
        if activo and line.startswith("#") and not any(k in folded for k in claves):
            if filas:
                break
        if not activo or "|" not in line:
            continue
        cells = _cells(line)
        if len(cells) < 2 or _is_separator(cells):
            continue
        montos = [(idx, parse_monto_chileno(c)) for idx, c in enumerate(cells) if parse_monto_chileno(c) is not None and re.search(r"\d", c)]
        if len(montos) < 1:
            continue
        nombre = cells[0]
        if not nombre or nombre.lower() in {"activos", "pasivos", "nota"}:
            continue
        if re.fullmatch(r"[\d.\-]+", nombre):
            continue
        nota = ""
        for c in cells[1:montos[0][0]]:
            if re.fullmatch(r"\d{1,2}", c):
                nota = c
        filas.append(_linea_estado(meta, estado, nombre, nota, clase_cuenta(nombre, estado), montos[0][1], montos[1][1] if len(montos) > 1 else None))
    return filas


def _parse_indice(text: str, meta: dict) -> list[dict]:
    encontrados = []
    vistos = set()
    bloque = re.search(r"^##\s+NOTAS_INDICE\s*$([\s\S]*?)(?=^##\s+|\Z)", text, re.MULTILINE)
    if bloque:
        for line in bloque.group(1).splitlines():
            if "|" not in line or line.strip().startswith("#"):
                continue
            cells = _cells(line)
            if not cells or not cells[0].isdigit():
                continue
            numero = int(cells[0])
            titulo = cells[1] if len(cells) > 1 else ""
            pagina = cells[2] if len(cells) > 2 and cells[2].isdigit() else ""
            _agregar_indice(encontrados, vistos, meta, numero, titulo, pagina)
    for match in _TOC.finditer(text):
        _agregar_indice(encontrados, vistos, meta, int(match.group(1)), match.group(2).strip(" ."), match.group(3))
    for match in _NOTA_HEAD.finditer(text):
        titulo = re.sub(r"\s+", " ", match.group(2)).strip(" -–.")
        if len(titulo) < 4 or titulo.lower().startswith("a los estados"):
            continue
        _agregar_indice(encontrados, vistos, meta, int(match.group(1)), titulo, "")
    return encontrados


def _agregar_indice(encontrados, vistos, meta, numero, titulo, pagina):
    if numero in vistos or not titulo:
        return
    vistos.add(numero)
    encontrados.append({
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta["periodo"],
        "numero_nota": numero,
        "titulo_nota": titulo[:180],
        "pagina": str(pagina or ""),
        "nota_canonica": familia_nota(titulo),
        "extraida": 0,
        "fuente": meta.get("fuente", "EEFF PDF/MD"),
    })


def _parse_nota_tablas(text: str, meta: dict) -> list[dict]:
    """Tablas que siguen a un encabezado Nota N. Un número se lee una sola vez."""
    filas = []
    vistos = set()
    for match in re.finditer(r"^##\s+NOTA\s+(\d{1,2})\s+([^\n]*)$", text, re.MULTILINE):
        numero = int(match.group(1))
        titulo = match.group(2).strip() or f"Nota {numero}"
        resto = text[match.end():]
        corte = re.search(r"^##\s+", resto, re.MULTILINE)
        bloque = resto[: corte.start()] if corte else resto
        filas.extend(_filas_tabla_nota(bloque, meta, numero, titulo))
        vistos.add(numero)
    partes = _NOTA_HEAD.split(text)
    if len(partes) > 1:
        i = 1
        while i + 2 < len(partes):
            numero = int(partes[i])
            titulo = re.sub(r"\s+", " ", partes[i + 1]).strip(" -–.")
            cuerpo = partes[i + 2]
            siguiente = _NOTA_HEAD.search(cuerpo)
            if siguiente:
                cuerpo = cuerpo[: siguiente.start()]
            if numero not in vistos and ("nota" not in titulo.lower() or len(titulo) > 8):
                filas.extend(_filas_tabla_nota(cuerpo, meta, numero, titulo))
                vistos.add(numero)
            i += 3
    return filas


_MONTO_HDR = re.compile(r"m\$|saldo|neto|coloc|provisi|monto|bruto|capital", re.IGNORECASE)


def _fecha_header(header: str) -> str:
    match = re.search(r"(\d{2})[./](\d{2})[./](\d{4})", header or "")
    if match:
        dia, mes, anio = match.groups()
        return f"{anio}-{mes}-{dia}"
    match = re.search(r"(20\d{2})", header or "")
    return match.group(1) if match else ""


def _columnas_monto(headers: list[str]) -> list[int]:
    return [i for i, header in enumerate(headers) if i > 0 and _MONTO_HDR.search(header or "")]


def _primaria_y_comparativo(headers: list[str], idxs: list[int]) -> tuple[int, int | None]:
    """El neto (o el saldo de la fecha más nueva) es el monto. El otro saldo es comparativo."""
    def puntaje(idx: int) -> tuple:
        header = (headers[idx] or "").lower()
        score = 0
        if "neto" in header:
            score += 100
        if "saldo" in header:
            score += 40
        return (score, _fecha_header(headers[idx]), -idx)

    primaria = max(idxs, key=puntaje)
    header_p = (headers[primaria] or "").lower()
    if "neto" in header_p:
        return primaria, None
    candidatos = [
        i for i in idxs
        if i != primaria and ("saldo" in (headers[i] or "").lower() or "compar" in (headers[i] or "").lower())
    ]
    if not candidatos:
        return primaria, None
    candidatos.sort(key=lambda i: _fecha_header(headers[i]))
    if _fecha_header(headers[candidatos[0]]) and _fecha_header(headers[candidatos[0]]) < _fecha_header(headers[primaria]):
        return primaria, candidatos[0]
    if "compar" in (headers[candidatos[0]] or "").lower():
        return primaria, candidatos[0]
    return primaria, None


def _filas_tabla_nota(bloque: str, meta: dict, numero: int, titulo: str) -> list[dict]:
    familia = familia_nota(titulo)
    out = []
    headers = None
    cols = []
    for line in bloque.splitlines():
        if "|" not in line:
            continue
        cells = _cells(line)
        if _is_separator(cells) or not cells:
            continue
        if headers is None:
            if _columnas_monto(cells) or cells[0].lower().startswith(("concepto", "nombre", "descripcion", "composicion", "detalle")):
                headers = cells
                cols = _columnas_monto(cells)
                continue
            montos = [parse_monto_chileno(c) for c in cells]
            numericos = [i for i, monto in enumerate(montos) if monto is not None and re.search(r"\d", cells[i])]
            if not numericos:
                continue
            concepto = cells[0]
            if not concepto:
                continue
            out.append(_fila_nota(meta, numero, titulo, familia, concepto, "", montos[numericos[0]], montos[numericos[1]] if len(numericos) > 1 else None))
            continue
        if not cols:
            cols = [i for i, monto in enumerate(parse_monto_chileno(c) for c in cells) if monto is not None and i > 0]
        if not cols:
            continue
        concepto = cells[0].strip()
        if not concepto:
            continue
        valores = []
        for idx in cols:
            token = cells[idx] if idx < len(cells) else ""
            valores.append(parse_monto_chileno(token))
        if all(v is None for v in valores):
            continue
        primaria, comp = _primaria_y_comparativo(headers, cols)
        pos = {idx: n for n, idx in enumerate(cols)}
        monto = valores[pos[primaria]]
        if monto is None:
            continue
        comparativo = None if comp is None else valores[pos[comp]]
        extras = []
        for idx in cols:
            if idx in {primaria, comp}:
                continue
            valor = valores[pos[idx]]
            if valor is None:
                continue
            nombre = headers[idx] if idx < len(headers) else f"col{idx}"
            extras.append(f"{nombre}={valor:.0f}")
        out.append(_fila_nota(meta, numero, titulo, familia, concepto, "; ".join(extras), monto, comparativo))
    return out


def _fila_nota(meta, numero, titulo, familia, concepto, detalle, monto, comp):
    return {
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta["periodo"],
        "numero_nota": numero,
        "titulo_nota": titulo[:180],
        "nota_canonica": familia,
        "concepto": concepto.strip()[:180],
        "detalle": (detalle or "").strip()[:180],
        "monto_miles_clp": round(float(monto), 2),
        "monto_comparativo_miles_clp": None if comp is None else round(float(comp), 2),
        "moneda": "CLP",
        "fuente": meta.get("fuente", "EEFF PDF/MD"),
        "calidad": "extraida_documento",
    }


def cargar_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    meta = {
        "rut": "",
        "razon_social": "",
        "periodo": "",
        "fecha_corte": "",
        "tipo_eeff": "",
        "fuente": "EEFF PDF/MD",
        "url_pdf": "",
        "url_visualizacion": "",
    }
    for line in text.splitlines():
        if not line.startswith("<!--") and not line.startswith("# "):
            if line.startswith("rut:"):
                meta["rut"] = line.split(":", 1)[1].strip()
            elif line.startswith("razon_social:"):
                meta["razon_social"] = line.split(":", 1)[1].strip()
            elif line.startswith("periodo:"):
                meta["periodo"] = line.split(":", 1)[1].strip()
            elif line.startswith("fecha_corte:"):
                meta["fecha_corte"] = line.split(":", 1)[1].strip()
            elif line.startswith("tipo_eeff:"):
                meta["tipo_eeff"] = line.split(":", 1)[1].strip()
            elif line.startswith("fuente:"):
                meta["fuente"] = line.split(":", 1)[1].strip()
            elif line.startswith("url_pdf:"):
                meta["url_pdf"] = line.split(":", 1)[1].strip()
            elif line.startswith("url_visualizacion:"):
                meta["url_visualizacion"] = line.split(":", 1)[1].strip()
        if line.startswith("## "):
            break
    return meta, text
