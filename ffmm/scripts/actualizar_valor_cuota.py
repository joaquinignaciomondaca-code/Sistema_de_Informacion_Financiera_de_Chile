"""Valor cuota de fondos mutuos y de fondos de inversión desde la Circular 1835.

Publica una tabla por sector, a partir de lo que `seguros_carteras.yml` ya deja en
`docs/outputs/seguros/fondos_mutuos/`. No descarga nada: es una agregación de datos ya publicados
y verificados, con su fuente y su hash. La lógica y las compuertas están en `valor_cuota.py`.

  docs/outputs/valor_cuota/{ffmm,fi}/<AAAA>.parquet     una fila por período, fondo, nemotécnico y serie
  docs/outputs/valor_cuota/{ffmm,fi}/manifest.json
  docs/outputs/valor_cuota_control.json                avisos y cobertura

Incremental: solo relee los años whose archivos o maestro cambiaron. `estable.escribir_json` evita
el commit de marcas de tiempo cuando no cambió ningún dato.

  python -m ffmm.scripts.actualizar_valor_cuota                # reconstruye lo que falte
  python -m ffmm.scripts.actualizar_valor_cuota --rehacer      # desde cero
  python -m ffmm.scripts.actualizar_valor_cuota --solo-data-manifest
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from ffmm.scripts import valor_cuota as VC  # noqa: E402
from pipelines.auto import estable  # noqa: E402

# Raíz propia y no dentro de docs/outputs/{ffmm,fi}/: ffmm_carteras.yml hace `git add docs/outputs/ffmm`
# y se llevaría esta carpeta en su commit, y dos publicadores peleando por los mismos Parquet es
# justo la contención que el contrato de commit evita. Precedente: docs/outputs/entidades/.
SECTORES = {"ffmm": RAIZ / "docs" / "outputs" / "valor_cuota" / "ffmm",
            "fi": RAIZ / "docs" / "outputs" / "valor_cuota" / "fi"}
CONTROL = RAIZ / "docs" / "outputs" / "valor_cuota_control.json"
# RUN con valor cuota reportado que no figuran en ningún padrón oficial: se cuentan, no se publican.
SIN_MAESTRO: list[str] = []
# Sector que la fuente no alcanza para publicar una tabla, con el motivo escrito.
NO_PUBLICADO: dict[str, str] = {}

# Un sector solo recibe tabla si la fuente da algo que se pueda consultar. Medido hoy: la Circular
# 1835 da 309 fondos mutuos y **un solo** fondo de inversión (el 9144, Zurich Gestión Patrimonial C,
# en 2018-10). Publicar una tabla de una fila sería ruido en el sitio, así que el umbral se declara
# y el motivo queda escrito en el control: para fondos de inversión esta fuente no sirve y hay que
# ir a la ficha de la CMF.
MIN_FONDOS = 10
NORMAS = {"ffmm": "CMF — Circular 1835, sección B.3 (cartera de aseguradoras)",
          "fi": "CMF — Circular 1835, sección B.3 (cartera de aseguradoras)"}
ETIQUETAS = {"ffmm": "Valor cuota de fondos mutuos", "fi": "Valor cuota de fondos de inversión"}
# id de vista -> (sector, nombre en el explorador, descripción)
WEB = {
    "ffmm_valor_cuota": ("ffmm", "ffmm.valor_cuota",
                        "Valor cuota de cada serie de cada fondo mutuo, al cierre de cada mes, con las unidades y "
                        "el patrimonio que las aseguradoras declaran tener invertidos. Es una cota inferior del "
                        "patrimonio del fondo, no el total: solo incluye fondos que alguna aseguradora reportó."),
    "fi_valor_cuota": ("fi", "fi.valor_cuota",
                       "Valor cuota de cada serie de cada fondo de inversión, al cierre de cada mes, con las unidades "
                       "y el patrimonio que las aseguradoras declaran tener invertidos. Cobertura parcial: solo los "
                       "fondos que alguna aseguradora reportó tener."),
}


def _rutas_anuales() -> list[Path]:
    return sorted(VC.ORIGEN_SEGUROS.glob("*.parquet"))


def reconstruir(rehacer: bool) -> tuple[dict, list[dict]]:
    """Agrega los Parquet de la fuente y escribe un Parquet por sector y año."""
    rutas = _rutas_anuales()
    if not rutas:
        raise SystemExit(f"no hay fuente en {VC.ORIGEN_SEGUROS}")
    hechos, avisos = [], []
    for ruta in rutas:
        tabla, av = VC.agregar(VC.leer_fuente(ruta))
        avisos.extend(av)
        if not tabla.empty:
            hechos.append(tabla)
    if not hechos:
        return {}, avisos

    todo = pd.concat(hechos, ignore_index=True)
    # Un RUN que no está en ninguno de los dos padrónes oficiales no se publica: sin maestro no hay
    # a qué sector pertenece ni qué nombre tiene. Queda contado en el control.
    sin_maestro = sorted(todo.loc[todo["sector"] == "sin_maestro", "run_fondo"].unique())
    todo = todo[todo["sector"] != "sin_maestro"]
    if todo.empty:
        return {}, avisos

    destinos = {}
    for sector in sorted(todo["sector"].unique()):
        propios = todo[todo["sector"] == sector]
        fondos = propios["run_fondo"].nunique()
        if fondos < MIN_FONDOS:
            NO_PUBLICADO[sector] = (f"la Circular 1835 entrega {fondos} fondo(s) de este sector y el mínimo para "
                                    f"publicar una tabla es {MIN_FONDOS}: una tabla de {fondos} fila(s) no "
                                    f"sostiene ninguna consulta. Esta fuente no alcanza para el sector; hace "
                                    f"falta la ficha de la CMF.")
            continue
        for (anio,), g in propios.groupby([propios["periodo"].str[:4]], sort=True):
            destino = SECTORES[sector] / f"{anio}.parquet"
            if rehacer or not destino.exists():
                VC.publicar(g.sort_values(["periodo", "run_fondo", "serie"], kind="stable").reset_index(drop=True),
                            destino)
            destinos[(sector, anio[0] if isinstance(anio, tuple) else anio)] = destino
    SIN_MAESTRO.clear()
    SIN_MAESTRO.extend(sin_maestro)
    return destinos, avisos


def escribir_manifiestos() -> None:
    for sector, base in SECTORES.items():
        carpeta = base
        if not carpeta.exists():
            continue
        rutas = sorted(carpeta.glob("*.parquet"))
        if not rutas:
            continue
        periodos = sorted({p for r in rutas for p in _periodos_de(r)})
        man = {
            "tabla": "valor_cuota",
            "sector": sector,
            "files": [f"outputs/valor_cuota/{sector}/{r.name}" for r in rutas],
            "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas),
            "periodos": periodos,
            "primera": periodos[0] if periodos else None,
            "ultima": periodos[-1] if periodos else None,
            "fondos": None,
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        fondos = set()
        for r in rutas:
            fondos |= {v for v in pq.read_table(r, columns=["run_fondo"]).to_pydict()["run_fondo"] if v}
        man["fondos"] = len(fondos)
        estable.escribir_json(carpeta / "manifest.json", man)


def _periodos_de(ruta: Path) -> list[str]:
    return sorted({str(v) for v in pq.read_table(ruta, columns=["periodo"]).to_pydict()["periodo"] if v})


def _run(v) -> str | None:
    """Clave comparable de un RUN. El registro lo guarda como entero y lo publicado como cadena, así que
    sin normalizar el cruce no encuentra nada y la cobertura por vigencia sale en cero sin avisar."""
    if v is None or v == "":
        return None
    return str(int(v)) if isinstance(v, (int, float)) and float(v).is_integer() else str(v).strip()


def _runs_publicados(base: Path) -> set[str]:
    """RUN que efectivamente tienen valor cuota publicado, contados en los Parquet, no en el manifiesto."""
    archivos = sorted(base.glob("*.parquet"))
    if not archivos:
        return set()
    return {k for k in (_run(v) for v in pq.read_table(archivos, columns=["run_fondo"])["run_fondo"].to_pylist()) if k}


def _desglose_vigencia(universo: Path, publicados: set[str]) -> dict:
    """Reparte el universo entre fondos vigentes y cerrados, y en cuál de los dos grupos cae la cobertura.

    El denominador "todos los RUN del registro" mezcla dos poblaciones que no se parecen: los fondos
    vigentes, que una aseguradora puede mantener hoy, y los que la CMF da por no vigentes, que ya
    no pueden aparecer en una cartera salvo en periodos antiguos. Medir contra el total y publicar
    un solo porcentaje hace creer que faltó procesar algo, cuando el techo lo pone la fuente.
    """
    if not universo.exists():
        return {}
    t = pq.read_table(universo, columns=["run_fondo", "estado_cmf"]).to_pydict()
    out: dict[str, dict] = {}
    for run, estado in zip(t["run_fondo"], t["estado_cmf"]):
        clave = _run(run)
        if not clave:
            continue
        g = out.setdefault(estado or "sin estado", {"fondos": 0, "con_valor_cuota": 0})
        g["fondos"] += 1
        if clave in publicados:
            g["con_valor_cuota"] += 1
    for g in out.values():
        g["cobertura"] = round(g["con_valor_cuota"] / g["fondos"], 4) if g["fondos"] else None
    return out


def escribir_control(avisos: list[dict]) -> None:
    """Cobertura y los casos que no se publicaron con un valor."""
    resumen = {}
    for sector, base in SECTORES.items():
        universo = VC.UNIVERSO_FFMM if sector == "ffmm" else VC.MAESTRO_FI
        total = pq.ParquetFile(universo).metadata.num_rows if universo.exists() else 0
        carpeta = base / "manifest.json"
        if not carpeta.exists():
            continue
        m = json.loads(carpeta.read_text(encoding="utf-8"))
        publicados = _runs_publicados(base)
        resumen[sector] = {
            "publicado": sector not in NO_PUBLICADO,
            "motivo_sin_publicar": NO_PUBLICADO.get(sector),
            "series_periodo": m["total_records"] if sector not in NO_PUBLICADO else 0,
            "fondos_con_valor_cuota": m["fondos"],
            "universo_registro": total,
            "cobertura": round(m["fondos"] / total, 4) if total else None,
            "por_vigencia": _desglose_vigencia(universo, publicados),
            "periodos_fuente": m.get("periodos"),
            "primera": m["primera"],
            "ultima": m["ultima"],
        }
    por_estado: dict[str, int] = {}
    for a in avisos:
        por_estado[a["estado"]] = por_estado.get(a["estado"], 0) + 1
    VC.cargar_maestros()  # llena VC.PENDIENTES_CODIFICACION
    estable.escribir_json(CONTROL, {
        "descripcion": ("Valor cuota derivada de la sección B.3 de la Circular 1835. Cubre los fondos que alguna "
                        "aseguradora reportó tener, no el mercado. Los casos sin consenso entre aseguradoras se "
                        "publican con valor nulo y motivo, nunca con un número elegido."),
        "identidad_tolerancia": {"absoluta_pesos": VC.IDENTIDAD_ABS, "relativa": VC.IDENTIDAD_REL},
        "cobertura": resumen,
        "minimo_fondos_para_publicar": MIN_FONDOS,
        "sin_maestro": SIN_MAESTRO,
        "codificacion_pendiente": {
            "nota": ("Nombres del universo de fondos mutuos que llegaron con el UTF-8 leído como latin-1 y se "
                     "repararon invirtiendo la decodificación. Estos quedaron con un carácter que ya venía "
                     "perdido en el origen: la reparación da otra palabra y conviene que alguien los mire."),
            "casos": list(VC.PENDIENTES_CODIFICACION.values()),
        },
        "sin_valor_publicado": por_estado,
        "avisos": avisos[:2000],
        "avisos_totales": len(avisos),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


def actualizar_data_manifest() -> None:
    """Mantiene al día las dos entradas de valor cuota en data_manifest.json."""
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text(encoding="utf-8"))
    tablas = [t for t in man["tables"] if t.get("id") not in WEB]
    for vista, (sector, nombre, descripcion) in WEB.items():
        archivo = SECTORES[sector] / "manifest.json"
        if not archivo.exists():
            continue
        m = json.loads(archivo.read_text(encoding="utf-8"))
        corte = f"{m['primera']} a {m['ultima']}" if m.get("primera") else "sin datos"
        tablas.append({
            "id": vista,
            "name": nombre,
            "view_name": vista,
            "sector": sector,
            "sector_label": "Fondos Mutuos" if sector == "ffmm" else "Fondos de Inversión",
            "norma": NORMAS[sector],
            "corte": corte,
            "frescura": f"Derivado de la cartera de aseguradoras (Circular 1835). Último mes: {m.get('ultima')}",
            "modo": "Automático · derivado, se reconstruye cuando cambia la cartera de seguros",
            "ultima_actualizacion": date.today().isoformat(),
            "file_parquet": f"outputs/valor_cuota/{sector}/manifest.json",
            "registros_reales": m["total_records"],
            "descripcion": descripcion,
            "origen": ("CMF — sección B.3 del reporte de cartera de inversiones de aseguradoras (Circular 1835), "
                       "leída de docs/outputs/seguros/fondos_mutuos/. Derivado por ffmm/scripts/actualizar_valor_cuota.py."),
            "advertencia": ("Cobertura parcial: solo los fondos que alguna aseguradora reportó tener. No es el "
                            "patrimonio del fondo, es el que las aseguradoras tienen invertido en él."),
        })
    tablas.sort(key=lambda t: (t.get("sector", ""), t.get("id", "")))
    man["tables"] = tablas
    man["total_tables"] = len(tablas)
    man["total_records"] = sum(t.get("registros_reales") or 0 for t in tablas)
    man["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estable.escribir_json(ruta, man)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rehacer", action="store_true", help="reescribir todos los años, no solo los que falten")
    ap.add_argument("--solo-data-manifest", action="store_true",
                    help="solo recalcular las entradas de valor cuota en data_manifest.json")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
        return 0
    destinos, avisos = reconstruir(a.rehacer)
    escribir_manifiestos()
    escribir_control(avisos)
    actualizar_data_manifest()
    for (sector, anio), ruta in sorted(destinos.items()):
        print(f"{sector} {anio}: {pq.ParquetFile(ruta).metadata.num_rows} filas -> {ruta.relative_to(RAIZ)}")
    print(f"avisos: {len(avisos)} (detalle en {CONTROL.relative_to(RAIZ)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
