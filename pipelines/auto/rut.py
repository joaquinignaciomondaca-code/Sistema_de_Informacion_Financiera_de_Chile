"""Convención canónica de RUT para todo el sistema (datos publicados y pipelines).

Formatos:
    A (completo)   97.004.000-5   puntos + guión + DV  → `rut_completo`
    B (con DV)     97004000-5     cuerpo + guión + DV  → `rut_dv`
    C (cuerpo)     97004000       solo cuerpo numérico → `rut` y FK `rut_<entidad>`

Reglas de normalización (idempotentes):
  1. `rut` en A o B → `rut` = cuerpo (C) y `rut_dv` = cuerpo-DV (B).
  2. `rut_cuerpo` junto a `rut` → se retira; `rut` toma su valor (C); si el
     valor anterior de `rut` traía DV, ese pasa a `rut_dv`.
  3. `rut_formateado` → renombrada `rut_completo` (formato A).
  4. `*_dv` (ej. `rut_fondo_dv`) → B.
  5. `*_completo` → A cuando el cuerpo tiene ≥6 cifras; RUNs de fondo de
     4-5 cifras quedan en B (la fuente no trae puntos para RUN).
  6. `rut_<entidad>` (FK) → C.
  7. `run_*` y columnas numéricas (int64 ya es el cuerpo) → sin cambios.
"""
from __future__ import annotations

import re

RE_A = re.compile(r"^(\d{1,6}(?:\.\d{3}){1,2})-([\dKk])$")
RE_B = re.compile(r"^(\d{4,9})-([\dKk])$")
RE_C = re.compile(r"^\d{4,9}$")

# FK: rut_ algo, pero no las variantes con formato propio.
RE_FK = re.compile(r"^rut_(?!dv$)(?!completo$)(?!cuerpo$)(?!formateado$)(?!.*_dv$)(?!.*_completo$)([a-z_]+)$")


# ---------------------------------------------------------------------------
# Dígito verificador (algoritmo oficial módulo 11)
# ---------------------------------------------------------------------------
def dv(cuerpo: str) -> str:
    """DV oficial: multiplicadores 2,3,4,5,6,7 (vuelve a 2) sobre el cuerpo invertido."""
    s = 0
    mul = 2
    for ch in reversed(str(cuerpo).strip()):
        s += int(ch) * mul
        mul = 2 if mul == 7 else mul + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def dv_valido(valor: str) -> bool:
    """True si `valor` (A o B) lleva su DV correcto."""
    n = _norm(valor)
    return n is not None and n[1] is not None and n[1].upper() == dv(n[0])


# ---------------------------------------------------------------------------
# Parseo y formateo
# ---------------------------------------------------------------------------
def _norm(s) -> tuple[str, str | None] | None:
    """Devuelve (cuerpo, dv|None) para A/B/C; None si no parsea."""
    if s is None:
        return None
    t = str(s).strip()
    if not t:
        return None
    m = RE_A.match(t) or RE_B.match(t)
    if m:
        return m.group(1).replace(".", ""), m.group(2).upper()
    if RE_C.match(t):
        return t, None
    return None


def cuerpo(v):
    n = _norm(v)
    return None if n is None else n[0]


def con_dv(v) -> str | None:
    """B: cuerpo-DV (recalcula el DV si el valor no traía DV válido)."""
    n = _norm(v)
    if n is None:
        return None
    c, d = n
    if d is None:
        d = dv(c)
    return f"{c}-{d}"


def con_puntos(v) -> str | None:
    """A: puntos de miles + guión + DV. Solo cuerpos de ≥6 cifras (RUN queda B)."""
    n = _norm(v)
    if n is None:
        return None
    c, d = n
    if len(c) < 6:
        return con_dv(v)
    if d is None:
        d = dv(c)
    grupos = []
    for i in range(len(c) - 1, -1, -3):
        grupos.append(c[max(0, i - 2):i + 1])
    return ".".join(reversed(grupos)) + f"-{d}"


