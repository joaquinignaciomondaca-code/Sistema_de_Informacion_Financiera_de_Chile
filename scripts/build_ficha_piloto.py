#!/usr/bin/env python3
"""Construye una ficha técnica estática piloto desde el contrato de CCAF.

La ruta usa referencias relativas para que funcione tanto bajo el prefijo de
GitHub Pages como en un hosting con `docs/` como raíz, sin elegir aún un dominio
canónico. No contiene JavaScript: los metadatos esenciales son HTML desde la
primera respuesta.

Uso:
    python scripts/build_ficha_piloto.py
    python scripts/build_ficha_piloto.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FICHA_REL = Path("datos/ccaf_lista_entidades/index.html")
FICHA = DOCS / FICHA_REL
ID_API = "ccaf_lista_entidades"
ID_MANIFIESTO = "ccaf_maestro"
CONSULTA = (
    "SELECT rut_completo, razon_social, estado_vigencia "
    f"FROM {ID_API} ORDER BY razon_social;"
)


def leer_json(ruta: Path) -> dict[str, Any]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"No se pudo leer {ruta.relative_to(ROOT)}: {exc}") from exc


def esc(valor: Any) -> str:
    return html.escape(str(valor if valor is not None else ""), quote=True)


def numero(valor: int) -> str:
    return f"{int(valor):,}".replace(",", ".")


def enlace_relativo(ruta_doc: str) -> str:
    destino = DOCS / ruta_doc
    if not destino.is_file():
        raise SystemExit(f"No existe el destino de la ficha: {destino.relative_to(ROOT)}")
    return os.path.relpath(destino, FICHA.parent).replace(os.sep, "/")


def construir() -> str:
    catalogo = leer_json(DOCS / "api" / "v2" / "catalog.json")
    paquete = leer_json(DOCS / "api" / "v2" / "datapackage.json")
    manifiesto = leer_json(ROOT / "data_manifest.json")
    version_contrato = str(catalogo.get("version") or "")
    release = str(catalogo.get("data_release") or "")
    if not version_contrato or paquete.get("version") != version_contrato:
        raise SystemExit("La versión del catálogo y del Data Package no coincide")
    if not release:
        raise SystemExit("El catálogo no declara data_release para identificar esta publicación")
    objetos = {o.get("id"): o for o in catalogo.get("objetos", [])}
    objeto = objetos.get(ID_API)
    if not objeto:
        raise SystemExit(f"Falta {ID_API} en catalog.json")

    tabla = next((t for t in manifiesto.get("tables", []) if t.get("id") == ID_MANIFIESTO), None)
    if not tabla:
        raise SystemExit(f"Falta {ID_MANIFIESTO} en data_manifest.json")
    meta = tabla.get("metadatos") or {}
    procedencia = meta.get("procedencia")
    if not procedencia or procedencia != objeto.get("procedencia"):
        raise SystemExit("La procedencia editorial/directa difiere entre manifiesto y catálogo API")

    ruta_esquema = DOCS / "api" / "v2" / "schema" / f"{ID_API}.json"
    ruta_particiones = DOCS / "api" / "v2" / "partitions" / f"{ID_API}.json"
    esquema = leer_json(ruta_esquema)
    descriptor_particiones = leer_json(ruta_particiones)
    if descriptor_particiones.get("id") != ID_API:
        raise SystemExit("El descriptor de particiones tiene un ID inesperado")
    partes = descriptor_particiones.get("particiones") or []
    recurso = next((r for r in paquete.get("resources", []) if r.get("name") == ID_API), None)
    if not recurso or (recurso.get("sif") or {}).get("manifest_id") != ID_MANIFIESTO:
        raise SystemExit("El Data Package no enlaza el recurso con el manifest CCAF esperado")
    if (recurso.get("sif") or {}).get("procedencia") != procedencia:
        raise SystemExit("La procedencia del Data Package difiere del catálogo API")
    if not partes or len(partes) != int(objeto.get("particiones") or 0):
        raise SystemExit("El número de particiones de la ficha no coincide con catalog.json")
    if len(partes) != 1:
        raise SystemExit("La ficha piloto ofrece una descarga directa única; revisar si el objeto pasa a varias particiones")
    total_partes = descriptor_particiones.get("total") or {}
    if sum(int(p.get("bytes") or 0) for p in partes) != int(objeto.get("bytes") or 0):
        raise SystemExit("Los bytes de particiones no coinciden con catalog.json")
    if int(total_partes.get("bytes") or 0) != int(objeto.get("bytes") or 0):
        raise SystemExit("Los bytes totales del descriptor de particiones no coinciden con catalog.json")
    if int(total_partes.get("filas") or 0) != int(objeto.get("filas") or 0):
        raise SystemExit("Las filas declaradas en particiones no coinciden con catalog.json")
    if int(total_partes.get("archivos") or 0) != len(partes):
        raise SystemExit("El total de archivos del descriptor de particiones es inconsistente")
    if esquema.get("primaryKey") != objeto.get("primaryKey"):
        raise SystemExit("La clave primaria de la ficha no coincide con el esquema del API")

    # Verifica que la cifra de bytes y la huella del contrato describan el mismo
    # archivo físico antes de enlazar una descarga directa.
    parte = partes[0]
    archivo = str(parte.get("archivo", ""))
    ruta_fisica = DOCS / archivo
    if not archivo.startswith("outputs/") or not ruta_fisica.is_file():
        raise SystemExit(f"La partición de descarga no existe bajo docs/: {archivo}")
    contenido = ruta_fisica.read_bytes()
    if len(contenido) != int(parte.get("bytes") or 0):
        raise SystemExit("El tamaño físico no coincide con la partición publicada")
    if hashlib.sha256(contenido).hexdigest() != parte.get("sha256"):
        raise SystemExit("El SHA-256 físico no coincide con la partición publicada")

    rutas = {
        "descarga": enlace_relativo(archivo),
        "esquema": enlace_relativo(f"api/v2/schema/{ID_API}.json"),
        "particiones": enlace_relativo(f"api/v2/partitions/{ID_API}.json"),
        "datapackage": enlace_relativo("api/v2/datapackage.json"),
        "aplicacion": enlace_relativo("index.html"),
    }
    terminos = str(objeto.get("url_terminos") or "")
    if not terminos.startswith("https://"):
        raise SystemExit("Falta una URL HTTPS de condiciones de la fuente de atribución")

    periodo = esc(objeto.get("corte") or "No declarado")
    frescura = esc(objeto.get("frescura") or "No declarada")
    fecha_extraccion = esc(meta.get("fecha_extraccion") or "No declarada")
    unidad = esc(meta.get("unidad") or "No declarada")
    cobertura = esc(meta.get("cobertura") or "No declarada")
    sector = esc(tabla.get("sector_label") or objeto.get("sector") or "No declarado")
    descripcion = esc(objeto.get("descripcion") or "Descripción no declarada.")
    titulo = f"Lista de entidades de {sector}"
    id_visible = esc(objeto["id"])
    version_visible = esc(version_contrato)
    release_visible = esc(release)
    condiciones = procedencia.get("condiciones_reutilizacion") or []
    etiquetas_estado = {
        "verificada": "Verificada",
        "pendiente_verificacion": "Pendiente de verificación",
    }
    filas_condiciones = "\n".join(
        "<tr>"
        f"<th scope=\"row\">{esc(f.get('institucion'))}</th>"
        f"<td><span class=\"estado\">{esc(etiquetas_estado.get(f.get('estado'), f.get('estado')))}</span></td>"
        f"<td>{esc(f.get('alcance'))}</td>"
        "</tr>"
        for f in condiciones
    )
    if not filas_condiciones:
        raise SystemExit("Faltan estados de reutilización por fuente en la procedencia")

    fuentes_directas = procedencia.get("fuentes_directas_actuales") or []
    filas_directas = "\n".join(
        "<tr>"
        f"<th scope=\"row\">{esc(f.get('institucion'))}</th>"
        f"<td>{esc(f.get('recurso'))}</td>"
        f"<td>{esc(f.get('alcance'))}</td>"
        "</tr>"
        for f in fuentes_directas
    )
    base_editorial = (procedencia.get("procedencia_editorial") or {}).get("universo_inicial") or []
    filas_editoriales = "\n".join(
        "<tr>"
        f"<th scope=\"row\">{esc(f.get('institucion'))}</th>"
        f"<td>{esc(f.get('recurso'))}</td>"
        "</tr>"
        for f in base_editorial
    )
    if not filas_directas or not filas_editoriales:
        raise SystemExit("La procedencia requiere fuentes directas y editoriales")

    columnas = esquema.get("columnas") or []
    filas_columnas = "\n".join(
        "<tr>"
        f"<th scope=\"row\"><code>{esc(c.get('nombre'))}</code></th>"
        f"<td><code>{esc(c.get('tipo'))}</code></td>"
        f"<td>{esc(c.get('significado') or 'Sin significado editorial declarado.')}</td>"
        "</tr>"
        for c in columnas
    )
    pk = esquema.get("primaryKey") or []
    pk_texto = ", ".join(pk) if pk else "No declarada"
    terminos_link = esc(terminos)
    ruta_descarga = esc(rutas["descarga"])
    ruta_esquema = esc(rutas["esquema"])
    ruta_particiones = esc(rutas["particiones"])
    ruta_paquete = esc(rutas["datapackage"])
    ruta_app = esc(rutas["aplicacion"])
    sql_hash = quote(CONSULTA, safe="")
    filas = numero(objeto.get("filas") or 0)
    bytes_archivo = numero(objeto.get("bytes") or 0)
    archivos = numero(len(partes))
    columnas_count = numero(len(columnas))
    sha = esc(parte.get("sha256") or "")
    atribucion = esc(objeto.get("atribucion") or "")
    fuente = esc(objeto.get("fuente") or "No declarada")
    primary = esc(pk_texto)

    documento = f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <meta name="description" content="Ficha piloto de {esc(titulo)}. Metadatos, procedencia, condiciones declaradas y acceso a los archivos publicados.">
  <title>{esc(titulo)} · SIF Chile</title>
  <style>
    :root {{ color-scheme: light; --tinta:#17212b; --secundario:#4b5967; --fondo:#f4f6f8; --papel:#fff; --borde:#cbd3db; --enlace:#075a84; --aviso:#754700; --aviso-fondo:#fff4d6; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--fondo); color:var(--tinta); font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
    a {{ color:var(--enlace); text-underline-offset:.18em; }}
    a:focus-visible, summary:focus-visible {{ outline:3px solid #a44900; outline-offset:3px; border-radius:2px; }}
    .skip-link {{ position:fixed; inset-block-start:.75rem; inset-inline-start:.75rem; z-index:10; transform:translateY(calc(-100% - 1rem)); padding:.55rem .8rem; border:2px solid #a44900; background:var(--papel); color:var(--enlace); font-weight:650; }}
    .skip-link:focus {{ transform:translateY(0); }}
    .marco {{ width:min(100% - 2rem, 72rem); margin-inline:auto; }}
    header {{ padding:1.25rem 0; border-bottom:1px solid var(--borde); background:var(--papel); }}
    nav {{ font-size:.9rem; }}
    main {{ padding-block:2rem 4rem; }}
    .sobrelinea {{ margin:.2rem 0; color:var(--secundario); font-size:.95rem; }}
    h1 {{ margin:.3rem 0 .5rem; font-size:clamp(1.8rem,4vw,2.6rem); line-height:1.15; }}
    h2 {{ margin:2rem 0 .6rem; font-size:1.35rem; line-height:1.25; }}
    h3 {{ margin:1.25rem 0 .4rem; font-size:1.05rem; }}
    p {{ max-width:76ch; }}
    code {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; overflow-wrap:anywhere; }}
    .id {{ display:inline-block; padding:.15rem .45rem; background:#e8edf1; border-radius:.25rem; }}
    .resumen {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(9rem,1fr)); gap:.7rem 1.5rem; margin:1.4rem 0; padding:1rem 0; border-block:1px solid var(--borde); }}
    .resumen div {{ min-width:0; }}
    dt {{ color:var(--secundario); font-size:.88rem; }}
    dd {{ margin:.1rem 0 0; font-weight:650; }}
    .acciones {{ display:flex; flex-wrap:wrap; gap:.65rem; margin:1.25rem 0; }}
    .boton {{ display:inline-block; min-height:2.75rem; padding:.6rem .9rem; border:1px solid var(--enlace); border-radius:.35rem; background:var(--enlace); color:#fff; font-weight:650; text-decoration:none; }}
    .boton.secundario {{ background:var(--papel); color:var(--enlace); }}
    .nota {{ padding:.85rem 1rem; border-left:4px solid #a46a00; background:var(--aviso-fondo); color:#3b2b12; }}
    .tabla-wrap {{ box-sizing:border-box; overflow-x:auto; border:1px solid var(--borde); background:var(--papel); padding:6px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ padding:.65rem .75rem; border-bottom:1px solid #dce2e7; text-align:left; vertical-align:top; }}
    thead th {{ background:#edf1f4; }}
    tbody th {{ font-weight:650; }}
    .estado {{ display:inline-block; padding:.1rem .4rem; border:1px solid #8b6a2c; border-radius:.25rem; font-size:.88rem; white-space:nowrap; }}
    details {{ margin-top:1.25rem; }}
    summary {{ cursor:pointer; font-weight:650; }}
    pre {{ max-width:100%; overflow:auto; padding:1rem; border:1px solid var(--borde); background:var(--papel); }}
    footer {{ padding:1.25rem 0 2rem; border-top:1px solid var(--borde); color:var(--secundario); font-size:.9rem; }}
    @media (max-width:38rem) {{ .marco {{ width:min(100% - 1.25rem,72rem); }} main {{ padding-top:1.35rem; }} th,td {{ padding:.55rem; }} .acciones {{ display:grid; }} .boton {{ text-align:center; }} }}
    @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto !important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Saltar al contenido principal</a>
  <header>
    <div class="marco"><nav aria-label="Navegación de la ficha"><a href="{ruta_app}">Volver al sitio SIF Chile</a> <span aria-hidden="true">›</span> Ficha piloto</nav></div>
  </header>
  <main class="marco" id="main-content" tabindex="-1">
    <p class="sobrelinea">{sector} · Ficha técnica piloto</p>
    <h1>{esc(titulo)}</h1>
    <p class="id">ID de API: <code>{id_visible}</code></p>
    <p>{descripcion}</p>

    <dl class="resumen">
      <div><dt>Registros</dt><dd>{filas}</dd></div>
      <div><dt>Archivos Parquet</dt><dd>{archivos}</dd></div>
      <div><dt>Tamaño publicado</dt><dd>{bytes_archivo} bytes</dd></div>
      <div><dt>Columnas</dt><dd>{columnas_count}</dd></div>
      <div><dt>Cobertura</dt><dd>{periodo}</dd></div>
      <div><dt>Extracción declarada</dt><dd>{fecha_extraccion}</dd></div>
      <div><dt>Versión API</dt><dd>{version_visible}</dd></div>
      <div><dt>Identificador de publicación</dt><dd><code>{release_visible}</code></dd></div>
      <div><dt>Unidad</dt><dd>{unidad}</dd></div>
      <div><dt>Clave primaria declarada</dt><dd><code>{primary}</code></dd></div>
    </dl>

    <div class="acciones" role="group" aria-label="Acciones disponibles">
      <a class="boton" href="{ruta_descarga}" download>Descargar Parquet</a>
      <a class="boton secundario" href="{ruta_esquema}">Ver esquema JSON</a>
      <a class="boton secundario" href="{ruta_particiones}">Ver rutas y hashes</a>
      <a class="boton secundario" href="{ruta_paquete}">Abrir Data Package</a>
    </div>
    <p class="sobrelinea">La fuente declara esta frescura: {frescura}. {cobertura}</p>

    <h2>Fuente y procedencia</h2>
    <p><strong>Atribución del contrato:</strong> {esc(fuente)}. {atribucion} <a href="{terminos_link}" target="_blank" rel="noopener noreferrer">Ver condiciones CMF</a>.</p>
    <h3>Entrada directa actual</h3>
    <div class="tabla-wrap"><table><thead><tr><th scope="col">Institución</th><th scope="col">Recurso</th><th scope="col">Alcance declarado</th></tr></thead><tbody>{filas_directas}</tbody></table></div>
    <h3>Procedencia editorial del universo inicial</h3>
    <div class="tabla-wrap"><table><thead><tr><th scope="col">Institución</th><th scope="col">Recurso de origen</th></tr></thead><tbody>{filas_editoriales}</tbody></table></div>
    <p>{esc((procedencia.get('procedencia_editorial') or {}).get('mantenimiento') or '')}</p>

    <h3>Condiciones de reutilización documentadas</h3>
    <div class="tabla-wrap"><table><thead><tr><th scope="col">Fuente</th><th scope="col">Estado</th><th scope="col">Alcance</th></tr></thead><tbody>{filas_condiciones}</tbody></table></div>
    <p class="nota"><strong>Pendiente:</strong> las condiciones de reutilización aplicables a la procedencia histórica SUSESO no se verificaron. La atribución CMF no resuelve ese punto; no se concluye aquí autorización ni prohibición.</p>

    <h2>Esquema y consulta</h2>
    <p>La tabla contiene {columnas_count} columnas; el esquema JSON enlazado arriba es la definición completa. La consulta se ejecuta en el navegador con el motor del sitio, no mediante SQL remoto.</p>
    <pre><code>{esc(CONSULTA)}</code></pre>
    <p><a href="{ruta_app}#sql={sql_hash}">Abrir esta consulta en el explorador; se ejecutará en tu navegador</a>.</p>
    <details>
      <summary>Ver las {columnas_count} columnas y sus definiciones</summary>
      <div class="tabla-wrap"><table><thead><tr><th scope="col">Columna</th><th scope="col">Tipo</th><th scope="col">Significado</th></tr></thead><tbody>{filas_columnas}</tbody></table></div>
    </details>

    <h2>Integridad de la descarga</h2>
    <p>SHA-256 de la partición publicada:</p>
    <pre><code>{sha}</code></pre>
    <p>El hash verifica estos bytes y el identificador de publicación sitúa el contrato; ninguno promete que exista un archivo histórico recuperable.</p>
  </main>
  <footer><div class="marco">Ficha piloto no indexable. La licencia MIT cubre el código, no los datos de terceros; consulta las condiciones por fuente antes de reutilizar.</div></footer>
</body>
</html>
'''
    if "<script" in documento.lower():
        raise SystemExit("La ficha debe entregar sus metadatos esenciales sin JavaScript")
    return documento


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="falla si la ficha generada está desactualizada")
    args = parser.parse_args()
    esperado = construir()
    if args.check:
        if not FICHA.is_file():
            print(f"FALTA: {FICHA.relative_to(ROOT)}; ejecuta scripts/build_ficha_piloto.py")
            return 1
        actual = FICHA.read_text(encoding="utf-8")
        if actual != esperado:
            print(f"ATRASADA: {FICHA.relative_to(ROOT)} no coincide con los metadatos vigentes")
            return 1
        print(f"FICHA PILOTO OK: {FICHA.relative_to(ROOT)} · {ID_API} · sin JavaScript · enlaces relativos")
        return 0
    FICHA.parent.mkdir(parents=True, exist_ok=True)
    FICHA.write_text(esperado, encoding="utf-8")
    print(f"Escrita: {FICHA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
