#!/usr/bin/env python3
"""Prueba en memoria la plantilla de ficha en casos representativos.

No crea rutas públicas: el único HTML persistido sigue siendo la ficha CCAF.
"""
from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, unquote
from unittest.mock import patch

import ficha_renderer
from ficha_renderer import DOCS, construir_ficha
from test_ficha_piloto_http import comprobar_accesibilidad_estatica

CANDIDATAS = (
    "seguros_renta_fija",
    "ffmm_cartera_nacional",
    "fi_cartera_nacional",
    "macro_uf",
    "bancos_balance",
    "patrimonios_separados_balance",
    "fi_bienes_raices",
    "seguros_bienes_raices_arriendo_morosidad",
)


class Recolector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.enlaces: list[str] = []
        self.descargas = 0
        self.href_descargas: list[str] = []
        self.scripts = 0
        self.h1 = 0
        self.th_sin_scope = 0
        self.viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.enlaces.append(str(a["href"]))
            if "download" in a:
                self.descargas += 1
                self.href_descargas.append(str(a["href"]))
        if tag == "script":
            self.scripts += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "th" and a.get("scope") not in {"col", "row", "colgroup", "rowgroup"}:
            self.th_sin_scope += 1
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True


def verificar_recurso_datapackage(objeto: dict, recursos: dict[str, dict]) -> dict | None:
    id_api = str(objeto["id"])
    recurso = recursos.get(id_api)
    descriptor = json.loads((DOCS / "api" / "v2" / "partitions" / f"{id_api}.json").read_text(encoding="utf-8"))
    partes = descriptor.get("particiones") or []
    total = descriptor.get("total") or {}
    if len(partes) != int(objeto.get("particiones") or 0):
        raise SystemExit(f"Conteo de particiones catálogo/descriptor difiere para {id_api}")
    if (int(objeto.get("filas") or 0), int(objeto.get("bytes") or 0)) != (int(total.get("filas") or 0), int(total.get("bytes") or 0)):
        raise SystemExit(f"Filas/bytes catálogo/descriptor difieren para {id_api}")
    if recurso is None:
        if partes or int(objeto.get("filas") or 0) or int(objeto.get("bytes") or 0):
            raise SystemExit(f"{id_api} tiene datos declarados pero no recurso Data Package")
        return None

    esperados = [str(p.get("archivo") or "") for p in partes]
    rutas = recurso.get("path") or []
    if isinstance(rutas, str):
        rutas = [rutas]
    publicados = []
    for ruta in rutas:
        path = urlsplit(str(ruta)).path
        marcador = "/outputs/"
        if marcador not in path:
            raise SystemExit(f"Ruta Data Package fuera de outputs/ para {id_api}: {ruta}")
        publicados.append(path.split(marcador, 1)[1])
        publicados[-1] = "outputs/" + publicados[-1]
    if publicados != esperados:
        raise SystemExit(f"Particiones Data Package/catálogo difieren para {id_api}")
    bytes_descriptor = sum(int(p.get("bytes") or 0) for p in partes)
    filas_descriptor = int((descriptor.get("total") or {}).get("filas") or 0)
    sif = recurso.get("sif") or {}
    partes_sif = sif.get("particiones") or []
    firmas_descriptor = [
        (str(p.get("archivo") or ""), int(p.get("bytes") or 0), str(p.get("sha256") or ""))
        for p in partes
    ]
    firmas_sif = []
    filas_sif_partes = 0
    for parte in partes_sif:
        path = urlsplit(str(parte.get("path") or "")).path
        if "/outputs/" not in path:
            raise SystemExit(f"Ruta sif.particiones fuera de outputs/ para {id_api}")
        archivo = "outputs/" + path.split("/outputs/", 1)[1]
        firmas_sif.append((archivo, int(parte.get("bytes") or 0), str(parte.get("sha256") or "")))
        filas_sif_partes += int(parte.get("filas") or 0)
    if (int(recurso.get("bytes") or 0) != bytes_descriptor
            or int(sif.get("filas") or 0) != filas_descriptor
            or filas_sif_partes != filas_descriptor):
        raise SystemExit(f"Filas/bytes Data Package/particiones difieren para {id_api}")
    if firmas_sif != firmas_descriptor:
        raise SystemExit(f"Archivos, filas, bytes o SHA-256 de Data Package/particiones difieren para {id_api}")
    if recurso.get("format") != "parquet" or sif.get("sql_view") != id_api:
        raise SystemExit(f"Formato o vista canónica Data Package incorrectos para {id_api}")
    return recurso


