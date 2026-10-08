"""Diccionario de datos de las tablas de seguros, generado desde la ficha técnica.

Toma el inventario de campos (``seguros/fuentes/inventario_1835.json``, que se arma con
``inventario_1835.py`` desde los anexos técnicos de la Circular 1835) y publica, para cada
tabla, una fila por columna con el nombre original de la CMF, su tipo, la unidad en que
viene y la descripción literal de la ficha.

Salidas:

  * ``docs/js/diccionario_seguros.js`` — ``window.DICCIONARIO_SEGUROS``; lo usa la descarga
    de Excel para agregar la hoja "Diccionario" al lado de los datos.
  * ``docs/js/data_dictionary.js`` — con ``--web``, reemplaza la lista de columnas de las
    tablas de seguros (el resto de la ficha de cada tabla queda como está).

Uso::

    python -m seguros.scripts.diccionario_1835            # escribe ambos
    python -m seguros.scripts.diccionario_1835 --check    # falla si están desactualizados
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from seguros.scripts import formato_1835  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
SALIDA_JS = RAIZ / "docs" / "js" / "diccionario_seguros.js"
DIC_WEB = RAIZ / "docs" / "js" / "data_dictionary.js"

# Columnas que agrega el pipeline (no vienen en la ficha) y que van al principio de la tabla.
CONTROL = [
    {"columna": "periodo", "tipo": "t", "decimales": 0, "unidad": None, "nombre_ficha": "",
     "descripcion": "Mes de la cartera informada (AAAA-MM)."},
    {"columna": "sector", "tipo": "t", "decimales": 0, "unidad": None, "nombre_ficha": "",
     "descripcion": "vida (archivos CSVID) o generales (CSGEN)."},
    {"columna": "rut_aseguradora", "tipo": "r", "decimales": 0, "unidad": None, "nombre_ficha": "",
     "descripcion": "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades)."},
    {"columna": "nombre_aseguradora", "tipo": "t", "decimales": 0, "unidad": None, "nombre_ficha": "",
     "descripcion": "Nombre de la compañía tal como aparece en el encabezado del archivo del mes."},
    {"columna": "tipo_registro", "tipo": "t", "decimales": 0, "unidad": None, "nombre_ficha": "",
     "descripcion": "Subtipo de registro dentro del archivo (por ejemplo forward, swap o deuda)."},
]

UNIDAD_TEXTO = {"(M$)": "miles de pesos", "($)": "pesos", "(UF)": "UF", "(UM)": "unidad monetaria del instrumento",
                "(%)": "porcentaje", "(US$)": "dólares"}

TIPO_JS = {"t": "VARCHAR", "r": "VARCHAR", "f": "VARCHAR", "n": "BIGINT", "s": "BIGINT"}

# Criterio contable, por fragmento del nombre (el primero que calza).
CONTABLE = [("valor_razonable", "Valor razonable"), ("deterioro", "Deterioro"),
            ("costo_amortizado", "Costo amortizado"), ("valor_final", "Valor contable informado"),
            ("valor_bolsa", "Valor de mercado bruto"), ("valor_mercado", "Valor de mercado bruto"),
            ("valor_compra", "Costo"), ("valor_costo", "Costo"), ("costo", "Costo"),
            ("interes", "Devengado"), ("mayor_o_menor_valor", "Valor razonable")]


def _limpiar(texto: str) -> str:
    return re.sub(r"\s+", " ", (texto or "").replace("–", "-")).strip()


def _resumen(texto: str, tope: int = 300) -> str:
    t = _limpiar(texto)
    if not t:
        return ""
    if t[-1] not in ".!?":
        t = t.rstrip(",;:") + "."
    if len(t) <= tope:
        return t
    corte = t[:tope]
    punto = max(corte.rfind(". "), corte.rfind("; "))
    return (corte[:punto + 1] if punto > 80 else corte.rsplit(" ", 1)[0] + ".")


def _tipo_js(campo: dict) -> str:
    if campo["tipo"] in "ns" and campo["decimales"]:
        return "DOUBLE"
    return TIPO_JS[campo["tipo"]]


def _rol(campo: dict) -> str:
    c = campo["columna"]
    if c == "periodo":
        return "Fecha"
    if c == "rut_aseguradora":
        return "FK"
    if campo["tipo"] == "f":
        return "Fecha"
    if c.startswith(("rut_", "run_", "rol", "lei_")) or c in ("run", "rut"):
        return "Identificador"
    if campo["tipo"] in "tr":
        return "Atributo"
    return "Métrica"


def _contable(campo: dict) -> str:
    c = campo["columna"]
    for fragmento, criterio in CONTABLE:
        if fragmento in c:
            return criterio
    return "No aplica"


def _unidad(campo: dict) -> str | None:
    return UNIDAD_TEXTO.get(campo["unidad"] or "")


def filas(tabla: str) -> list[dict]:
    """Una fila por columna publicada de la tabla, en orden (control, luego la ficha)."""
    orden: list[dict] = []
    visto: dict[str, dict] = {}
    for formato in ("v2016", "v2024"):
        for (letra, tipo), reg in formato_1835.diccionario(formato).items():
            for campo in reg:
                if campo["tabla"] != tabla:
                    continue
                clave = campo["columna"]
                etiqueta = f"{letra}{tipo}" + (f" ({campo['subtipo']})" if campo["subtipo"] else "")
                if clave in visto:
                    visto[clave]["formatos"].add(formato)
                    visto[clave]["registros"].add(etiqueta)
                    continue
                fila = {"columna": clave, "nombre_ficha": campo["nombre_ficha"],
                        "picture": campo["picture"], "tipo": campo["tipo"],
                        "decimales": campo["decimales"], "unidad": campo["unidad"],
                        "descripcion": _limpiar(campo["descripcion"]),
                        "formato": formato, "formatos": {formato},
                        "registros": {etiqueta}}
                visto[clave] = fila
                orden.append(fila)
    con_subtipo = any(r["subtipo"] for r in _registros_de(tabla))
    base = [c for c in CONTROL if c["columna"] != "tipo_registro" or con_subtipo]
    return base + orden


def _registros_de(tabla: str) -> list[dict]:
    salida = []
    for formato in ("v2016", "v2024"):
        for clave, reg in formato_1835.registros_inventario(formato).items():
            if reg["tabla"] == tabla:
                salida.append({"clave": clave, "subtipo": reg["subtipo"], "formato": formato})
    return salida


def genera() -> dict:
    """{tabla: [filas]} con todas las tablas de cartera (sin el maestro de compañías)."""
    tablas = []
    for formato in ("v2016", "v2024"):
        for reg in formato_1835.registros_inventario(formato).values():
            if reg["tabla"] not in tablas:
                tablas.append(reg["tabla"])
    return {t: filas(t) for t in tablas}


# ── Salidas ──────────────────────────────────────────────────────────────────────────

def _json_js(objeto) -> str:
    return json.dumps(objeto, ensure_ascii=False, separators=(",", ":"))


CABECERA = ["columna", "tipo", "unidad", "nombre en la ficha CMF", "registro", "vigencia", "descripción"]

VIGENCIA = {"v2016": "hasta 2024-11", "v2024": "desde 2024-12"}


def _fila_js(fila: dict) -> list:
    formatos = sorted(fila.get("formatos") or ("v2016", "v2024"))
    # p. ej. "p2 (opción), p5 (swap)"; vacío en las columnas que agrega el pipeline.
    registros = ", ".join(sorted(fila.get("registros") or []))
    return [fila["columna"], _tipo_js(fila), _unidad(fila) or "", fila["nombre_ficha"] or "",
            registros, VIGENCIA[formatos[0]] if len(formatos) == 1 else "ambos",
            fila["descripcion"]]


def texto_diccionario_js(datos: dict) -> str:
    total = sum(len(v) for v in datos.values())
    cuerpo = _json_js({t: {"cabecera": CABECERA, "filas": [_fila_js(f) for f in filas_]}
                       for t, filas_ in datos.items()})
    return ("/**\n"
            " * Diccionario de datos de las tablas de seguros (Circular CMF 1835).\n"
            " * Archivo GENERADO por seguros/scripts/diccionario_1835.py — no editar a mano.\n"
            " * Cada columna sale de los anexos técnicos de la Circular 1835, con el nombre\n"
            " * original de la CMF, su tipo, la unidad y la descripción literal de la ficha.\n"
            " * Lo usa la descarga de Excel para agregar la hoja \"Diccionario\" a los datos.\n"
            " */\n"
            f"window.DICCIONARIO_SEGUROS = {cuerpo};\n"
            f"window.DICCIONARIO_SEGUROS_TOTAL = {total};\n")


def _columna_js(fila: dict) -> str:
    significado = _resumen(fila["descripcion"])
    unidad = _unidad(fila)
    if unidad:
        significado = f"{significado} Expresado en {unidad}." if significado else f"Expresado en {unidad}."
    return ('      { name: "%s", type: "%s", role: "%s", significado: "%s", contable: "%s" }'
            % (fila["columna"], _tipo_js(fila), _rol(fila),
               significado.replace('"', '\\"'), _contable(fila)))


def _actualiza_diccionario_web(texto: str, datos: dict) -> str:
    """Reemplaza el bloque de columnas de cada tabla de seguros en data_dictionary.js."""
    for tabla, filas_ in datos.items():
        vista = f"seguros_{tabla}"
        patron = re.compile(
            r'(id: "%s",(?:.|\n)*?\n)    columnas: \[\n.*?\n    \]\n' % re.escape(vista), re.S)
        nuevo = "    columnas: [\n" + ",\n".join(_columna_js(f) for f in filas_) + "\n    ]\n"
        texto, n = patron.subn(lambda m: m.group(1) + nuevo, texto, count=1)
        if not n:
            raise SystemExit(f"No se encontró la entrada {vista} en {DIC_WEB.name}")
    return texto


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="falla si los archivos generados están desactualizados")
    ap.add_argument("--solo", choices=("js", "web"), default=None, help="escribir solo uno de los dos archivos")
    args = ap.parse_args()

    datos = genera()
    js = texto_diccionario_js(datos)
    web = DIC_WEB.read_text(encoding="utf-8") if DIC_WEB.exists() else ""
    web_nuevo = _actualiza_diccionario_web(web, datos) if web else ""

    if args.check:
        malo = False
        if args.solo != "web" and (not SALIDA_JS.exists() or SALIDA_JS.read_text(encoding="utf-8") != js):
            print(f"DESACTUALIZADO: {SALIDA_JS.relative_to(RAIZ)}")
            malo = True
        if args.solo != "js" and web_nuevo and web_nuevo != web:
            print(f"DESACTUALIZADO: {DIC_WEB.relative_to(RAIZ)}")
            malo = True
        if malo:
            print("Ejecuta python -m seguros.scripts.diccionario_1835")
            return 1
        print("Diccionarios al día:", ", ".join(f"{t}: {len(f)} columnas" for t, f in datos.items()))
        return 0

    if args.solo != "web":
        SALIDA_JS.write_text(js, encoding="utf-8")
        print(f"{SALIDA_JS.relative_to(RAIZ)}: {len(js):,} bytes, "
              f"{sum(len(v) for v in datos.values())} columnas en {len(datos)} tablas")
    if args.solo != "js" and web_nuevo and web_nuevo != web:
        DIC_WEB.write_text(web_nuevo, encoding="utf-8")
        print(f"{DIC_WEB.relative_to(RAIZ)}: columnas de {len(datos)} tablas de seguros actualizadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