def formato(v) -> str:
    s = str(v).strip() if v is not None else ""
    return "A" if RE_A.match(s) else "B" if RE_B.match(s) else "C" if RE_C.match(s) else "X"


# ---------------------------------------------------------------------------
# Qué operación toca cada columna
# ---------------------------------------------------------------------------
def _op_de(nombre: str) -> tuple[str | None, None]:
    """Operación para el nombre de columna: 'cuerpo' | 'con_dv' | 'con_puntos' | None."""
    nombre = str(nombre)
    if nombre in ("run_fondo",) or nombre.startswith("run_"):
        return None, None
    if nombre == "rut":
        return "cuerpo", None  # el paso especial (cuerpo + rut_dv) va en normalizar_registro
    if nombre == "rut_dv" or nombre.endswith("_dv"):
        return "con_dv", None
    if nombre == "rut_formateado":
        return "con_puntos", None
    if nombre.endswith("_completo"):
        return "con_puntos", None
    if RE_FK.match(nombre):
        return "cuerpo", None
    return None, None


def transformadora(nombre: str):
    op, _ = _op_de(nombre)
    return {"cuerpo": lambda v: cuerpo(v), "con_dv": con_dv, "con_puntos": con_puntos}.get(op)


# ---------------------------------------------------------------------------
# Normalización registro a registro (JSON / listas)
# ---------------------------------------------------------------------------
def normalizar_registro(reg: dict) -> tuple[dict, list[str]]:
    """Devuelve (registro normalizado, cambios). No muta el original."""
    reg = dict(reg)
    cambios: list[str] = []

    # 1. rut_formateado → rut_completo (A)
    if "rut_formateado" in reg:
        v = con_puntos(reg.pop("rut_formateado"))
        if v is not None:
            reg["rut_completo"] = v
        cambios.append("rut_formateado→rut_completo")

    # 2. rut A/B → rut C + rut_dv B
    if "rut" in reg and reg["rut"] is not None:
        f = formato(reg["rut"])
        if f in ("A", "B"):
            if "rut_dv" not in reg:
                reg["rut_dv"] = con_dv(reg["rut"])
            reg["rut"] = cuerpo(reg["rut"])
            cambios.append("rut→C (+rut_dv)")

    # 3. rut_cuerpo + rut → rut C, rut_dv (si la anterior traía DV), sin rut_cuerpo
    if "rut_cuerpo" in reg and "rut" in reg:
        b = reg.pop("rut_cuerpo")
        if reg.get("rut") != b:
            reg["rut"] = b
        if "rut_dv" not in reg and (b is not None and formato(b) in ("A", "B")):
            reg["rut_dv"] = con_dv(b)
        cambios.append("rut_cuerpo→(rut, rut_dv)")

    # 4. restantes: FK→C, *_dv→B, *_completo→A
    for k in list(reg):
        op, _ = _op_de(k)
        if op is None:
            continue
        v = reg[k]
        if v is None or not isinstance(v, str):
            continue
        nueva = {"cuerpo": cuerpo, "con_dv": con_dv, "con_puntos": con_puntos}[op](v)
        if nueva is not None and nueva != v:
            reg[k] = nueva
            cambios.append(f"{k}→{op}")
    return reg, cambios


def normalizar_registros(regs: list[dict]) -> tuple[list[dict], set[str]]:
    out, todos = [], set()
    for r in regs:
        r2, cam = normalizar_registro(r)
        out.append(r2)
        todos.update(cam)
    return out, todos