def verificar_campos_ficha(id_api: str, documento: str, objeto: dict, tablas: dict, recurso: dict | None) -> None:
    manifest_id = str(((recurso or {}).get("sif") or {}).get("manifest_id") or id_api)
    metadatos = (tablas.get(manifest_id) or {}).get("metadatos") or {}
    if id_api not in documento or "Esquema" not in documento or "Versión API" not in documento:
        raise SystemExit(f"La ficha {id_api} debe conservar ID, esquema y versión API")
    fuente = str(objeto.get("fuente") or "")
    if fuente and ("Fuente declarada" not in documento or escape(fuente) not in documento):
        raise SystemExit(f"La ficha {id_api} debe exponer su fuente declarada")
    periodo = str(objeto.get("corte") or metadatos.get("cobertura") or "")
    if periodo and ("Cobertura declarada" not in documento or escape(periodo) not in documento):
        raise SystemExit(f"La ficha {id_api} debe exponer el período declarado, sin sustituirlo")
    unidad = str(metadatos.get("unidad") or "")
    if unidad and ("<dt>Unidad</dt>" not in documento or escape(unidad) not in documento):
        raise SystemExit(f"La ficha {id_api} debe mostrar la unidad existente")
    if not unidad and "<dt>Unidad</dt>" in documento:
        raise SystemExit(f"La ficha {id_api} no debe inventar una unidad ausente")
    if not objeto.get("primaryKey") and "No declarada" not in documento:
        raise SystemExit(f"La ficha {id_api} debe dejar explícita la ausencia de clave primaria")
    qa = str(metadatos.get("estado_qa") or "")
    if qa and ("Observación QA declarada" not in documento or escape(qa) not in documento):
        raise SystemExit(f"La ficha {id_api} debe mostrar su observación QA declarada")
    if not qa and "Observación QA declarada" in documento:
        raise SystemExit(f"La ficha {id_api} no debe inventar una observación QA")


def verificar_escape_html() -> None:
    carga_original = ficha_renderer._json

    def cargar_con_texto_hostil(path: Path) -> dict:
        documento = carga_original(path)
        if path == ficha_renderer.CATALOGO:
            objeto = next(o for o in documento["objetos"] if o.get("id") == "macro_uf")
            objeto["titulo"] = '<img src=x onerror="alert(1)">'
            objeto["descripcion"] = "Texto <script>alert(1)</script> & comillas \""
        return documento

    with patch.object(ficha_renderer, "_json", side_effect=cargar_con_texto_hostil), patch.object(
        ficha_renderer, "_labels_descargas", return_value={}
    ):
        documento = construir_ficha("macro_uf", verificar_hash=False)
    if '<script>alert(1)</script>' in documento or '<img src=x' in documento:
        raise SystemExit("El renderer no escapó metadatos HTML potencialmente hostiles")
    if "&lt;script&gt;alert(1)&lt;/script&gt; &amp;" not in documento or "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" not in documento:
        raise SystemExit("El escape HTML debe conservar el texto como literal visible")


