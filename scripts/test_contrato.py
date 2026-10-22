#!/usr/bin/env python3
"""Test de contrato de la API (fase 1d de la ruta).

Es el test del **consumidor**, no del generador: mira lo publicado por HTTP, como
lo haría un tercero, y falla si el contrato promete algo que no está.

  1d.1  Las rutas del catálogo existen: 0 × 404 entre esquemas, particiones y
        los 728 Parquet.
  1d.2  El esquema declarado es el `DESCRIBE` real, columna y tipo.
  1d.3  `views.sql` crea las 105 vistas y los 4 objetos vacíos no crean ninguna,
        con su motivo escrito.
  1d.4  Las 156 consultas publicadas corren y devuelven filas; el vacío solo se
        admite si la tabla de la consulta está declarada vacía.
  1d.5  Los ejemplos del README siguen siendo ciertos: el cruce devuelve un
        subconjunto de `bancos_lista_entidades`, y el período histórico fijado
        (2026-09) mantiene los mismos cinco países en cabeza.
  1d.6  `bytes` y `sha256` declarados coinciden con el archivo, y una descarga
        por HTTP trae exactamente los bytes anunciados.
  1d.7  Cobertura cruzada: manifiesto ↔ catálogo y `SEMANTIC_VIEWS` ↔ contrato.

Lo que este test **no** puede verificar solo: que el sitio de GitHub Pages
responda. Se sirve `docs/` con `http.server` en un puerto efímero, igual que
`probar_maquina_limpia.py`.

Tiene autoprueba: `--autoprueba` corre el test contra una copia con una columna
renombrada y un SHA-256 alterado y exige que **falle**. Un test que no puede
fallar no prueba nada.

    python3 scripts/test_contrato.py              # informe (~20 s)
    python3 scripts/test_contrato.py --check      # exit 1 si algo falla
    python3 scripts/test_contrato.py --autoprueba # además, prueba en negativo
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
V1 = DOCS / "api" / "v1"
LOG = DOCS / "api" / "test_contrato.log"
sys.path.insert(0, str(RAIZ))

# 1d.5 · Expectativa histórica. Se fija el período y se comparan **conjuntos**,
# no conteos: la CMF republica cierres y el pipeline reprocesa carteras, así que
# un número exacto caduca (pasó entre el 20 y el 22 de octubre de 2026), pero el
# orden de los países que concentran la inversión en el exterior no cambió.
PERIODO_HISTORICO = "2026-09"
TOP5_HISTORICO = ["US", "LU", "IE", "BR", "GB"]

# 1d.2 · Columnas declaradas que hoy no tienen un solo valor. No se tapan: se
# listan, se cuentan y se vigilan, porque un `WHERE rut = '97004000'` sobre una
# columna así devuelve 0 filas **sin error**. Tarea 1d.8 de la ruta.
COLUMNAS_VACIAS_CONOCIDAS = {
    # El registro RGAGF de la CMF no publica un código institucional: la columna
    # existe porque el maestro de entidades comparte plantilla con CCAF, donde sí
    # hay código para las cajas emisoras. Se declara vacía en el diccionario.
    "agf_lista_entidades.codigo_cmf": "la CMF no publica código institucional para AGF (1d.8.1)",
}

class Servidor:
    """Sirve un directorio por HTTP en un puerto efímero."""

    def __init__(self, raiz: Path) -> None:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.puerto = s.getsockname()[1]
        manejador = functools.partial(_SinRuido, directory=str(raiz))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", self.puerto), manejador)
        self.httpd.daemon_threads = True
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.puerto}"

    def cerrar(self) -> None:
        self.httpd.shutdown()


class _SinRuido(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_: object) -> None:  # el informe ya dice lo que importa
        return


def estado(url: str, metodo: str = "HEAD") -> int:
    peticion = urllib.request.Request(url, method=metodo)
    try:
        with urllib.request.urlopen(peticion, timeout=30) as r:
            if metodo == "GET":
                r.read(1)
            return r.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001 - red caída o timeout
        return 0


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def ejecutar(raiz: Path, base: str) -> tuple[list[tuple[str, bool, str]], list[str]]:
    """Corre las siete comprobaciones. Devuelve (resultados, avisos)."""
    import duckdb

    checks: list[tuple[str, bool, str]] = []
    avisos: list[str] = []
    v1 = raiz / "api" / "v1"
    catalogo = json.loads((v1 / "catalog.json").read_text(encoding="utf-8"))
    objetos = catalogo["objetos"]

    def anotar(codigo: str, ok: bool, detalle: str) -> None:
        checks.append((codigo, ok, detalle))

    # --- 1d.1 · rutas -------------------------------------------------------
    t0 = time.time()
    revisadas = rotas = 0
    for objeto in objetos:
        for ruta in (objeto["esquema"], objeto["particiones_url"]):
            revisadas += 1
            if estado(ruta.replace("https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile", base)) != 200:
                rotas += 1
        for parte in json.loads((v1 / "partitions" / f"{objeto['id']}.json").read_text(encoding="utf-8"))["particiones"]:
            revisadas += 1
            if estado(f"{base}/{parte['archivo']}") != 200:
                rotas += 1
    anotar("1d.1 rutas", rotas == 0, f"{revisadas} rutas por HTTP, {rotas} × 404 ({time.time() - t0:.1f} s)")

    # --- 1d.2 · esquema declarado = esquema real ----------------------------
    con = duckdb.connect()
    malas = []
    vacias = []
    for objeto in objetos:
        documento = json.loads((v1 / "schema" / f"{objeto['id']}.json").read_text(encoding="utf-8"))
        partes = json.loads((v1 / "partitions" / f"{objeto['id']}.json").read_text(encoding="utf-8"))["particiones"]
        if not partes:
            continue
        real = {r[0]: r[1] for r in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{raiz / partes[0]['archivo']}')").fetchall()}
        declarado = {c["nombre"]: c["tipo"] for c in documento["columnas"]}
        for columna, tipo in declarado.items():
            obtenido = real.get(columna)
            if obtenido == tipo:
                continue
            clave = f"{objeto['id']}.{columna}"
            if clave in COLUMNAS_VACIAS_CONOCIDAS and obtenido == '"NULL"':
                vacias.append(clave)
                continue
            malas.append(f"{clave}: declara {tipo}, la base dice {obtenido}")
        for columna in sorted(set(real) - set(declarado)):
            malas.append(f"{objeto['id']}.{columna}: está en la base y no en el esquema")
    total_columnas = sum(
        len(json.loads((v1 / "schema" / f"{o['id']}.json").read_text(encoding="utf-8"))["columnas"])
        for o in objetos)
    anotar("1d.2 esquema", not malas,
           f"{total_columnas} columnas comparadas con DESCRIBE"
           + (f" · {len(malas)} discrepancias" if malas else ""))
    for m in malas[:5]:
        avisos.append(f"1d.2 · {m}")
    if vacias:
        avisos.append(f"1d.2 · {len(vacias)} columnas declaradas sin un solo valor "
                      f"(toleradas por estar declaradas): {', '.join(sorted(vacias))}")

    # --- 1d.3 · views.sql ---------------------------------------------------
    with urllib.request.urlopen(f"{base}/api/v1/views.sql", timeout=30) as r:
        ddl = r.read().decode("utf-8")
    local = ddl.replace("https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile",
                        str(raiz.resolve()))
    con.execute(local)
    creadas = {f[0] for f in con.execute(
        "SELECT view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
    esperadas = {o["id"] for o in objetos if o["particiones"]}
    esperadas |= {a for o in objetos for a in (o.get("aliases") or [])}
    vacios = [o for o in objetos if not o["particiones"]]
    comentados = [o["id"] for o in vacios if o["id"] in ddl]
    ok_views = creadas == esperadas and len(comentados) == len(vacios) and not (set(comentados) & creadas)
    anotar("1d.3 views.sql", ok_views,
           f"{len(creadas)} vistas creadas, {len(vacios)} objetos vacíos sin vista y con su motivo escrito"
           if ok_views else f"{len(creadas)} vs {len(esperadas)} esperadas; vacíos comentados: {len(comentados)}/{len(vacios)}")

    # --- 1d.4 · consultas publicadas ---------------------------------------
    consultas = json.loads((v1 / "queries.json").read_text(encoding="utf-8"))["consultas"]
    vacias_declaradas = {o["id"] for o in vacios}
    fallidas = []
    sin_filas = []
    for consulta in consultas:
        try:
            filas = con.execute(consulta["sql"]).fetchall()
        except Exception as exc:  # noqa: BLE001
            fallidas.append(f"{consulta['id']}: {str(exc).splitlines()[0][:70]}")
            continue
        if not filas and not set(consulta["espera"]["tablas"]) <= vacias_declaradas:
            sin_filas.append(consulta["id"])
    anotar("1d.4 consultas", not fallidas and not sin_filas,
           f"{len(consultas)} consultas ejecutadas, {len(fallidas)} con error y {len(sin_filas)} vacías sin motivo"
           if fallidas or sin_filas else f"las {len(consultas)} consultas corren y devuelven filas")
    for f in (fallidas + sin_filas)[:5]:
        avisos.append(f"1d.4 · {f}")

    # --- 1d.5 · los ejemplos del README ------------------------------------
    sql_cruce = """
    WITH bancos AS (SELECT rut, razon_social FROM bancos_lista_entidades),
    seguros AS (SELECT nro_rut AS rut, count(DISTINCT rut_aseguradora) AS aseguradoras
                FROM seguros_renta_fija
                WHERE periodo = (SELECT max(periodo) FROM seguros_renta_fija) GROUP BY 1),
    fondos AS (SELECT rut_emisor AS rut, count(DISTINCT run_fondo) AS fondos_mutuos
               FROM ffmm_cartera_nacional
               WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional) GROUP BY 1)
    SELECT b.razon_social
    FROM bancos b JOIN seguros s USING (rut) JOIN fondos f USING (rut)
    """
    emisores = {f[0] for f in con.execute(sql_cruce).fetchall()}
    bancos = {f[0] for f in con.execute("SELECT razon_social FROM bancos_lista_entidades").fetchall()}
    fuera = emisores - bancos
    anotar("1d.5 README · cruce", bool(emisores) and not fuera,
           f"{len(emisores)} emisores, todos del catálogo de bancos" if not fuera
           else f"{len(fuera)} emisores ajenos: {sorted(fuera)[:3]}")

    top = [f[0] for f in con.execute(f"""
        SELECT pais_emisor, count(*) AS posiciones
        FROM ffmm_cartera_extranjera WHERE periodo = '{PERIODO_HISTORICO}'
        GROUP BY 1 ORDER BY posiciones DESC, pais_emisor LIMIT 5
    """).fetchall()]
    anotar(f"1d.5 README · {PERIODO_HISTORICO}", set(top) == set(TOP5_HISTORICO),
           f"top 5 del período fijado: {top}" if set(top) == set(TOP5_HISTORICO)
           else f"top 5 {top} ≠ esperado {TOP5_HISTORICO}")

    # --- 1d.6 · bytes y sha256 ---------------------------------------------
    declarados = []
    for objeto in objetos:
        for parte in json.loads((v1 / "partitions" / f"{objeto['id']}.json").read_text(encoding="utf-8"))["particiones"]:
            declarados.append((objeto["id"], parte))
    discrepancias = []
    for identificador, parte in declarados:
        ruta = raiz / parte["archivo"]
        if not ruta.exists():
            discrepancias.append(f"{identificador}: falta {parte['archivo']}")
        elif ruta.stat().st_size != parte["bytes"] or sha256(ruta) != parte["sha256"]:
            discrepancias.append(f"{identificador}: {ruta.name} no coincide con lo declarado")
    # Una descarga real por HTTP: los bytes servidos son los anunciados.
    _, muestra = declarados[0]
    with urllib.request.urlopen(f"{base}/{muestra['archivo']}", timeout=120) as r:
        servido = r.read()
    if hashlib.sha256(servido).hexdigest() != muestra["sha256"]:
        discrepancias.append(f"{muestra['archivo']}: lo servido por HTTP no coincide con su SHA-256")
    anotar("1d.6 bytes y sha256", not discrepancias,
           f"{len(declarados)} archivos verificados y 1 descargado por HTTP" if not discrepancias
           else f"{len(discrepancias)} discrepancias")
    for d in discrepancias[:5]:
        avisos.append(f"1d.6 · {d}")

    # --- 1d.7 · cobertura cruzada ------------------------------------------
    # El manifiesto declara 89 filas; el catálogo, 672 archivos en 728
    # particiones. La correspondencia no es por nombre sino por archivo: quien
    # produce `outputs/…/x.parquet` es la fila del manifiesto que lo apunta (o
    # toda su carpeta, cuando el manifiesto apunta a un `manifest.json`).
    from pipelines.api.vistas import vistas_semanticas

    ids = {o["id"] for o in objetos}
    estado_objeto = {o["id"]: o["estado"] for o in objetos}
    filas_manifiesto = json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))["tables"]
    cobertura = []
    for fila in filas_manifiesto:
        archivo = fila["file_parquet"]
        prefijo = os.path.dirname(archivo) + "/" if archivo.endswith("manifest.json") else archivo
        cobertura.append((fila["id"], prefijo))

    def quien_lo_produce(ruta: str) -> list[str]:
        return [i for i, prefijo in cobertura
                if ruta == prefijo or (prefijo.endswith("/") and ruta.startswith(prefijo))]

    archivos = [(o["id"], p["archivo"]) for o in objetos
                for p in json.loads((v1 / "partitions" / f"{o['id']}.json").read_text(encoding="utf-8"))["particiones"]]
    # Los dos objetos de banca salen del dataset CMF, cuya fila del manifiesto
    # apunta acertadamente al maestro de entidades y no a las líneas.
    derivados_banca = {o["id"] for o in objetos if o.get("deriva_de") == "bancos_cmf_lineas"}
    sin_fila = [(i, a) for i, a in archivos if not quien_lo_produce(a) and i not in derivados_banca]
    cubiertas_banca = sum(1 for i, a in archivos if i in derivados_banca and not quien_lo_produce(a))

    sin_datos = []
    for identificador, prefijo in cobertura:
        if any(a == prefijo or (prefijo.endswith("/") and a.startswith(prefijo)) for _, a in archivos):
            continue
        if estado_objeto.get(identificador) != "vacio":  # los 4 vacíos declaran que lo están
            sin_datos.append(identificador)

    semantica = {v["name"] for v in vistas_semanticas()}
    fuera_de_contrato = semantica - ids
    ok = not sin_fila and not sin_datos and not fuera_de_contrato
    anotar("1d.7 cobertura", ok,
           f"{len(archivos)} archivos y {len(cobertura)} filas del manifiesto encajan con los {len(ids)} objetos "
           f"({cubiertas_banca} de banca vía bancos_cmf_lineas, 4 objetos vacíos declarados)"
           if ok else f"{len(sin_fila)} archivos sin fila, {len(sin_datos)} filas sin datos, "
                      f"{len(fuera_de_contrato)} vistas fuera del contrato")
    for identificador, archivo in sin_fila[:3]:
        avisos.append(f"1d.7 · {archivo} ({identificador}) no lo declara ninguna fila del manifiesto")
    for identificador in sin_datos[:3]:
        avisos.append(f"1d.7 · el manifiesto declara {identificador} y no hay archivos publicados")
    for nombre in sorted(fuera_de_contrato)[:3]:
        avisos.append(f"1d.7 · la vista semántica {nombre} no está en el contrato")

    con.close()
    return checks, avisos


def copia_con_defectos(destino: Path) -> Path:
    """Copia `docs/` dejando los Parquet enlazados y rompe dos cosas a propósito."""
    destino.mkdir(parents=True, exist_ok=True)
    for entrada in DOCS.iterdir():
        if entrada.name == "api":
            continue
        (destino / entrada.name).symlink_to(entrada.resolve(), target_is_directory=entrada.is_dir())
    (destino / "api").mkdir()
    for entrada in (DOCS / "api").iterdir():
        if entrada.name == "v1":
            shutil.copytree(entrada, destino / "api" / "v1")
        else:
            (destino / "api" / entrada.name).symlink_to(entrada.resolve(), target_is_directory=entrada.is_dir())

    # a) una columna renombrada en el esquema declarado
    esquema = destino / "api" / "v1" / "schema" / "bancos_balance.json"
    documento = json.loads(esquema.read_text(encoding="utf-8"))
    documento["columnas"][3]["nombre"] = "codigo_institucion_renombrado"
    esquema.write_text(json.dumps(documento, ensure_ascii=False, indent=1), encoding="utf-8")
    # b) un SHA-256 que no es el del archivo
    particiones = destino / "api" / "v1" / "partitions" / "afp_lista_entidades.json"
    documento = json.loads(particiones.read_text(encoding="utf-8"))
    documento["particiones"][0]["sha256"] = "0" * 64
    particiones.write_text(json.dumps(documento, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


def correr(raiz: Path, etiqueta: str) -> tuple[int, list[tuple[str, bool, str]], list[str]]:
    servidor = Servidor(raiz)
    try:
        checks, avisos = ejecutar(raiz, servidor.base)
    finally:
        servidor.cerrar()
    fallos = [c for c in checks if not c[1]]
    return len(fallos), checks, avisos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 si algo falla")
    ap.add_argument("--autoprueba", action="store_true", help="comprueba además que el test falla con defectos")
    args = ap.parse_args()

    lineas: list[str] = [f"# Test de contrato · {time.strftime('%Y-%m-%dT%H:%M:%S')}", ""]
    t0 = time.time()
    fallos, checks, avisos = correr(DOCS, "publicado")
    for codigo, ok, detalle in checks:
        texto = f"{'OK   ' if ok else 'FALLA'} {codigo} · {detalle}"
        print(texto)
        lineas.append(texto)
    for aviso in avisos:
        print(f"AVISO {aviso}")
        lineas.append(f"AVISO {aviso}")

    if args.autoprueba:
        print()
        temporal = Path(tempfile.mkdtemp(prefix="sif-contrato-roto-"))
        try:
            rota = copia_con_defectos(temporal / "docs")
            fallos_rota, checks_rota, _ = correr(rota, "rota")
            detectadas = {c for c, ok, _ in checks_rota if not ok}
            esperadas = {"1d.2 esquema", "1d.6 bytes y sha256"}
            ok = fallos_rota > 0 and esperadas <= detectadas
            texto = (f"{'OK   ' if ok else 'FALLA'} autoprueba · con una columna renombrada y un SHA-256 "
                     f"alterado, el test detecta {sorted(detectadas)}")
            print(texto)
            lineas.append(texto)
            fallos += 0 if ok else 1
        finally:
            shutil.rmtree(temporal, ignore_errors=True)

    duracion = time.time() - t0
    lineas.append("")
    lineas.append(f"Duración: {duracion:.1f} s · comprobaciones: {len(checks)} · fallos: {len([c for c in checks if not c[1]])}")
    lineas.append("TEST DE CONTRATO: " + ("lo publicado cumple lo que promete" if not fallos
                                         else f"{fallos} comprobación(es) fallaron"))
    print(f"\nDuración: {duracion:.1f} s")
    print(lineas[-1])
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia: {LOG.relative_to(RAIZ)}")
    return 1 if (fallos and args.check) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # el CI necesita una línea, no un traceback remoto
        print(f"[FALLA] excepción: {type(exc).__name__}: {exc}")
        raise SystemExit(1)