# ---------------------------------------------------------------------------
# Normalización vectorizada (PyArrow) para Parquet
# ---------------------------------------------------------------------------
def normalizar_tabla(t) -> tuple["pa.Table", set[str]]:  # noqa: F821
    """Aplica las mismas reglas sobre una tabla PyArrow (solo columnas de texto).

    Devuelve (tabla, cambios). Los valores se convierten con las mismas
    funciones de referencia; el resultado es idempotente.
    """
    import pyarrow as pa
    import pyarrow.compute as pc

    cambios: set[str] = set()
    nombres = list(t.column_names)
    TIPO_STR = ("string", "large_string")

    def _es_str(nombre: str) -> bool:
        return str(t[nombre].type) in TIPO_STR

    def _cambios(vals, nuevos) -> bool:
        return any(a != b for a, b in zip(vals, nuevos))

    # 1. rut_formateado → rut_completo (A)
    if "rut_formateado" in nombres and _es_str("rut_formateado"):
        vals = t["rut_formateado"].to_pylist()
        nuevos = [con_puntos(v) if isinstance(v, str) else v for v in vals]
        if _cambios(vals, nuevos):
            cambios.add("rut_formateado→rut_completo")
        t = t.set_column(nombres.index("rut_formateado"), "rut_completo", pa.array(nuevos, type=pa.string()))
        nombres = list(t.column_names)

    # 2. rut A/B → rut C (+rut_dv B)
    if "rut" in nombres and _es_str("rut"):
        vals = t["rut"].to_pylist()
        mask = [v is not None and formato(v) in ("A", "B") for v in vals]
        if any(mask):
            nuevos = [cuerpo(v) if m else v for m, v in zip(mask, vals)]
            t = t.set_column(nombres.index("rut"), "rut", pa.array(nuevos, type=pa.string()))
            nombres = list(t.column_names)
            if "rut_dv" in nombres and _es_str("rut_dv"):
                dv_vals = t["rut_dv"].to_pylist()
                nuevos_dv = [
                    con_dv(v) if (m and (d is None or d != con_dv(v))) else d
                    for m, v, d in zip(mask, vals, dv_vals)
                ]
                t = t.set_column(nombres.index("rut_dv"), "rut_dv", pa.array(nuevos_dv, type=pa.string()))
            else:
                t = t.append_column("rut_dv", pa.array(
                    [con_dv(v) if m else None for m, v in zip(mask, vals)], type=pa.string()))
                nombres = list(t.column_names)
            cambios.add("rut→C (+rut_dv)")

    # 3. rut_cuerpo junto a rut → se retira (rut toma su valor)
    if "rut_cuerpo" in nombres and "rut" in nombres:
        if _es_str("rut_cuerpo") and _es_str("rut"):
            rc, rut = t["rut_cuerpo"].to_pylist(), t["rut"].to_pylist()
            merged = [r if c is None else c for c, r in zip(rc, rut)]
            if any(a != b for a, b in zip(merged, rut)):
                t = t.set_column(nombres.index("rut"), "rut", pa.array(merged, type=pa.string()))
        t = t.drop("rut_cuerpo")
        nombres = list(t.column_names)
        cambios.add("rut_cuerpo→(rut, rut_dv)")

    # 4. restantes: FK→C, *_dv→B, *_completo→A
    for k in list(t.column_names):
        op, _ = _op_de(k)
        if op is None or k in ("rut", "rut_cuerpo", "rut_formateado"):
            continue
        if not _es_str(k):
            continue  # numérico (int64 = cuerpo) o nulo: fuera de la convención de texto
        fn = {"cuerpo": cuerpo, "con_dv": con_dv, "con_puntos": con_puntos}[op]
        vals = t[k].to_pylist()
        nuevos = [fn(v) if isinstance(v, str) and v != "" else v for v in vals]
        if _cambios(vals, nuevos):
            t = t.set_column(t.column_names.index(k), k, pa.array(nuevos, type=pa.string()))
            cambios.add(f"{k}→{op}")
    return t, cambios


def normalizar_dataframe(df):
    """pandas → normalizado (mismas reglas; conserva tipos no-RUT)."""
    import pyarrow as pa

    t = pa.Table.from_pandas(df, preserve_index=False)
    t2, _ = normalizar_tabla(t)
    return t2.to_pandas()
