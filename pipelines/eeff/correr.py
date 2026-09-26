"""Corrida incremental de los EEFF de factoring y leasing.

No parte de cero. Un documento ok, con el mismo hash y la misma versión del
parser, se salta. Si uno falla, se anota y se sigue con el siguiente. El
checkpoint se escribe después de cada documento, no al final.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipelines.eeff import parse_md
from pipelines.eeff.alias import ESQUEMAS_CERRADOS, PARSER_VERSION, TABLAS_COMUNES
from pipelines.eeff.estado import Store, ahora, id_documento
from pipelines.eeff.validate_api import (
    cuadratura_balance,
    cuadratura_detalle,
    cuadratura_resultados,
    validar_documento,
)

TOLERANCIA_MILES = 1.0


def listar_fuentes(fuentes: Path, periodo: str = "", rut: str = "") -> list[Path]:
    salida = []
    for path in sorted(Path(fuentes).glob("*.md")):
        meta, _ = parse_md.cargar_md(path)
        got_periodo = meta.get("periodo") or ""
        got_rut = meta.get("rut") or ""
        if periodo:
            if got_periodo and got_periodo != periodo:
                continue
            if not got_periodo and f"_{periodo}" not in path.name:
                continue
        if rut:
            if got_rut and got_rut != rut:
                continue
            if not got_rut and rut not in path.name:
                continue
        salida.append(path)
    return salida


def indice_completo(indice: list[dict]) -> bool:
    """Un índice cortado no niega una nota. Solo un índice que parte en 1 y cubre el cierre."""
    numeros = []
    for row in indice:
        try:
            numeros.append(int(row["numero_nota"]))
        except (TypeError, ValueError, KeyError):
            continue
    if not numeros or min(numeros) > 1 or len(numeros) < 15:
        return False
    return True


def cargar_api(path: Path | None) -> dict:
    """rut por periodo. Si hay dos filas, no se elige una: la validación queda sin API."""
    if path is None or not Path(path).exists():
        return {}
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    por = {}
    for row in rows:
        slot = por.setdefault(row.get("periodo") or "", {})
        clave = row.get("rut") or ""
        if clave in slot:
            slot[clave] = None
        else:
            slot[clave] = row
    return por


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _num(value):
    if value is None:
        return None
    number = float(value)
    if number.is_integer():
        return int(number)
    return round(number, 2)


def _paginas(indice: list[dict]) -> dict[int, str]:
    return {int(row["numero_nota"]): str(row.get("pagina") or "") for row in indice}


def _cara_de_nota(balance: list[dict], numero: int, cuenta: str):
    citados = [
        row for row in balance
        if str(row.get("nota_ref") or "") == str(numero) and row.get("monto_miles_clp") is not None
    ]
    if citados:
        return _num(sum(float(row["monto_miles_clp"]) for row in citados))
    alt = [
        row for row in balance
        if row.get("cuenta_canonica") == cuenta
        and row.get("clase") != "Total"
        and row.get("monto_miles_clp") is not None
        and "no_corriente" not in str(row.get("cuenta_canonica") or "")
    ]
    if len(alt) == 1:
        return _num(alt[0]["monto_miles_clp"])
    return None


def _ref_nota(filas: list[dict], campo: str):
    detalles = [row for row in filas if not row.get("es_total") and row.get(campo) is not None]
    totales = [row for row in filas if row.get("es_total") and row.get(campo) is not None]
    suma = _num(sum(float(row[campo]) for row in detalles)) if detalles else None
    total = _num(totales[-1][campo]) if totales else None
    interno = True
    if suma is not None and total is not None and abs(suma - total) > TOLERANCIA_MILES:
        interno = False
    return (total if total is not None else suma), interno


def _cuadre_tabla(filas: list[dict], campo: str, balance: list[dict], cuenta: str) -> tuple[str, float | None]:
    if not filas:
        return "SIN_NOTA", None
    estados = []
    diffs = []
    for numero in sorted({int(row["numero_nota"]) for row in filas}):
        grupo = [row for row in filas if int(row["numero_nota"]) == numero]
        cara = _cara_de_nota(balance, numero, cuenta)
        estado, diff = _cuadre_nota(grupo, campo, cara)
        estados.append(estado)
        if diff is not None:
            diffs.append(float(diff))
    if any(estado == "DIFIERE" for estado in estados):
        final = "DIFIERE"
    elif any(estado == "SIN_CARA" for estado in estados):
        final = "SIN_CARA"
    elif estados and all(estado == "OK" for estado in estados):
        final = "OK"
    else:
        final = estados[0] if estados else "SIN_NOTA"
    return final, _num(sum(diffs)) if diffs else None


def _cuadre_nota(filas: list[dict], campo: str, cara) -> tuple[str, float | None]:
    if not filas:
        return "SIN_NOTA", None
    ref, interno = _ref_nota(filas, campo)
    if ref is None:
        return "SIN_NOTA", None
    if cara is None:
        return "SIN_CARA", None
    diff = round(float(ref) - float(cara), 2)
    if abs(diff) <= TOLERANCIA_MILES and interno:
        return "OK", _num(diff)
    return "DIFIERE", _num(diff)


def _estado_api(vals: list[dict]) -> str:
    estados = {v["estado"] for v in vals}
    if "DIFIERE" in estados or "DIFIERE_SIN_TIPO" in estados:
        return "DIFIERE"
    if "SIN_TIPO" in estados:
        return "SIN_TIPO"
    if estados and estados <= {"OK"}:
        return "OK"
    if "SIN_API" in estados and "OK" not in estados and "SIN_TIPO" not in estados:
        return "SIN_API"
    return "PARCIAL"


def _estado_extraccion(balance, tablas, cuadre_balance, cuadres_nota, faltan_lineas: bool) -> str:
    if not balance:
        return "PDF_VACIO"
    if any(estado == "DIFIERE" for estado in cuadres_nota.values()):
        return "PDF_NOTA_DIFIERE"
    if any(tablas.values()):
        if cuadre_balance.get("estado") == "OK" and not faltan_lineas:
            return "PDF_CON_NOTAS"
        return "PDF_PARCIAL_CON_NOTAS"
    if cuadre_balance.get("estado") == "OK" and not faltan_lineas:
        return "PDF_CARATULA"
    if cuadre_balance.get("estado") == "DIFIERE":
        return "PDF_DESCUADRADO"
    return "PDF_PARCIAL"


def _armar(meta: dict, parsed: dict, archivo: str, sha256: str, fila_api: dict | None) -> dict[str, list[dict]]:
    clave = id_documento(meta["rut"], meta["periodo"], meta.get("tipo_eeff", ""))
    paginas = _paginas(parsed["indice"])
    completo = indice_completo(parsed["indice"])
    balance = []
    for i, row in enumerate(parsed["balance"], 1):
        row = dict(row)
        row["id_documento"] = clave
        row["id_linea"] = f"{clave}|B|{i:04d}"
        row["monto_miles_clp"] = _num(row.get("monto_miles_clp"))
        row["monto_m_clp"] = _num(row.get("monto_m_clp"))
        row["monto_comparativo_miles_clp"] = _num(row.get("monto_comparativo_miles_clp"))
        balance.append(row)
    resultados = []
    for i, row in enumerate(parsed["resultados"], 1):
        row = dict(row)
        row["id_documento"] = clave
        row["id_linea"] = f"{clave}|R|{i:04d}"
        row["monto_miles_clp"] = _num(row.get("monto_miles_clp"))
        row["monto_m_clp"] = _num(row.get("monto_m_clp"))
        row["monto_comparativo_miles_clp"] = _num(row.get("monto_comparativo_miles_clp"))
        resultados.append(row)

    tablas = {nombre: [] for nombre in ESQUEMAS_CERRADOS}
    for nombre, filas in (parsed.get("tablas") or {}).items():
        if nombre not in ESQUEMAS_CERRADOS:
            continue
        for i, row in enumerate(filas, 1):
            item = dict(row)
            item["id_documento"] = clave
            item["id_linea"] = f"{clave}|{nombre}|{i:04d}"
            item["pagina"] = paginas.get(int(item["numero_nota"]), "")
            item["moneda"] = "CLP"
            item["calidad"] = "extraida_documento"
            item["es_total"] = 1 if item.get("es_total") else 0
            for col in (
                "saldo_miles", "saldo_comparativo_miles", "colocacion_miles", "provision_miles",
                "neto_miles", "colocacion_comparativo_miles", "provision_comparativo_miles",
                "neto_comparativo_miles",
            ):
                if col in item:
                    item[col] = _num(item.get(col))
            tablas[nombre].append(item)

    extraidas_por_nota = {}
    for nombre, filas in tablas.items():
        for row in filas:
            extraidas_por_nota.setdefault(int(row["numero_nota"]), set()).add(nombre)

    indice = []
    for row in parsed["indice"]:
        item = dict(row)
        numero = int(item["numero_nota"])
        item["id_documento"] = clave
        item["id_nota"] = f"{clave}|N|{numero}"
        item["tipo_eeff"] = meta.get("tipo_eeff", "")
        item["extraida"] = 1 if numero in extraidas_por_nota else 0
        if item["extraida"]:
            item["estado_tabla"] = "leida"
        elif item.get("tabla"):
            item["estado_tabla"] = "en_indice_sin_tabla"
        else:
            item["estado_tabla"] = "no_es_comun"
        indice.append(item)

    pendientes = []
    for i, row in enumerate(parsed.get("pendientes") or [], 1):
        item = dict(row)
        item["id_documento"] = clave
        item["id_pendiente"] = f"{clave}|P|{item.get('tabla')}|{item.get('numero_nota')}|{i}"
        item["razon_social"] = meta.get("razon_social", "")
        item["periodo"] = meta["periodo"]
        item["tipo_eeff"] = meta.get("tipo_eeff", "")
        item["rut"] = meta["rut"]
        pendientes.append(item)
    pendientes_notas = {int(row["numero_nota"]) for row in pendientes}
    for item in indice:
        if int(item["numero_nota"]) in pendientes_notas and not item["extraida"]:
            item["estado_tabla"] = "esquema_pendiente"

    cuadre_balance = cuadratura_balance(balance)
    cara = cuadratura_detalle(balance)
    if cara["estado"] == "OK" and cuadre_balance.get("estado") == "INCOMPLETO":
        cara = {
            "estado": "INCOMPLETO",
            "hueco": "la carátula no trae los totales para cerrar activos = pasivos + patrimonio",
        }
    resultado = cuadratura_resultados(resultados)
    faltan_lineas = cara["estado"] == "FALTAN_LINEAS" or resultado["estado"] == "FALTAN_LINEAS"
    hueco = " | ".join(texto for texto in (cara.get("hueco"), resultado.get("hueco")) if texto)
    campos = {"efectivo": "saldo_miles", "deudores": "neto_miles"}
    cuentas = {"efectivo": "efectivo", "deudores": "deudores"}
    cuadres_nota = {}
    diffs_nota = {}
    for nombre, filas in tablas.items():
        estado, diff = _cuadre_tabla(filas, campos[nombre], balance, cuentas[nombre])
        if filas:
            cuadres_nota[nombre] = estado
            diffs_nota[nombre] = diff

    cobertura = []
    for tabla in TABLAS_COMUNES:
        notas = [row for row in indice if row.get("tabla") == tabla]
        numeros = [str(row["numero_nota"]) for row in notas]
        titulos = [row["titulo_nota"] for row in notas]
        filas = tablas.get(tabla) or []
        extraida = 1 if filas else 0
        extraidos = {int(row["numero_nota"]) for row in filas}
        en_indice = {int(n) for n in numeros}
        if extraida and en_indice and en_indice <= extraidos:
            estado = "leida"
        elif extraida and en_indice:
            estado = "parcial"
        elif extraida:
            estado = "leida"
        elif any(int(row["numero_nota"]) in pendientes_notas for row in notas):
            estado = "esquema_pendiente"
        elif notas:
            estado = "en_indice_sin_tabla"
        elif completo:
            estado = "ausente"
        else:
            estado = "indice_incompleto"
        cobertura.append({
            "id_cobertura": f"{clave}|{tabla}",
            "id_documento": clave,
            "rut": meta["rut"],
            "razon_social": meta.get("razon_social", ""),
            "periodo": meta["periodo"],
            "tipo_eeff": meta.get("tipo_eeff", ""),
            "tabla": tabla,
            "numeros_nota": ",".join(numeros),
            "titulo_nota": " | ".join(titulos),
            "extraida": extraida,
            "lineas": len(filas),
            "estado": estado,
            "cuadre": cuadres_nota.get(tabla, "SIN_NOTA"),
            "diff_miles": diffs_nota.get(tabla),
            "indice_completo": 1 if completo else 0,
        })

    vals = validar_documento(balance, fila_api if fila_api else None)
    tipo_api = ""
    if fila_api and fila_api.get("tipo_eeff"):
        tipo_api = str(fila_api.get("tipo_eeff"))
    tipo_doc = (meta.get("tipo_eeff") or "").strip().lower()
    chequeado = 1 if tipo_api and tipo_api.strip().lower()[:1] == tipo_doc[:1] and tipo_doc else 0
    validacion = []
    for row in vals:
        item = dict(row)
        item["id_documento"] = clave
        item["id_validacion"] = f"{clave}|V|{item['concepto']}"
        item["tipo_eeff"] = meta.get("tipo_eeff", "")
        item["tipo_api"] = tipo_api
        item["tipo_chequeado"] = chequeado
        item["numeros"] = ""
        if item["estado"] == "OK":
            item["numeros"] = "cuadra"
            if not chequeado:
                item["estado"] = "SIN_TIPO"
        elif item["estado"] == "DIFIERE":
            item["numeros"] = "difiere"
            if not chequeado:
                item["estado"] = "DIFIERE_SIN_TIPO"
        elif item["estado"] == "SOLO_API":
            item["numeros"] = "solo_api"
        elif item["estado"] == "SIN_API":
            item["numeros"] = "sin_api"
        validacion.append(item)

    leidas = sorted(nombre for nombre, filas in tablas.items() if filas)
    documento = {
        "id_documento": clave,
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta["periodo"],
        "fecha_corte": meta.get("fecha_corte", ""),
        "tipo_eeff": meta.get("tipo_eeff", ""),
        "unidad": "M$ miles CLP",
        "fuente": meta.get("fuente", "EEFF PDF/MD"),
        "archivo": archivo,
        "sha256": sha256,
        "url_pdf": meta.get("url_pdf", ""),
        "url_visualizacion": meta.get("url_visualizacion", ""),
        "notas_en_indice": len(indice),
        "lineas_balance": len(balance),
        "lineas_resultados": len(resultados),
        "tablas_leidas": ",".join(leidas),
        "estado_extraccion": _estado_extraccion(
            balance, tablas, cuadre_balance, cuadres_nota, faltan_lineas
        ),
        "cuadre_balance": cuadre_balance.get("estado", ""),
        "diff_balance_m_clp": _num(cuadre_balance.get("diff_m_clp")),
        "cuadre_caratula": cara["estado"],
        "cuadre_resultados": resultado["estado"],
        "hueco": hueco,
        "cuadre_efectivo": cuadres_nota.get("efectivo", "SIN_NOTA"),
        "diff_efectivo_miles": diffs_nota.get("efectivo"),
        "cuadre_deudores": cuadres_nota.get("deudores", "SIN_NOTA"),
        "diff_deudores_miles": diffs_nota.get("deudores"),
        "estado_api": _estado_api(validacion),
        "indice_completo": 1 if completo else 0,
        "parser_version": PARSER_VERSION,
        "actualizado": ahora(),
    }
    return {
        "documentos": [documento],
        "balance": balance,
        "resultados": resultados,
        "indice": indice,
        "nota_efectivo": tablas["efectivo"],
        "nota_deudores": tablas["deudores"],
        "cobertura": cobertura,
        "validacion": validacion,
        "esquema_pendiente": pendientes,
    }


def procesar_uno(path: Path, store: Store, checkpoint: dict, forzar: bool, fila_api: dict | None) -> str:
    path = Path(path)
    try:
        sha = _sha256(path)
        meta, text = parse_md.cargar_md(path)
    except Exception as exc:
        print(f"[error] {path.name} no se pudo leer: {exc}")
        return "error"
    if not meta.get("rut") or not meta.get("periodo"):
        print(f"[error] {path.name} sin rut o periodo en el encabezado")
        return "error"
    clave = id_documento(meta["rut"], meta["periodo"], meta.get("tipo_eeff", ""))
    if not forzar and store.debe_saltar(checkpoint, clave, sha):
        print(f"[skip] {clave} hash igual, no se relee")
        return "skip"
    try:
        parsed = parse_md.parse_documento(text, meta)
        por_tabla = _armar(meta, parsed, path.name, sha, fila_api)
        store.reemplazar_documento(meta["periodo"], clave, por_tabla)
    except Exception as exc:
        prev = checkpoint.setdefault("documentos", {}).get(clave, {})
        checkpoint.setdefault("documentos", {})[clave] = {
            "sha256": sha,
            "archivo": path.name,
            "estado": "error",
            "parser_version": PARSER_VERSION,
            "actualizado": ahora(),
            "error": str(exc),
            "filas_previas": prev.get("estado") == "ok",
        }
        store.guardar_checkpoint(checkpoint)
        print(f"[error] {clave} {exc}. Se sigue con el siguiente. Las filas buenas anteriores no se borran.")
        return "error"
    doc = por_tabla["documentos"][0]
    checkpoint.setdefault("documentos", {})[clave] = {
        "sha256": sha,
        "archivo": path.name,
        "estado": "ok",
        "parser_version": PARSER_VERSION,
        "actualizado": doc["actualizado"],
        "error": "",
        "tablas_leidas": doc["tablas_leidas"],
        "estado_extraccion": doc["estado_extraccion"],
    }
    store.guardar_checkpoint(checkpoint)
    print(
        f"[ok] {clave} {doc['estado_extraccion']} "
        f"balance={doc['lineas_balance']} notas={doc['tablas_leidas'] or '-'} "
        f"caratula={doc['cuadre_caratula']} resultados={doc['cuadre_resultados']} "
        f"efectivo={doc['cuadre_efectivo']} deudores={doc['cuadre_deudores']} api={doc['estado_api']}"
    )
    return "ok"


def correr(
    fuentes: Path,
    store: Store,
    out_dir: Path,
    periodo: str = "",
    rut: str = "",
    forzar: bool = False,
    api_json: Path | None = None,
    olvidar_ausentes: bool = False,
    publicar: bool = True,
) -> dict:
    fuentes = Path(fuentes)
    with store.lock():
        if publicar and store.tiene_filas():
            store.publicar(out_dir)
        checkpoint = store.cargar_checkpoint()
        if olvidar_ausentes:
            presentes = {path.name for path in fuentes.glob("*.md")}
            ausentes = {
                clave for clave, prev in checkpoint.get("documentos", {}).items()
                if prev.get("archivo") and prev["archivo"] not in presentes
            }
            borradas = store.olvidar(ausentes)
            if borradas:
                print(f"[olvidar] {len(borradas)} documentos cuya fuente ya no está")
                checkpoint = store.cargar_checkpoint()
        api = cargar_api(api_json)
        archivos = listar_fuentes(fuentes, periodo, rut)
        conteo = {"ok": 0, "skip": 0, "error": 0}
        errores = []
        for path in archivos:
            meta, _ = parse_md.cargar_md(path)
            fila_api = None
            if meta.get("periodo") in api and meta.get("rut"):
                fila_api = api[meta["periodo"]].get(meta["rut"])
            resultado = procesar_uno(path, store, checkpoint, forzar, fila_api)
            conteo[resultado] = conteo.get(resultado, 0) + 1
            if resultado == "error":
                errores.append(path.name)
            if publicar and resultado == "ok":
                store.publicar(out_dir)
        if publicar:
            escritos = store.publicar(out_dir)
        else:
            escritos = {}
        resumen = {
            "actualizado": ahora(),
            "parser_version": PARSER_VERSION,
            "periodo": periodo or "todos",
            "rut": rut or "todos",
            "archivos": len(archivos),
            "ok": conteo.get("ok", 0),
            "skip": conteo.get("skip", 0),
            "error": conteo.get("error", 0),
            "errores": errores,
            "publicadas": escritos,
        }
        store.registrar_corrida(resumen)
        _resumen_validacion(store, out_dir, periodo)
        print(
            f"[fin] ok={resumen['ok']} skip={resumen['skip']} error={resumen['error']} "
            f"de {resumen['archivos']} archivos"
        )
        return resumen


def _resumen_validacion(store: Store, out_dir: Path, periodo: str) -> None:
    todo = store.leer_todo()
    vals = todo["validacion"]
    if periodo:
        vals = [row for row in vals if row.get("periodo") == periodo]
    resumen = {
        "periodo": periodo or "todos",
        "documentos": len({row["id_documento"] for row in todo["documentos"]}),
        "validacion": {},
        "cobertura": {},
    }
    for row in vals:
        resumen["validacion"][row["estado"]] = resumen["validacion"].get(row["estado"], 0) + 1
    for row in todo["cobertura"]:
        if periodo and row.get("periodo") != periodo:
            continue
        clave = f"{row['tabla']}:{row['estado']}"
        resumen["cobertura"][clave] = resumen["cobertura"].get(clave, 0) + 1
    path = Path(out_dir) / "factoring_leasing_eeff_resumen_validacion.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
