"""Lee un estado financiero en Markdown (conversión de PDF o transcripción).

No rellena notas con porcentajes. Si el documento no trae la tabla, la fila
no existe. Las notas comunes con esquema cerrado van a su tabla. Las otras
no se aplanan en una bolsa.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipelines.eeff.alias import ESQUEMAS_CERRADOS, clasificar_nota, cuenta_cara, fold
from pipelines.eeff.canon import clase_cuenta, parse_monto_chileno

_NOTA_HEAD = re.compile(
    r"(?:^|\n)#{0,3}\s*(?:nota|NOTA)\s+(\d{1,2})\s*[.\-–:]?\s*([^\n|]{3,180})",
    re.IGNORECASE,
)
_TOC = re.compile(
    r"Nota\s+(\d{1,2})\s*[.\-–]\s*(.+?)\s{2,}(\d{1,3})\s*$",
    re.IGNORECASE,
)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c)


def parse_documento(text: str, meta: dict) -> dict:
    balance = _parse_pipe_block(text, "BALANCE", "balance", meta)
    resultados = _parse_pipe_block(text, "RESULTADOS", "resultado", meta)
    if not balance:
        balance = _parse_tablas_crudas(text, "balance", meta)
    if not resultados:
        resultados = _parse_tablas_crudas(text, "resultado", meta)
    indice = _parse_indice(text, meta)
    tablas, pendientes = _extraer_comunes(text, meta)
    return {
        "balance": balance,
        "resultados": resultados,
        "indice": indice,
        "tablas": tablas,
        "pendientes": pendientes,
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
        filas.append(_linea_estado(
            meta, estado, nombre, row.get("nota") or "",
            row.get("clase") or clase_cuenta(nombre, estado), monto, comp,
        ))
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
        "cuenta_canonica": cuenta_cara(nombre, estado),
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
    for line in lines:
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
        montos = [
            (idx, parse_monto_chileno(c))
            for idx, c in enumerate(cells)
            if parse_monto_chileno(c) is not None and re.search(r"\d", c)
        ]
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
        filas.append(_linea_estado(
            meta, estado, nombre, nota, clase_cuenta(nombre, estado),
            montos[0][1], montos[1][1] if len(montos) > 1 else None,
        ))
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
    for match in re.finditer(r"^##\s+NOTA\s+(\d{1,2})\s+([^\n]*)$", text, re.MULTILINE):
        titulo = match.group(2).strip()
        if titulo:
            _agregar_indice(encontrados, vistos, meta, int(match.group(1)), titulo, "")
    return encontrados


def _agregar_indice(encontrados, vistos, meta, numero, titulo, pagina):
    if numero in vistos or not titulo:
        return
    vistos.add(numero)
    clas = clasificar_nota(titulo)
    encontrados.append({
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta["periodo"],
        "numero_nota": numero,
        "titulo_nota": titulo[:180],
        "pagina": str(pagina or ""),
        "nota_canonica": clas["tabla"] or clas["familia"],
        "tabla": clas["tabla"],
        "extraida": 0,
        "fuente": meta.get("fuente", "EEFF PDF/MD"),
    })


def _span_indice(text: str) -> tuple[int, int] | None:
    match = re.search(r"^##\s+NOTAS_INDICE\s*$[\s\S]*?(?=^##\s+|\Z)", text, re.MULTILINE)
    if not match:
        return None
    return match.start(), match.end()


def _secciones_nota(text: str) -> list[tuple[int, str]]:
    vistos = set()
    secciones = []
    indice = _span_indice(text)
    for match in re.finditer(r"^##\s+NOTA\s+(\d{1,2})\s+([^\n]*)$", text, re.MULTILINE):
        numero = int(match.group(1))
        titulo = match.group(2).strip() or f"Nota {numero}"
        resto = text[match.end():]
        corte = re.search(r"^##\s+", resto, re.MULTILINE)
        cuerpo = resto[: corte.start()] if corte else resto
        secciones.append((numero, titulo, cuerpo))
        vistos.add(numero)
    for match in _NOTA_HEAD.finditer(text):
        if indice and indice[0] <= match.start() < indice[1]:
            continue
        numero = int(match.group(1))
        if numero in vistos:
            continue
        titulo = re.sub(r"\s+", " ", match.group(2)).strip(" -–.")
        if len(titulo) < 4 or titulo.lower().startswith("a los estados"):
            continue
        resto = text[match.end():]
        siguiente = _NOTA_HEAD.search(resto)
        cuerpo = resto[: siguiente.start()] if siguiente else resto
        secciones.append((numero, titulo, cuerpo))
        vistos.add(numero)
    return secciones


def _extraer_comunes(text: str, meta: dict) -> tuple[dict, list[dict]]:
    tablas = {nombre: [] for nombre in ESQUEMAS_CERRADOS}
    pendientes = []
    periodo = meta.get("periodo") or (meta.get("fecha_corte") or "")[:7]
    for numero, titulo, cuerpo in _secciones_nota(text):
        clas = clasificar_nota(titulo)
        tabla = clas["tabla"]
        if not tabla:
            continue
        bloques = _bloques_tabla(cuerpo)
        if tabla not in ESQUEMAS_CERRADOS:
            if bloques:
                headers = _headers_de(bloques[0])
                pendientes.append({
                    "tabla": tabla,
                    "numero_nota": numero,
                    "titulo_nota": titulo[:180],
                    "encabezados": " | ".join(headers),
                    "motivo": "tabla vista, esquema no cerrado",
                })
            continue
        tomada = False
        for bloque in bloques:
            filas = _filas_esquema(bloque, meta, numero, titulo, tabla, periodo)
            if filas:
                tablas[tabla].extend(filas)
                tomada = True
                break
        if not tomada and bloques:
            headers = _headers_de(bloques[0])
            pendientes.append({
                "tabla": tabla,
                "numero_nota": numero,
                "titulo_nota": titulo[:180],
                "encabezados": " | ".join(headers),
                "motivo": "la tabla no trae el esquema cerrado",
            })
    return tablas, pendientes


def _bloques_tabla(bloque: str) -> list[list[str]]:
    actual = []
    tablas = []
    for line in bloque.splitlines():
        if "|" in line and not line.strip().startswith("#"):
            actual.append(line)
        elif actual:
            tablas.append(actual)
            actual = []
    if actual:
        tablas.append(actual)
    return tablas


def _headers_de(lineas: list[str]) -> list[str]:
    for line in lineas:
        cells = _cells(line)
        if cells and not _is_separator(cells):
            return cells
    return []


def _fecha_header(header: str) -> str:
    match = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", header or "")
    if match:
        dia, mes, anio = match.groups()
        return f"{anio}-{mes}-{dia}"
    match = re.search(r"(20\d{2})", header or "")
    return match.group(1) if match else ""


def _rol(header: str) -> str:
    blob = fold(header)
    if not blob:
        return ""
    if blob in {"concepto", "nombre", "detalle", "descripcion", "composicion", "producto"}:
        return "concepto"
    if "neto" in blob and "coloc" not in blob:
        return "neto"
    if "provision" in blob:
        return "provision"
    if "colocacion" in blob or "saldo bruto" in blob:
        return "colocacion"
    if "saldo" in blob:
        return "saldo"
    return ""


def _elegir(pares: list[tuple[int, str]], doc_periodo: str) -> tuple[int | None, int | None]:
    if not pares:
        return None, None
    actuales = [par for par in pares if par[1] and doc_periodo and par[1][:7] == doc_periodo]
    if actuales:
        actual = actuales[0][0]
    else:
        fechados = [par for par in pares if par[1]]
        actual = max(fechados, key=lambda par: par[1])[0] if fechados else pares[0][0]
    otros = [par for par in pares if par[0] != actual]
    if not otros:
        return actual, None
    fechados = [par for par in otros if par[1]]
    if fechados:
        return actual, min(fechados, key=lambda par: par[1])[0]
    return actual, otros[0][0]


def _es_total(concepto: str) -> int:
    blob = fold(concepto)
    if blob.startswith("total") or blob.startswith("subtotal"):
        return 1
    return 0


def _filas_esquema(lineas: list[str], meta: dict, numero: int, titulo: str, tabla: str, periodo: str) -> list[dict]:
    headers = None
    roles = []
    filas = []
    for line in lineas:
        cells = _cells(line)
        if not cells or _is_separator(cells):
            continue
        if headers is None:
            roles = [_rol(c) for c in cells]
            if not any(rol in {"saldo", "neto", "colocacion", "provision"} for rol in roles):
                continue
            headers = cells
            continue
        concepto_idx = next((i for i, rol in enumerate(roles) if rol == "concepto"), 0)
        concepto = cells[concepto_idx].strip() if concepto_idx < len(cells) else ""
        if not concepto:
            continue
        valores = {}
        for idx, rol in enumerate(roles):
            if not rol or rol == "concepto" or idx >= len(cells):
                continue
            valores.setdefault(rol, []).append((idx, _fecha_header(headers[idx])))
        montos = {
            idx: parse_monto_chileno(cells[idx]) if idx < len(cells) else None
            for idx, _ in (
                (i, rol) for i, rol in enumerate(roles) if rol and rol != "concepto"
            )
        }
        if tabla == "efectivo":
            actual, comp = _elegir(valores.get("saldo") or [], periodo)
            if actual is None or montos.get(actual) is None:
                continue
            filas.append(_base(meta, numero, titulo, concepto, {
                "saldo_miles": montos.get(actual),
                "saldo_comparativo_miles": None if comp is None else montos.get(comp),
            }))
        elif tabla == "deudores":
            if not valores.get("neto") and not (valores.get("colocacion") and valores.get("provision")):
                return []
            campos = {}
            for rol, destino in (
                ("colocacion", "colocacion_miles"),
                ("provision", "provision_miles"),
                ("neto", "neto_miles"),
            ):
                actual, comp = _elegir(valores.get(rol) or [], periodo)
                campos[destino] = None if actual is None else montos.get(actual)
                campos[destino.replace("_miles", "_comparativo_miles")] = None if comp is None else montos.get(comp)
            if campos.get("neto_miles") is None and campos.get("colocacion_miles") is None:
                continue
            filas.append(_base(meta, numero, titulo, concepto, campos))
    if tabla == "efectivo" and not any("saldo_miles" in row for row in filas):
        return []
    if tabla == "deudores" and filas and not any(row.get("neto_miles") is not None or row.get("colocacion_miles") is not None for row in filas):
        return []
    return filas


def _base(meta, numero, titulo, concepto, campos) -> dict:
    fila = {
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta["periodo"],
        "fecha_corte": meta.get("fecha_corte", ""),
        "tipo_eeff": meta.get("tipo_eeff", ""),
        "numero_nota": numero,
        "titulo_nota": titulo[:180],
        "concepto": concepto.strip()[:180],
        "es_total": _es_total(concepto),
        "fuente": meta.get("fuente", "EEFF PDF/MD"),
    }
    for clave, valor in campos.items():
        fila[clave] = None if valor is None else round(float(valor), 2)
    return fila


def cargar_md(path: Path) -> tuple[dict, str]:
    text = Path(path).read_text(encoding="utf-8")
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
        if line.startswith("## "):
            break
        clave = line.split(":", 1)[0].strip()
        if clave in meta and ":" in line:
            meta[clave] = line.split(":", 1)[1].strip()
    return meta, text
