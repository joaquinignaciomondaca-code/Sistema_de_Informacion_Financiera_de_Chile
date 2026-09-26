"""Estado incremental de los EEFF.

El Markdown es la fuente. Este directorio es la corrida: un checkpoint por
documento y una partición JSONL por periodo. Si el proceso se corta, la
próxima corrida publica lo ya guardado y solo relee lo que no quedó ok.

La escritura es atómica (archivo temporal y os.replace). No se reescribe
el historial de otro periodo para actualizar un documento.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipelines.eeff.alias import ESQUEMAS_CERRADOS, PARSER_VERSION, TABLAS_COMUNES

ZONA = ZoneInfo("America/Santiago")

TABLAS = (
    "documentos",
    "balance",
    "resultados",
    "indice",
    "nota_efectivo",
    "nota_deudores",
    "cobertura",
    "validacion",
    "esquema_pendiente",
)

COLUMNAS = {
    "documentos": (
        "id_documento", "rut", "razon_social", "periodo", "fecha_corte", "tipo_eeff",
        "unidad", "fuente", "archivo", "sha256", "url_pdf", "url_visualizacion",
        "notas_en_indice", "lineas_balance", "lineas_resultados", "tablas_leidas",
        "estado_extraccion", "cuadre_balance", "diff_balance_m_clp",
        "cuadre_efectivo", "diff_efectivo_miles", "cuadre_deudores", "diff_deudores_miles",
        "estado_api", "indice_completo", "parser_version", "actualizado",
    ),
    "balance": (
        "id_linea", "id_documento", "rut", "razon_social", "periodo", "fecha_corte",
        "tipo_eeff", "estado", "nombre_cuenta", "cuenta_canonica", "nota_ref", "clase",
        "monto_miles_clp", "monto_m_clp", "monto_comparativo_miles_clp", "fuente",
    ),
    "resultados": (
        "id_linea", "id_documento", "rut", "razon_social", "periodo", "fecha_corte",
        "tipo_eeff", "estado", "nombre_cuenta", "cuenta_canonica", "nota_ref", "clase",
        "monto_miles_clp", "monto_m_clp", "monto_comparativo_miles_clp", "fuente",
    ),
    "indice": (
        "id_nota", "id_documento", "rut", "razon_social", "periodo", "tipo_eeff",
        "numero_nota", "titulo_nota", "pagina", "nota_canonica", "tabla",
        "extraida", "estado_tabla", "fuente",
    ),
    "nota_efectivo": (
        "id_linea", "id_documento", "rut", "razon_social", "periodo", "fecha_corte",
        "tipo_eeff", "numero_nota", "titulo_nota", "pagina", "concepto",
        "saldo_miles", "saldo_comparativo_miles", "es_total", "moneda", "fuente", "calidad",
    ),
    "nota_deudores": (
        "id_linea", "id_documento", "rut", "razon_social", "periodo", "fecha_corte",
        "tipo_eeff", "numero_nota", "titulo_nota", "pagina", "concepto",
        "colocacion_miles", "provision_miles", "neto_miles",
        "colocacion_comparativo_miles", "provision_comparativo_miles", "neto_comparativo_miles",
        "es_total", "moneda", "fuente", "calidad",
    ),
    "cobertura": (
        "id_cobertura", "id_documento", "rut", "razon_social", "periodo", "tipo_eeff",
        "tabla", "numeros_nota", "titulo_nota", "extraida", "lineas",
        "estado", "cuadre", "diff_miles", "indice_completo",
    ),
    "validacion": (
        "id_validacion", "id_documento", "rut", "razon_social", "periodo", "tipo_eeff",
        "tipo_api", "tipo_chequeado", "concepto", "monto_documento_m_clp", "monto_api_m_clp",
        "diff_m_clp", "numeros", "estado", "fuente_documento", "fuente_api",
    ),
    "esquema_pendiente": (
        "id_pendiente", "id_documento", "rut", "razon_social", "periodo", "tipo_eeff",
        "tabla", "numero_nota", "titulo_nota", "encabezados", "motivo",
    ),
}

PUBLICADAS = {
    "documentos": "factoring_leasing_eeff_documentos",
    "balance": "factoring_leasing_balance_lineas",
    "resultados": "factoring_leasing_resultados_lineas",
    "indice": "factoring_leasing_notas_indice",
    "nota_efectivo": "factoring_leasing_nota_efectivo",
    "nota_deudores": "factoring_leasing_nota_deudores",
    "cobertura": "factoring_leasing_notas_cobertura",
    "validacion": "factoring_leasing_validacion_api",
    "esquema_pendiente": "factoring_leasing_nota_esquema_pendiente",
}

_NOTA_LINEAS_VIEJA = (
    "id_linea", "rut", "razon_social", "periodo", "numero_nota", "titulo_nota",
    "nota_canonica", "concepto", "detalle", "monto_miles_clp",
    "monto_comparativo_miles_clp", "moneda", "fuente", "calidad",
)


def ahora() -> str:
    return datetime.now(ZONA).isoformat(timespec="seconds")


def id_documento(rut: str, periodo: str, tipo: str) -> str:
    return f"{rut}|{periodo}|{(tipo or 'ND').strip()}"


def _pid_vivo(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _escribir_atomico(path: Path, texto: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(texto)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _leer_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    filas = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        filas.append(json.loads(line))
    return filas


def _ordenar(filas: list[dict]) -> list[dict]:
    return sorted(filas, key=lambda row: (
        str(row.get("periodo") or ""),
        str(row.get("razon_social") or ""),
        str(row.get("numero_nota") or row.get("tabla") or ""),
        str(row.get("id_linea") or row.get("id_nota") or row.get("id_cobertura") or row.get("id_documento") or ""),
    ))


def _proyectar(fila: dict, columnas: tuple[str, ...]) -> dict:
    return {col: fila.get(col) for col in columnas}


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.checkpoint_path = self.root / "checkpoint.json"
        self.tablas = self.root / "tablas"

    @contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / "LOCK"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            pid = int(data.get("pid") or 0)
            if pid and pid != os.getpid() and _pid_vivo(pid):
                raise RuntimeError(f"otra corrida en curso (pid {pid}). No se pisan los JSONL.")
        _escribir_atomico(path, json.dumps({"pid": os.getpid(), "desde": ahora()}))
        try:
            yield
        finally:
            try:
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if int(data.get("pid") or 0) == os.getpid():
                        path.unlink()
            except (OSError, json.JSONDecodeError):
                pass

    def cargar_checkpoint(self) -> dict:
        if not self.checkpoint_path.exists():
            return {"version": 1, "parser_version": PARSER_VERSION, "documentos": {}}
        try:
            data = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"checkpoint ilegible, no se parte de cero: {exc}") from exc
        data.setdefault("documentos", {})
        return data

    def guardar_checkpoint(self, data: dict) -> None:
        data["version"] = 1
        data["parser_version"] = PARSER_VERSION
        data["actualizado"] = ahora()
        _escribir_atomico(self.checkpoint_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def debe_saltar(self, checkpoint: dict, clave: str, sha256: str) -> bool:
        prev = checkpoint.get("documentos", {}).get(clave) or {}
        return (
            prev.get("estado") == "ok"
            and prev.get("sha256") == sha256
            and prev.get("parser_version") == PARSER_VERSION
        )

    def reemplazar_documento(self, periodo: str, clave: str, por_tabla: dict[str, list[dict]]) -> None:
        """Saca las filas viejas de este documento y escribe las nuevas. Otras sociedades quedan."""
        for tabla in TABLAS:
            path = self.tablas / tabla / f"{periodo}.jsonl"
            previas = _leer_jsonl(path)
            resto = [row for row in previas if row.get("id_documento") != clave]
            nuevas = por_tabla.get(tabla) or []
            if not resto and not nuevas and not path.exists():
                continue
            texto = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in (resto + nuevas))
            _escribir_atomico(path, texto)

    def olvidar(self, claves: set[str]) -> list[str]:
        if not claves:
            return []
        checkpoint = self.cargar_checkpoint()
        docs = checkpoint.get("documentos", {})
        borradas = []
        for clave in sorted(claves):
            prev = docs.pop(clave, None)
            if not prev:
                continue
            periodo = clave.split("|")[1] if clave.count("|") >= 2 else ""
            if periodo:
                self.reemplazar_documento(periodo, clave, {})
            borradas.append(clave)
        if borradas:
            checkpoint["documentos"] = docs
            self.guardar_checkpoint(checkpoint)
        return borradas

    def tiene_filas(self) -> bool:
        return any(self.tablas.glob("*/*.jsonl"))

    def leer_todo(self) -> dict[str, list[dict]]:
        salida = {tabla: [] for tabla in TABLAS}
        if not self.tablas.exists():
            return salida
        for tabla in TABLAS:
            carpeta = self.tablas / tabla
            if not carpeta.exists():
                continue
            for path in sorted(carpeta.glob("*.jsonl")):
                salida[tabla].extend(_leer_jsonl(path))
        return salida

    def publicar(self, out_dir: Path, parquet: bool = True) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        todo = self.leer_todo()
        escritos = {}
        pyarrow = _cargar_pyarrow() if parquet else None
        if parquet and pyarrow is None and not getattr(self, "_aviso_parquet", False):
            print("[aviso] sin pyarrow: se publicó el JSON y no se actualizó el parquet.")
            self._aviso_parquet = True
        for tabla, nombre in PUBLICADAS.items():
            columnas = COLUMNAS[tabla]
            filas = [_proyectar(row, columnas) for row in _ordenar(todo[tabla])]
            _escribir_atomico(out_dir / f"{nombre}.json", json.dumps(filas, ensure_ascii=False, indent=2) + "\n")
            if pyarrow is not None:
                _escribir_parquet(pyarrow, out_dir / f"{nombre}.parquet", filas, columnas)
            escritos[nombre] = len(filas)
        _retirar_nota_lineas(out_dir, pyarrow)
        _escribir_atomico(out_dir / "factoring_leasing_eeff_esquemas.json", json.dumps(_esquemas(), ensure_ascii=False, indent=2) + "\n")
        return escritos

    def registrar_corrida(self, resumen: dict) -> None:
        path = self.root / "corridas.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(resumen, ensure_ascii=False) + "\n")
        _escribir_atomico(self.root / "ultima_corrida.json", json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")


def _esquemas() -> dict:
    sin = {
        tabla: "Está en el índice cuando el PDF la trae. La tabla de montos no se leyó. No se inventan columnas."
        for tabla in TABLAS_COMUNES
        if tabla not in ESQUEMAS_CERRADOS
    }
    return {
        "parser_version": PARSER_VERSION,
        "cerrados": {
            "efectivo": {
                "columnas": list(ESQUEMAS_CERRADOS["efectivo"]),
                "leido_en": "Factoring Security, marzo 2026. El saldo cuadra con la carátula.",
            },
            "deudores": {
                "columnas": list(ESQUEMAS_CERRADOS["deudores"]) + [
                    "colocacion_comparativo_miles", "provision_comparativo_miles", "neto_comparativo_miles",
                ],
                "leido_en": "Factoring Security, marzo 2026. El que cuadra con la carátula es el neto.",
                "comparativo": "Vacío si ese PDF no trae la columna. No se estima.",
            },
        },
        "sin_esquema": sin,
        "nota_lineas": "Retirada. Ninguna nota vive en una bolsa.",
    }


def _cargar_pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return None
    return pa, pq


def _tipo_columna(pa, col: str):
    if col in {
        "extraida", "es_total", "tipo_chequeado", "notas_en_indice", "lineas_balance",
        "lineas_resultados", "lineas", "numero_nota", "parser_version", "indice_completo",
    }:
        return pa.int64()
    if (
        col.endswith("_miles") or col.endswith("_clp") or col.startswith("diff_")
        or col in {"saldo_miles", "saldo_comparativo_miles"}
    ):
        return pa.float64()
    return pa.string()


def _escribir_parquet(pyarrow, path: Path, filas: list[dict], columnas: tuple[str, ...]) -> None:
    pa, pq = pyarrow
    arrays = []
    for col in columnas:
        tipo = _tipo_columna(pa, col)
        valores = [row.get(col) for row in filas]
        if tipo == pa.int64():
            valores = [None if v is None or v == "" else int(v) for v in valores]
        elif tipo == pa.float64():
            valores = [None if v is None or v == "" else float(v) for v in valores]
        else:
            valores = [None if v is None else str(v) for v in valores]
        arrays.append(pa.array(valores, type=tipo))
    table = pa.Table.from_arrays(arrays, names=list(columnas))
    tmp = path.with_suffix(".parquet.tmp")
    pq.write_table(table, tmp)
    os.replace(tmp, path)


def _retirar_nota_lineas(out_dir: Path, pyarrow) -> None:
    """La bolsa nota_lineas no se vuelve a llenar. Queda vacía para no servir filas viejas."""
    _escribir_atomico(out_dir / "factoring_leasing_nota_lineas.json", "[]\n")
    if pyarrow is None:
        return
    _escribir_parquet(pyarrow, out_dir / "factoring_leasing_nota_lineas.parquet", [], _NOTA_LINEAS_VIEJA)
