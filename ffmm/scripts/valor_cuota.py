"""Valor cuota de fondos mutuos y de fondos de inversión, derivado de la Circular 1835.

Por qué desde acá y no desde la ficha de la CMF
------------------------------------------------
La CMF publica el valor cuota de cada fondo en la pestaña 7 de su ficha (`entidad.php`), pero esa
pestaña es un formulario por fondo y no hay descarga masiva. La ruta que el repositorio ya
descarga todos los meses es otra: la **sección B.3 de la Circular 1835**, el reporte mensual de
cartera que cada aseguradora declara, donde cada línea de cuota de fondo trae `run_fondo`,
`serie`, `unidades`, `valor_cuota` y `valor_final`. Son 99.853 líneas ya publicadas en
`docs/outputs/seguros/fondos_mutuos/`, con su fuente y su hash, que hasta ahora nadie leía como
serie de valor cuota.

El grano y por qué no es «por fondo»
-----------------------------------
El valor cuota es de la **serie** del fondo, no del fondo: el 8806 reportaba en 2016-11 las series
B, G y H con 1.394,8885 / 1.042,3925 / 1.027,558. Y la serie se identifica por su **nemotécnico**,
no solo por la letra: agrupar por (período, fondo, serie) mezcla 271 casos en que una sola
aseguradorareported varias líneas del mismo fondo con letras vacías o repetidas, y los hace parecer
desacuerdos entre aseguradoras que no existen. La clave es
**(período, fondo, nemotécnico, serie)**: 51.512 grupos, de los que 1.360 discrepan, y solo 30 de
esos son de una sola aseguradora. El desvío mediano entre las que sí discrepan es de 8,6·10⁻⁵:
redondeo del propio archivo, no un valor distinto.

Las dos compuertas y de dónde salen los números
-----------------------------------------------
C1 · identidad aritmética. El archivo trae `unidades`, `valor_cuota` y `valor_final` (miles) del
mismo hecho, así que `unidades × valor_cuota` debe dar `valor_final × 1000`. Medida sobre las
99.853 líneas reales: el desvío mediano es 6,6·10⁻⁷ y el percentil 90 es 1,8·10⁻⁴, pero la cola la
forman las carteras chicas — la mediana de `valor_final` de las líneas que fallan es de **4
miles**, donde el redondeo a miles del archivo domina. Con tolerancia mixta (1.000.000 de pesos
absolutos o 0,5 % relativo) pasa el **99,85 %**.

C3 · el valor cuota tiene que ser positivo. Existe porque C1 se abre por atrás con un cero
(0 × 0 = 0 × 1.000): hay 94 líneas así en la fuente, en 5 fondos, y esos fondos sí tienen valores
normales en otros períodos.

C2 · consenso de aseguradoras. Varias aseguradoras pueden reportar la misma serie. Si todas
coinciden dentro de esa tolerancia, el valor cuota es el del fondo; si no, **no se publica un
número**: la fila sale con `valor_cuota` nulo y `estado = 'discrepancia_cu'`. Marcar es más honesto
que promediar o que quedarse con la primera.

Lo que esta tabla NO es
-----------------------
* No es el patrimonio del fondo. Es el patrimonio **que las aseguradoras tienen invertido en él**,
  una cota inferior. Por eso las columnas se llaman `unidades_aseguradoras` y
  `patrimonio_aseguradoras_m`.
* No cubre el mercado: son los fondos que alguna aseguradora reportó tener. Medido sobre lo
  publicado hoy, 309 de los 1.543 RUN del universo de fondos mutuos (20,0 %) y 1 de los 1.679 de
  fondos de inversión. La completitud es un dato de la tabla, no una promesa.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
ORIGEN_SEGUROS = RAIZ / "docs" / "outputs" / "seguros" / "fondos_mutuos"
UNIVERSO_FFMM = RAIZ / "docs" / "outputs" / "ffmm" / "ffmm_registro_fondos_universo.parquet"
MAESTRO_FI = RAIZ / "docs" / "outputs" / "fi" / "maestro_fondos_inversion.parquet"
# Nombres que la reparación de codificación no pudo dejar del todo bien (carácter perdido antes de
# llegar, o corrupción en dos capas). Llena `cargar_maestros`, con clave por RUN para no repetir:
# se la llama una vez por año de fuente y sin deduplicar salía el mismo caso doce veces.
PENDIENTES_CODIFICACION: dict[str, dict] = {}

# Tolerancias de C1 y C2, calibradas sobre las 99.853 líneas publicadas (ver docstring).
IDENTIDAD_ABS = 1_000_000.0   # pesos: el archivo redondea `valor_final` a miles
IDENTIDAD_REL = 0.005         # 0,5 %

# C4 · continuidad. Un valor cuota tiene que poder con el nivel de su propia serie. El umbral sale de
# medir la tabla completa, no de elegirlo a ojo: contra la mediana de los meses cercanos el desvío
# tiene mediana 1,6 % y p99,9 25,6 %, y el desvío más alto que corresponde a un fondo sano es 55 %
# (RUN 8684, que sube de 1.300 a 2.266 y vuelve a 1.346: un cambio de regimen real). Los cinco valores
# corruptos estan todos sobre 86 %. El hueco entre 55 % y 86 % esta vacio y 70 % cae en el medio: un
# umbral mas bajo reventaria al fondo volatil, uno mas alto dejaria pasar lo que se busca cazar.
#
# La ventana es de ±12 meses y no de los meses inmediatamente anteriores porque una serie con huecos
# rompe el criterio local. RUN 8230 serie EJECU vale unos 700.000 desde 2023 y en 2024-12 y 2025-01
# trae 727,67 y 729,99: mirando solo los dos meses siguientes, el valor sano de 2024-11 parece el
# raro, y es el bueno. Con la ventana ancha la mediana de la serie lo absuelve y cae el que corresponde.
CONTINUIDAD_REL = 0.70
CONTINUIDAD_VECINOS = 12       # meses a cada lado que entran en la referencia
CONTINUIDAD_MIN_VECINOS = 3    # con menos, la mediana de la serie no es confiable y la fila no se juzga

# Columnas de la fuente que se leen. `valor_final` viene en miles de la moneda de la línea.
FUENTE_COLS = ["periodo", "run_fondo", "serie", "nemotecnico", "unidad_monetaria",
               "unidades", "valor_cuota", "valor_final_m_clp", "rut_aseguradora"]

ESQUEMA = pa.schema([
    ("periodo", pa.string()),
    ("run_fondo", pa.string()),
    ("run_fondo_dv", pa.string()),
    ("serie", pa.string()),
    ("nemotecnico", pa.string()),
    ("sector", pa.string()),
    ("nombre_fondo", pa.string()),
    ("rut_agf", pa.string()),
    ("razon_social_agf", pa.string()),
    ("estado_fondo", pa.string()),
    ("unidad_monetaria", pa.string()),
    ("valor_cuota", pa.float64()),
    ("unidades_aseguradoras", pa.float64()),
    ("patrimonio_aseguradoras_m", pa.float64()),
    ("aseguradoras_reportantes", pa.int64()),
    ("estado", pa.string()),
])


# ---------------------------------------------------------------------------
# Codificación
# ---------------------------------------------------------------------------
# Caracteres que no aparecen en un nombre de fondo en español y que casi siempre son la huella de
# una reparación a medias: el carácter se perdió antes de llegar al repositorio y «arreglarlo»
# produciría otra cosa distinta sin avisar.
HUELLAS = ("¿", "ÿ", "Ÿ", "�", "Â")


def _tenia_mojibake(s) -> bool:
    return isinstance(s, str) and ("Ã" in s or "Â" in s)


def reparar_mojibake(s) -> str | None:
    """Deshace el UTF-8 leído como latin-1 de los nombres de fondos mutuos.

    El maestro de fondos mutuos se construyó leyendo la respuesta de la CMF en la codificación
    equivocada: 206 de 1.543 nombres quedaron como «HASTA 3 AÃ\\x91OS» (Ñ) o «INVERSIÃ\\x93N» (Ó).
    El arreglo es invertir la decodificación.

    No toda corrupción se arregla: «DEPÃ¿SITO» decodifica sin error a «DEPÿSITO», que es una cadena
    **distinta y equivocada** en lugar de una con signo de aviso. Por eso la reparación no se
    conforma con que el texto deje de verse mal: `reparado_con_huella` marca esas cases, y el
    publicador las lista en el control para que una persona las mire. Devolver el original sin más
    también sería mentir: el nombre de la CMF sí se perdió.
    """
    if not isinstance(s, str) or ("Ã" not in s and "Â" not in s):
        return s if isinstance(s, str) else None
    try:
        arreglado = s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    if "Ã" in arreglado or "Â" in arreglado:
        return s  # doble corrupción: la inversión no alcanza
    return arreglado


def reparado_con_huella(original, reparado) -> bool:
    """Verdadero si la reparación delató un carácter que ya venía perdido en el origen."""
    if not isinstance(original, str) or original == reparado:
        return False
    return any(h in reparado for h in HUELLAS)


# ---------------------------------------------------------------------------
# Compuertas
# ---------------------------------------------------------------------------
def _relativo(a: float, b: float) -> float:
    escala = max(abs(a), abs(b))
    return 0.0 if escala == 0 else abs(a - b) / escala


def identidad_ok(unidades: float, valor_cuota: float, valor_final_m: float) -> bool:
    """C1: unidades × valor_cuota ≈ valor_final × 1000, con tolerancia mixta."""
    esperado = unidades * valor_cuota
    real = valor_final_m * 1000.0
    return abs(esperado - real) <= max(IDENTIDAD_ABS, abs(real) * IDENTIDAD_REL)


def _consenso(valores: list[float]) -> tuple[float | None, str]:
    """C2 y C3: si todas las aseguradoras coinciden dentro de la tolerancia, ese es el valor cuota.

    Devuelve (valor, estado). El valor es None cuando hay discrepancia: no se promedia ni se elige
    la primera, porque cualquiera de las dos cosas inventa un número que la fuente no dio.

    C3 · el valor cuota tiene que ser positivo. Sin este control la compuerta C1 se abre por
    atrás: 0 × 0 = 0 × 1.000, así que un cero cierra la identidad y saldría publicado como si
    fuera un valor. En los datos reales hay 94 líneas así, en 5 fondos, y esos fondos tienen
    valores normales en otros períodos (el 9328, 190 veces): es un error de la línea reportada, no
    un fondo liquidado. Publicar el 0 convertiría un error de origen en un dato del sistema.
    """
    if not valores:
        return None, "sin_datos"
    mayor, menor = max(valores), min(valores)
    if _relativo(mayor, menor) > IDENTIDAD_REL:
        return None, "discrepancia_cu"
    if menor <= 0:
        return None, "valor_cuota_cero"
    return menor, "ok"


# ---------------------------------------------------------------------------
# Maestros y clasificación del RUN
# ---------------------------------------------------------------------------
def cargar_maestros() -> tuple[dict, dict]:
    """(fondos mutuos, fondos de inversión) por RUN, con el nombre ya sin mojibake.

    Los nombres cuya reparación quedó con la huella de un carácter perdido se anotan en
    `PENDIENTES_CODIFICACION` con su RUN: se publican igual, pero quedan señalados.
    """
    ffmm, fi = {}, {}
    if UNIVERSO_FFMM.exists():
        d = pq.read_table(UNIVERSO_FFMM).to_pydict()
        for i, run in enumerate(d["run_fondo"]):
            if not run:
                continue
            run = str(run).split("-")[0]
            original = d["nombre_fondo"][i]
            nombre = reparar_mojibake(original)
            if _tenia_mojibake(original) and reparado_con_huella(original, nombre):
                PENDIENTES_CODIFICACION[run] = {"run_fondo": run, "motivo": "reparado_con_huella",
                                                 "original": original, "publicado": nombre}
            elif _tenia_mojibake(original) and nombre == original:
                # Corrupción en dos capas (el 9049: «DEPÃ\x83Â¿SITO»): invertir una vez no alcanza y
                # el nombre queda como vino. Se publica igual, pero queda señalado.
                PENDIENTES_CODIFICACION[run] = {"run_fondo": run, "motivo": "no_reparable",
                                                 "original": original, "publicado": nombre}
            ffmm[run] = {
                "run_fondo_dv": d["rut_fondo_completo"][i],
                "nombre_fondo": nombre,
                "rut_agf": d["rut_agf"][i] or "",
                "razon_social_agf": d["razon_social_agf"][i] or "",
                "estado_fondo": d["estado_cmf"][i] or "",
            }
    if MAESTRO_FI.exists():
        d = pq.read_table(MAESTRO_FI).to_pydict()
        for i, run in enumerate(d["run_fondo"]):
            if not run:
                continue
            fi[str(run).split("-")[0]] = {
                "run_fondo_dv": d["rut_fondo_dv"][i],
                "nombre_fondo": d["nombre_fondo"][i],
                "rut_agf": "",
                "razon_social_agf": d["administradora"][i] or "",
                "estado_fondo": d["estado_vigencia"][i] or "",
            }
    return ffmm, fi


def clasificar(run: str, ffmm: dict, fi: dict) -> tuple[str, dict]:
    """Sector de un RUN y su ficha de maestro.

    Hay 22 RUN en los dos universos a la vez, y todos son fondos de inversión: el universo de
    fondos mutuos también los capturó, con el nombre duplicado y con la codificación rota. Cuando
    un RUN está en ambos, manda el maestro de fondos de inversión, que es el que trae `tipo_entidad`
    y el nombre limpio. No se hace cumplir la pertenencia con un nombre: se declara en el control.
    """
    if run in fi:
        return "fi", fi[run]
    if run in ffmm:
        return "ffmm", ffmm[run]
    return "sin_maestro", {}


# ---------------------------------------------------------------------------
# Agregación
# ---------------------------------------------------------------------------
def leer_fuente(ruta: Path) -> pd.DataFrame:
    """Lee un Parquet anual de `seguros/fondos_mutuos` con solo las columnas que hacen falta."""
    return pq.read_table(ruta, columns=FUENTE_COLS).to_pandas()


def _mes(periodo: str) -> int:
    """Periodo 'AAAA-MM' como mes entero, para medir distancias sin depender del calendario."""
    return int(periodo[:4]) * 12 + int(periodo[5:7])


def aplicar_continuidad(tabla: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """C4: el valor cuota tiene que poder con el nivel de su propia serie. Deja el valor fuera y explica
    por que.

    Existe porque C1, C2 y C3 no ven este caso, que es lo que lo hace peligroso. Cuando una
    aseguradora reporta `unidades`, `valor_cuota` y `valor_final` los tres escalados por el mismo
    error, la identidad aritmetica cierra igual porque compara numeros que se equivan, el valor es
    positivo, y si es la unica que reporta esa serie no hay con quien discrepar. Las tres compuertas
    dicen que el numero es bueno y queda publicado. Solo la trayectoria lo delata.

    En la tabla completa aparecieron cinco asi, todos por encima del 86 % de desvío contra la
    mediana de su serie, y los cinco son de fondos que se mueven como los demas. Uno de ellos es
    832 veces el nivel real de su serie. No se corrige el numero: se deja fuera y se dice por que,
    que es lo unico defendible sin ir a mirar la linea de origen una por una.

    Va en dos pasadas a proposito. Un valor corrupto dentro de la ventana contamina la mediana de sus
    vecinos y, con una serie corta, los condena tambien. Al excluir en la segunda pasada lo que ya
    se cayo, cada fila juzga a las que quedan en pie.
    """
    if tabla.empty:
        return tabla, []

    t = tabla.copy()
    t["_mes"] = [_mes(p) for p in t["periodo"]]
    cols = ["periodo", "run_fondo", "nemotecnico", "serie"]
    serie_cols = ["run_fondo", "nemotecnico", "serie"]
    caidas: set[tuple] = set()

    for _ in range(2):
        # Se agrupa por fondo, nemotecnico y serie: el periodo es la dimension que se quiere medir,
        # no parte de la clave. La referencia se arma solo con las filas que siguen en pie, para que
        # un valor caido no pueda contaminar a sus vecinos en la segunda pasada.
        #
        # La referencia es la mediana de la serie en la ventana, no el mes anterior. Un fondo sano
        # puede tener una serie con huecos, y mirar solo al vecino inmediato hace que el dato bueno
        # parezca el raro cuando al lado hay dos meses erroneos.
        refs: dict[tuple, list[float]] = {}
        en_pie = t[~t.set_index(cols).index.isin(caidas)]
        for clave, g in en_pie.groupby(serie_cols, sort=False):
            for _, fila in g.iterrows():
                # Los parentesis en la comparacion no son esteticos: sin ellos Python resuelve
                # `abs() <= (12 & mascara)` como una cuenta de bits entre enteros, la ventana de meses
                # deja de filtrar, cada fila se compara consigo misma y la compuerta no ve nada.
                vecinos = g[((g["_mes"] - fila["_mes"]).abs() <= CONTINUIDAD_VECINOS)
                            & (g["_mes"] != fila["_mes"])
                            & g["valor_cuota"].notna()]
                if len(vecinos) >= CONTINUIDAD_MIN_VECINOS:
                    refs[clave + (int(fila["_mes"]),)] = vecinos["valor_cuota"].tolist()

        for _, fila in en_pie.iterrows():
            clave = (fila["periodo"], fila["run_fondo"], fila["nemotecnico"], fila["serie"])
            vecinos = refs.get((fila["run_fondo"], fila["nemotecnico"], fila["serie"]) + (int(fila["_mes"]),))
            if not vecinos:
                continue
            if _relativo(float(fila["valor_cuota"]), float(np.median(vecinos))) > CONTINUIDAD_REL:
                caidas.add(clave)

    if not caidas:
        return tabla, []

    avisos = []
    for pos, fila in t.iterrows():
        clave = (fila["periodo"], fila["run_fondo"], fila["nemotecnico"], fila["serie"])
        if clave not in caidas:
            continue
        serie = t[(t["run_fondo"] == fila["run_fondo"]) & (t["nemotecnico"] == fila["nemotecnico"])
                  & (t["serie"] == fila["serie"])]
        vecinos = serie[((serie["_mes"] - fila["_mes"]).abs() <= CONTINUIDAD_VECINOS)
                        & (serie["_mes"] != fila["_mes"])].dropna(subset=["valor_cuota"])
        ref = float(vecinos["valor_cuota"].median()) if len(vecinos) else None
        mejor = _relativo(float(fila["valor_cuota"]), ref) if ref else None
        avisos.append({
            "periodo": fila["periodo"], "run_fondo": fila["run_fondo"],
            "nemotecnico": fila["nemotecnico"], "serie": fila["serie"],
            "estado": "salto_temporal",
            "origen": "una_aseguradora_varias_lineas" if int(fila["aseguradoras_reportantes"]) == 1 else "varias_aseguradoras",
            "valor_cuota_reportados": [float(fila["valor_cuota"])],
            "lineas": int(fila["aseguradoras_reportantes"]),
            "aseguradoras": int(fila["aseguradoras_reportantes"]),
            "referencia_serie": ref,
            "desviacion": None if mejor is None else round(mejor, 4),
            "meses_cercanos": int(len(vecinos)),
        })
        t.at[pos, "valor_cuota"] = None
        t.at[pos, "estado"] = "salto_temporal"

    avisos.sort(key=lambda a: (a["periodo"], a["run_fondo"]))
    return t.drop(columns=["_mes"]), avisos


def agregar(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """De las líneas de las aseguradoras a una fila por (período, fondo, nemotécnico, serie).

    Devuelve (tabla, avisos). En la tabla, `valor_cuota` viene nulo cuando el estado no es `ok`:
    la ausencia es información, y `unidades_aseguradoras` y `patrimonio_aseguradoras_m` sí se
    publican siempre, porque son la suma de lo que cada aseguradora declaró tener, y eso no depende
    de que el valor cuota esté confirmado.
    """
    if df.empty:
        return pd.DataFrame(columns=[f.name for f in ESQUEMA]), []

    df = df.copy()
    df["serie"] = df["serie"].fillna("").astype(str)
    df["run_fondo"] = df["run_fondo"].astype(str)
    df["nemotecnico"] = df["nemotecnico"].fillna("").astype(str)
    df["identidad_ok"] = [identidad_ok(u, v, f) for u, v, f in
                          zip(df["unidades"], df["valor_cuota"], df["valor_final_m_clp"])]

    filas, avisos = [], []
    clave_cols = ["periodo", "run_fondo", "nemotecnico", "serie"]
    for clave, g in df.groupby(clave_cols, sort=True):
        periodo, run, nemotecnico, serie = clave
        confirmadas = g[g["identidad_ok"]]
        if confirmadas.empty:
            # Ninguna línea cierra con la identidad: no hay forma de saber cuál es el valor cuota.
            estado = "identidad_falla"
            valor = None
        else:
            valor, estado = _consenso(list(confirmadas["valor_cuota"]))

        if estado != "ok":
            reportados = sorted({round(v, 4) for v in g["valor_cuota"]})
            aseguradoras = int(g["rut_aseguradora"].nunique())
            avisos.append({
                "periodo": periodo, "run_fondo": run, "nemotecnico": nemotecnico, "serie": serie,
                "estado": estado,
                "origen": "varias_aseguradoras" if aseguradoras > 1 else "una_aseguradora_varias_lineas",
                "valor_cuota_reportados": reportados[:5],
                "lineas": int(len(g)),
                "aseguradoras": aseguradoras,
            })

        # Casi siempre una moneda; cuando el grupo la mezcla, se declara con «|» en vez de elegir.
        monedas = sorted({m for m in g["unidad_monetaria"] if m})
        filas.append({
            "periodo": periodo,
            "run_fondo": run,
            "nemotecnico": nemotecnico,
            "serie": serie,
            "unidad_monetaria": "|".join(monedas),
            "valor_cuota": valor,
            "unidades_aseguradoras": float(g["unidades"].sum()),
            "patrimonio_aseguradoras_m": float(g["valor_final_m_clp"].sum()),
            "aseguradoras_reportantes": int(g["rut_aseguradora"].nunique()),
            "estado": estado,
        })

    tabla = pd.DataFrame(filas)
    # C4 no se aplica aqui: `agregar` se llama una vez por año y la continuidad se juzga contra los
    # meses vecinos de la misma serie, que casi siempre viven en otro archivo. El publicador la
    # aplica sobre la tabla concatenationada, en `reconstruir`.
    ffmm, fi = cargar_maestros()
    sectores, fichas = zip(*(clasificar(r, ffmm, fi) for r in tabla["run_fondo"]))
    tabla.insert(2, "run_fondo_dv", [f.get("run_fondo_dv", "") for f in fichas])
    tabla.insert(5, "sector", sectores)
    tabla.insert(6, "nombre_fondo", [f.get("nombre_fondo", "") for f in fichas])
    tabla.insert(7, "rut_agf", [f.get("rut_agf", "") for f in fichas])
    tabla.insert(8, "razon_social_agf", [f.get("razon_social_agf", "") for f in fichas])
    tabla.insert(9, "estado_fondo", [f.get("estado_fondo", "") for f in fichas])
    return tabla[[f.name for f in ESQUEMA]], avisos


def publicar(df: pd.DataFrame, ruta: Path) -> None:
    """Escribe el Parquet anual con el esquema fijo y compresión del repositorio."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tabla = pa.Table.from_pandas(df, schema=ESQUEMA, preserve_index=False)
    pq.write_table(tabla, tmp, compression="zstd", compression_level=9)
    os.replace(tmp, ruta)