def main() -> int:
    verificar_escape_html()
    paquete = json.loads((DOCS / "api" / "v2" / "datapackage.json").read_text(encoding="utf-8"))
    lista_recursos = paquete.get("resources", [])
    recursos = {r["name"]: r for r in lista_recursos}
    if len(recursos) != len(lista_recursos):
        raise SystemExit("El Data Package repite el nombre de un recurso")
    catalogo = json.loads((DOCS / "api" / "v2" / "catalog.json").read_text(encoding="utf-8"))
    objetos = catalogo.get("objetos", [])
    ids_con_archivos = {o["id"] for o in objetos if int(o.get("particiones") or 0) > 0}
    if set(recursos) != ids_con_archivos:
        raise SystemExit("Los recursos Data Package no coinciden con los objetos del catálogo que tienen particiones")
    for objeto in objetos:
        verificar_recurso_datapackage(objeto, recursos)
    catalogo_por_id = {o["id"]: o for o in objetos}
    manifiesto = json.loads((ficha_renderer.MANIFIESTO).read_text(encoding="utf-8"))
    tablas = {t["id"]: t for t in manifiesto.get("tables", [])}
    descripciones = {r["name"]: str(r.get("description") or "") for r in lista_recursos}
    desc_balance = descripciones.get("bancos_balance", "")
    desc_resultados = descripciones.get("bancos_resultados", "")
    frase_compartida = "filas fuente de b1 consolidado, b2 individual y r1 consolidado"
    if ("sólo filas de los archivos b1 (consolidado) y b2 (individual); excluye r1" not in desc_balance.lower()
            or "sólo filas del archivo r1 (estado de resultados); excluye b1 y b2" not in desc_resultados.lower()
            or frase_compartida in desc_balance.lower() or frase_compartida in desc_resultados.lower()
            or desc_balance == desc_resultados):
        raise SystemExit("Las descripciones Data Package de balance B1/B2 y resultados R1 deben ser distintas y explícitas")

    try:
        construir_ficha("ccaf_lista_entidades")
    except SystemExit as error:
        if "procedencia estructurada y requiere su ficha especializada" not in str(error):
            raise
    else:
        raise SystemExit("El renderer genérico no debe simplificar la procedencia estructurada de CCAF")

    host = "https://preview.invalid"
    for id_api in CANDIDATAS:
        ruta_publica = DOCS / "datos" / id_api / "index.html"
        if ruta_publica.exists():
            raise SystemExit(f"No se debe crear/publicar una ficha candidata automáticamente: {ruta_publica}")
        documento = construir_ficha(id_api)
        verificar_campos_ficha(id_api, documento, catalogo_por_id[id_api], tablas, recursos.get(id_api))
        parser = Recolector()
        parser.feed(documento)
        if parser.scripts or parser.h1 != 1 or parser.th_sin_scope or not parser.viewport:
            raise SystemExit(f"Semántica o entrega estática inválida: {id_api}")
        if 'name="robots" content="noindex,follow"' not in documento:
            raise SystemExit(f"La ficha candidata {id_api} no está marcada noindex")
        if ("<dt>Versión API</dt>" not in documento
                or "<dt>Identificador de publicación</dt>" not in documento
                or "no garantizan recuperar versiones históricas" not in documento):
            raise SystemExit(f"La ficha {id_api} debe mostrar la edición y no prometer recuperación histórica")
        contraste_minimo = comprobar_accesibilidad_estatica(documento, parser)

        base = f"{host}/datos/{id_api}/"
        descriptor = json.loads((DOCS / "api" / "v2" / "partitions" / f"{id_api}.json").read_text(encoding="utf-8"))
        cantidad_particiones = len(descriptor.get("particiones") or [])
        hashes_html = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", documento)
        if len(hashes_html) != cantidad_particiones:
            raise SystemExit(f"La ficha {id_api} debe mostrar una huella por partición existente")

        locales = 0
        for href in parser.enlaces:
            url = urljoin(base, href)
            partes = urlsplit(url)
            if partes.netloc != urlsplit(host).netloc:
                continue
            destino = (DOCS / partes.path.lstrip("/")).resolve()
            if not destino.is_relative_to(DOCS.resolve()) or not destino.is_file():
                raise SystemExit(f"Enlace local sin destino para {id_api}: {href}")
            locales += 1

        if id_api == "ffmm_cartera_nacional":
            if (parser.descargas != 57 or "2.960 filas exactamente duplicadas" not in documento
                    or "No declarada" not in documento):
                raise SystemExit("La ficha FFMM debe listar sus 57 archivos, la observación QA y no inventar una clave primaria")
        elif id_api == "seguros_renta_fija" and parser.descargas != 22:
            raise SystemExit("La ficha de renta fija debe listar las 22 particiones")
        elif id_api == "fi_cartera_nacional" and parser.descargas != 26:
            raise SystemExit("La ficha FI debe listar sus 26 particiones")
        elif id_api == "bancos_balance":
            if parser.descargas != 56 or not all("balance_b1_b2" in href for href in parser.href_descargas):
                raise SystemExit("El balance debe ofrecer sus 56 archivos B1+B2, sin mezclar los archivos R1")
            if "excluye R1" not in documento or "exclusivamente B1/B2" not in documento:
                raise SystemExit("La descripción de balance debe declarar explícitamente su alcance B1+B2 y la exclusión de R1")
            consultas = [unquote(href.split("#sql=", 1)[1]) for href in parser.enlaces if "#sql=" in href]
            if consultas != ["SELECT * FROM bancos_balance LIMIT 20;"]:
                raise SystemExit("La consulta debe conservar el ID canónico de balance y no ofrecer resultados R1")
        elif id_api == "macro_uf":
            if parser.descargas != 1 or "<dt>Unidad</dt>" in documento:
                raise SystemExit("La ficha macro UF debe ofrecer su único Parquet y omitir la unidad no declarada")
        elif id_api == "patrimonios_separados_balance" and parser.descargas != 1:
            raise SystemExit("La ficha de archivo debe ofrecer su único Parquet")
        elif id_api == "fi_bienes_raices":
            if parser.descargas != 1 or "#sql=" in documento or "0 filas" not in documento or "no acredita que el período esté completo ni que no existan datos en la fuente" not in documento:
                raise SystemExit("El objeto FI vacío debe mostrar el archivo, omitir SQL y no declarar ausencia en fuente")
        elif id_api == "seguros_bienes_raices_arriendo_morosidad":
            if (parser.descargas or "#sql=" in documento or "Ver Data Package" in documento
                    or "<dt>Unidad</dt>" in documento or "Observación QA declarada" in documento):
                raise SystemExit("El objeto sin archivos no debe ofrecer acciones ni inventar unidad/QA ausentes")
            if "No hay archivos Parquet publicados" not in documento:
                raise SystemExit("La ausencia de archivos debe explicarse sin inventar acciones")

        if contraste_minimo < 4.5:
            raise SystemExit(f"Contraste de ficha candidata bajo el umbral: {id_api}")
        bytes_html = len(documento.encode("utf-8"))
        print(f"OK {id_api}: {parser.descargas} descargas · {locales} enlaces locales · HTML {bytes_html:,} bytes · contraste mínimo {contraste_minimo:.2f}:1 · sin JS")
    print(f"DATAPACKAGE: {len(recursos)} recursos con rutas, filas, bytes y SHA-256 reconciliados frente al descriptor; {len(objetos)} IDs revisados")
    print(f"FICHAS CANDIDATAS: {len(CANDIDATAS)} previsualizaciones en memoria + CCAF retenida en su renderer especializado; no se escribieron rutas adicionales")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
