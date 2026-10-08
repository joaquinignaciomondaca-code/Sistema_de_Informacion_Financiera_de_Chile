"""Inventario de campos de la Circular 1835 (seguros) derivado de las fichas técnicas.

La CMF publica las fichas (``seguros/fuentes/fichas_tecnicas_1835/``) con el nombre,
la descripción y el PICTURE de cada campo.  ``ficha_1835.py`` las convierte en
posiciones; este módulo decide qué se publica y con qué nombre:

  - el nombre publicado es el de la ficha, en minúsculas y sin acentos;
  - se repara el nombre cuando la ficha lo partió a media palabra
    (``PARTICIPACION_PORC`` + ``ENTUAL`` -> ``PARTICIPACION_PORCENTUAL``);
  - se agrega el sufijo de la unidad declarada (``_m_clp``, ``_clp``, ``_uf``, ``_um``);
  - los nombres que la ficha repite dentro de un mismo registro se distinguen con un
    alias curado (dos RUT de deudor, activo objeto en unidades, etc.).

Uso::

    python -m seguros.scripts.inventario_1835 --escribir   # fuentes/inventario_1835.json
    python -m seguros.scripts.inventario_1835 --reporte    # resumen por tabla
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .ficha_1835 import FUENTES, FICHA, registros, unidad_del_texto

RUTA_JSON = Path(__file__).resolve().parent.parent / "fuentes" / "inventario_1835.json"

FORMATOS = ("v2016", "v2024")

# (letra, tipo de registro) -> (tabla publicada, subtipo)
DESTINO = {
    ("i", "2"): ("renta_fija", None),
    ("a", "2"): ("acciones", None),
    ("f", "2"): ("fondos_mutuos", None),
    ("b", "2"): ("bienes_raices", None),
    ("x", "2"): ("extranjeros", "deuda"),
    ("x", "3"): ("extranjeros", "acciones_y_fondos"),
    ("x", "4"): ("extranjeros", "bienes_raices"),
    ("x", "5"): ("extranjeros", "filiales"),
    ("c", "2"): ("control_inversiones", None),
    ("p", "2"): ("derivados", "opcion"),
    ("p", "3"): ("derivados", "forward"),
    ("p", "4"): ("derivados", "futuro"),
    ("p", "5"): ("derivados", "swap"),
    ("p", "6"): ("pactos", None),
}

# Unidad declarada en la ficha -> sufijo del nombre publicado.
SUFIJO_UNIDAD = {"(M$)": "M_CLP", "($)": "CLP", "(UM)": "UM", "(US$)": "USD", "(UF)": "UF"}

# La ficha imprime el nombre en una columna angosta y a veces lo corta a media palabra;
# el trozo suelto queda en el renglón siguiente y el parser lo une con "_".
REPARAR = (
    (r"^PARTICIPACION_PORC_ENTUAL$", "PARTICIPACION_PORCENTUAL"),
    (r"^PORCENTAJE_PARTICI_PACION$", "PORCENTAJE_PARTICIPACION"),
    (r"^RESULTADO_DE_LA_S_OCIEDAD_FILIAL$", "RESULTADO_DE_LA_SOCIEDAD_FILIAL"),
    (r"^MODELO_PROPIO_DE_TERIORO$", "MODELO_PROPIO_DETERIORO"),
    (r"^MODELO_PROPIO_DET_ERIORO$", "MODELO_PROPIO_DETERIORO"),
    (r"^TOTAL_COSTO_AMOR_TIZADO$", "TOTAL_COSTO_AMORTIZADO"),
    (r"^TOTAL_VALOR_RAZON_ABLE$", "TOTAL_VALOR_RAZONABLE"),
    (r"^TOTAL_EFECTIVO_EQ_UIVALENTE$", "TOTAL_EFECTIVO_EQUIVALENTE"),
    (r"^TOTAL_INST_OTRAS_C_LASIF$", "TOTAL_INST_OTRAS_CLASIF"),
    (r"^CODIGO_ACTIVIDAD_E(?:_CONOMICA)?$", "CODIGO_ACTIVIDAD_ECONOMICA"),
    (r"^CLASIFICACION_DE_RI_ESGO_PAIS$", "CLASIFICACION_DE_RIESGO_PAIS"),
    (r"^COSTO_HISTORICO_C_ORREGIDO$", "COSTO_HISTORICO_CORREGIDO"),
    (r"^TOTAL_M2_CONSTRU_CCION$", "TOTAL_M2_CONSTRUCCION"),
    (r"^VALOR_TASACION_TE_RRENO_M2$", "VALOR_TASACION_TERRENO_M2"),
    (r"^VALOR_TASACION_CO_NSTRUCCION_M2$", "VALOR_TASACION_CONSTRUCCION_M2"),
    (r"^DIG_RUT_ACTIVO_OBJ_ETO$", "DIG_RUT_ACTIVO_OBJETO"),
    (r"^VALORIZACION_DE_PACTO_A_LA_FEC_HA_DE_CIERRE$", "VALORIZACION_DE_PACTO_A_LA_FECHA_DE_CIERRE"),
    (r"^TIPO_DOCUMENTACIO$", "TIPO_DOCUMENTACION"),
    (r"^DESARROLLO_AVANC$", "DESARROLLO_AVANCE"),
    (r"^TIR_SIN_COSTO_NCG$", "TIR_SIN_COSTO"),
    (r"^FECHA_INSCRIPCION_AAAAMMDD$", "FECHA_INSCRIPCION"),
    (r"^VERIFICADOR_DEUDO$", "VERIFICADOR_DEUDOR"),
    (r"^VALOR_RAZONABLE_D_EL_", "VALOR_RAZONABLE_DEL_"),
    # Los dos campos de relación deuda-garantía se cortaron en "OT"/"OR" y "PE"/"R";
    # la descripción distingue la fecha de otorgamiento de la de información.
    (r"^DEUDA_GARANTIA_OT(?:_.*)?$", "DEUDA_GARANTIA_OTORGAMIENTO"),
    (r"^DEUDA_GARANTIA_PE(?:_.*)?$", "DEUDA_GARANTIA_INFORMACION"),
    # "INVERSIONES_REPRESENTATIVAS_D_E_(RT_+_PR)" = de reservas técnicas + patrimonio de riesgo.
    (r"^INVERSIONES_(NO_)?REPRESENTATIVAS_D_E_RT_PR$", r"INVERSIONES_\1REPRESENTATIVAS_DE_RT_PR"),
)
_REPARAR = tuple((re.compile(p), r) for p, r in REPARAR)

# Un mismo campo, dos nombres: la ficha de 2024 renombra o trunca distinto que la de 2016.
# Sin esto la tabla publicada tendría dos columnas para lo mismo (una nula en cada época).
PARES = {
    ("a", "TIPO_FONDO_ACC"): "TIPO_FONDO",
    ("x", "CODIGO_INDIVIDUALIZACION_O"): "CODIGO_INDIVIDUALIZACION_O_NEMOTECNICO",
    ("x", "ACTIVO_EN_MARGEN_O_SUJETO_A"): "ACTIVO_EN_MARGEN_O_SUJETO_A_PACTO",
    ("x", "CRITERIO_VALORIZ"): "CRITERIO_VALORIZACION",
    ("x", "CRITERIO_VALORIZACI"): "CRITERIO_VALORIZACION",
    ("x", "NOMBRE_CUSTODI"): "NOMBRE_CUSTODIO",
    ("x", "ACTIVO_RESPALDA_DFL_RESERVA_VALOR_DE_FONDO"): "ACTIVO_RESPALDA_RESERVA_VALOR_DE_FONDO",
    ("p", "FECHA_DE_LA"): "FECHA_DE_LA_OPERACION",
    ("p", "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMAC"):
        "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMACION",
    ("p", "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMAC_ION"):
        "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMACION",
    ("p", "TASA_A_FUTURO_MERCADO"): "TASA_A_FUTURO_MERCADO_POSICION_LARGA",
}


# Nombres que la ficha repite dentro de un mismo registro: (letra, tipo, nombre, aparición).
ALIAS = {
    # En los swaps (p5) la ficha usa el mismo nombre del activo objeto para el nocional del
    # contrato: se desambigua con el sufijo _NOCIONAL para no mezclar texto con número.
    ("p", "5", "ACTIVO_OBJETO_POSICION_LARGA", 1): "ACTIVO_OBJETO_POSICION_LARGA_NOCIONAL",
    ("p", "5", "ACTIVO_OBJETO_POSICION_CORTA", 1): "ACTIVO_OBJETO_POSICION_CORTA_NOCIONAL",
    ("i", "2", "DIG_RUT", 2): "DIG_RUT_PROVEEDOR_PRECIOS",
    ("i", "2", "RUT_DEUDOR", 2): "RUT_DEUDOR_SINDICADO",
    ("i", "2", "VERIFICADOR_DEUDOR", 1): "VERIFICADOR_DEUDOR_SINDICADO",
    ("p", "2", "ACTIVO_OBJETO", 1): "ACTIVO_OBJETO_POSICION_CORTA",
    ("p", "2", "ACTIVO_OBJETO", 2): "ACTIVO_OBJETO_UNIDADES",
    ("p", "3", "ACTIVO_OBJETO", 1): "ACTIVO_OBJETO_POSICION_CORTA",
    ("p", "3", "ACTIVO_OBJETO_POSICION_LARGA", 2): "ACTIVO_OBJETO_POSICION_LARGA_UNIDADES",
    ("p", "3", "ACTIVO_OBJETO_POSICION_CORTA", 1): "ACTIVO_OBJETO_POSICION_CORTA_UNIDADES",
    ("p", "4", "ACTIVO_OBJETO", 1): "ACTIVO_OBJETO_POSICION_CORTA",
    ("p", "4", "ACTIVO_OBJETO_POSICION_LARGA", 2): "ACTIVO_OBJETO_POSICION_LARGA_UNIDADES",
    ("p", "4", "ACTIVO_OBJETO_POSICION_CORTA", 1): "ACTIVO_OBJETO_POSICION_CORTA_UNIDADES",
    ("p", "6", "ACTIVO_OBJETO", 2): "ACTIVO_OBJETO_VALOR_CONTABLE",
}

# Campos que no se publican: relleno, tipo de registro y el dígito verificador
# (se publica junto al RUT, como ``97004000-5``).
_OMITIR_NOMBRE = {"FILLER", "FLLER"}
_OMITIR_INICIO = {(0, "TIPO")}
_RE_DV = re.compile(r"^(DIG_RUT|DIG|D_V|DV|VERIFICADOR)")
_RE_RUT = re.compile(r"^(RUT|NRO_RUT|RUN|NRO_RUN)")


def _reparar(nombre: str) -> str:
    for patron, reemplazo in _REPARAR:
        if patron.match(nombre):
            return re.sub(patron, reemplazo, nombre)
    return nombre


_SIN_UNIDAD = re.compile(r"UNIDAD_MONETARIA|MONEDA|UNIDAD$|CODIGO|TIPO|FECHA|NOMBRE|PAIS")


def _unidad(campo) -> str | None:
    """Unidad del campo: la anotada al lado del nombre o la que dice la descripción.

    Sólo aplica a los montos: los campos de texto (códigos, nombres) y los que la
    descripción menciona de paso ("en la unidad monetaria del instrumento") quedan sin
    sufijo, o terminarían llamándose ``unidad_monetaria_um``.
    """
    if campo.unidad:
        return campo.unidad
    if campo.tipo != "n" or _SIN_UNIDAD.search(campo.nombre):
        return None
    return unidad_del_texto(campo.descripcion)


def _con_unidad(nombre: str, unidad: str | None) -> str:
    if not unidad:
        return nombre
    sufijo = SUFIJO_UNIDAD.get(unidad)
    if not sufijo or nombre.endswith("_" + sufijo):
        return nombre
    return f"{nombre}_{sufijo}"


def columna(nombre: str) -> str:
    """Nombre publicado en la base: minúsculas, sin acentos ni guiones."""
    return re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")


def _es_fecha(campo) -> bool:
    return campo.largo == 8 and campo.decimales == 0 and (
        campo.nombre.startswith("FECHA") or "AAAAMMDD" in campo.descripcion.upper()
    )


def _es_rut(campo, siguiente) -> bool:
    """9(09) seguido del dígito verificador X(01)."""
    return (
        campo.largo == 9
        and campo.tipo == "n"
        and _RE_RUT.match(campo.nombre) is not None
        and siguiente is not None
        and siguiente.largo == 1
        and siguiente.tipo == "t"
        and _RE_DV.match(siguiente.nombre) is not None
    )


def _tipo(campo, siguiente) -> tuple[str, int]:
    """(tipo publicado, largo publicado)."""
    if _es_rut(campo, siguiente):
        return "r", campo.largo + 1
    if _es_fecha(campo):
        return "f", campo.largo
    return ("s" if campo.con_signo else campo.tipo), campo.largo


def _base(formato: str) -> dict[tuple[str, str], list[dict]]:
    """Campos de un formato con el nombre de la ficha ya reparado, sin sufijo de unidad."""
    salida: dict[tuple[str, str], list[dict]] = {}
    for clave, registro in sorted(registros(formato).items()):
        if clave not in DESTINO:
            continue
        vistos: dict[str, int] = {}
        campos: list[dict] = []
        for n, campo in enumerate(registro.campos):
            nombre = _reparar(campo.nombre)
            if nombre in _OMITIR_NOMBRE or (campo.inicio, nombre) in _OMITIR_INICIO:
                continue
            aparece = vistos[nombre] = vistos.get(nombre, 0) + 1
            nombre = ALIAS.get((clave[0], clave[1], nombre, aparece), nombre)
            nombre = PARES.get((clave[0], nombre), nombre)
            campos.append({
                "nombre": nombre,
                "aparece": aparece,
                "campo": campo,
                "siguiente": registro.campos[n + 1] if n + 1 < len(registro.campos) else None,
            })
        salida[clave] = campos
    return salida


def inventario(formato: str) -> dict[tuple[str, str], list[dict]]:
    """{(letra, tipo): [campos publicados]} de un formato, listos para publicar.

    La unidad se toma de los dos formatos: si la ficha de 2016 dice "en miles de pesos"
    y la de 2024 no lo repite, el sufijo se publica igual en las dos épocas.
    """
    base = {f: _base(f) for f in FORMATOS}
    # La unidad se guarda por (registro, nombre, aparición): los campos que la ficha repite
    # con distinta unidad ((UM) y (M$)) conservan así su propio sufijo.
    unidades: dict[tuple[tuple[str, str], str, int], str] = {}
    for f in FORMATOS:
        for clave, campos in base[f].items():
            for c in campos:
                unidad = _unidad(c["campo"])
                if unidad:
                    unidades.setdefault((clave, c["nombre"], c["aparece"]), unidad)
    salida: dict[tuple[str, str], list[dict]] = {}
    for clave, campos in base[formato].items():
        publicados: list[dict] = []
        salta_dv = False
        for c in campos:
            campo = c["campo"]
            if salta_dv:  # el dígito verificador viaja con el RUT
                salta_dv = False
                continue
            unidad = unidades.get((clave, c["nombre"], c["aparece"]))
            nombre = _con_unidad(c["nombre"], unidad)
            tipo, largo = _tipo(campo, c["siguiente"])
            if tipo == "r":
                salta_dv = True
            publicados.append({
                "nombre": nombre,
                "columna": columna(nombre),
                "inicio": campo.inicio,
                "largo": largo,
                "picture": campo.picture,
                "tipo": tipo,
                "decimales": campo.decimales,
                "unidad": unidad,
                "nombre_ficha": campo.nombre_ficha,
                "descripcion": campo.descripcion,
                "renglon": campo.renglon,
                "ficha": campo.ficha,
            })
        salida[clave] = publicados
    return salida


def escribir(ruta: Path = RUTA_JSON) -> Path:
    datos = {
        "origen": "Anexos técnicos de la Circular 1835 (CMF), copiados en seguros/fuentes/fichas_tecnicas_1835",
        "formatos": {
            formato: {
                f"{letra}{tipo}": {
                    "tabla": DESTINO[(letra, tipo)][0],
                    "subtipo": DESTINO[(letra, tipo)][1],
                    "campos": campos,
                }
                for (letra, tipo), campos in inventario(formato).items()
            }
            for formato in FORMATOS
        },
    }
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ruta


def reporte() -> None:
    for formato in FORMATOS:
        print(f"===== {formato}")
        for (letra, tipo), campos in inventario(formato).items():
            tabla, subtipo = DESTINO[(letra, tipo)]
            cols = [c["columna"] for c in campos]
            repetidas = sorted({c for c in cols if cols.count(c) > 1})
            print(f"  {letra}{tipo} {tabla}/{subtipo}: {len(campos)} campos"
                  + (f"  REPETIDAS {repetidas}" if repetidas else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escribir", action="store_true", help="escribe el JSON del inventario")
    ap.add_argument("--reporte", action="store_true", help="resume campos por tabla")
    a = ap.parse_args()
    if a.escribir:
        print(escribir())
    if a.reporte or not a.escribir:
        reporte()
