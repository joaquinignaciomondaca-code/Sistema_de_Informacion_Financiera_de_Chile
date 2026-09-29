#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica el vocabulario canónico (docs/vocabulario.json) a la web.

Qué normaliza, en todos los archivos vivos de `docs/` y de `scripts/`:

  * Los identificadores de vista (`afp_maestro` → `afp_lista_entidades`), sin tocar
    nunca las rutas de archivos publicados (`outputs/.../afp_maestro_administradoras.parquet`).
  * El nombre visible de cada tabla (`bancos.lista_instituciones` → `bancos.lista_entidades`),
    en el explorador, el visor, el diccionario y el mapa relacional.
  * El nombre de cada sector, para que diga lo mismo en el árbol, el visor, el
    diccionario y la pestaña de descargas.
  * El bloque de alias SQL de duckdb_client.js (los nombres anteriores siguen
    funcionando en consultas guardadas, pero la interfaz sólo sugiere el canónico).

Uso:
    python3 scripts/normalizar_vocabulario.py           # aplica
    python3 scripts/normalizar_vocabulario.py --check   # comprueba sin escribir
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_PATH = os.path.join(ROOT, "docs", "vocabulario.json")

# Archivos con vocabulario visible. Las notas datadas (docs/notas/), los
# directorios de datos publicados y docs/vendor/ quedan fuera a propósito.
TARGETS = [
    "docs/index.html",
    "docs/js/sidebar.js",
    "docs/js/data_viewer.js",
    "docs/js/data_dictionary.js",
    "docs/js/erd_graph.js",
    "docs/js/duckdb_client.js",
    "docs/js/chat_terminal.js",
    "docs/js/downloads_panel.js",
    "docs/js/ux_shell.js",
    "scripts/audit_interfaz.py",
    "scripts/audit_interfaz_dom.js",
    "scripts/audit_navigation.py",
    "scripts/audit_web_full.py",
    "scripts/build_download_catalog.py",
    "README.md",
]


def read(rel: str) -> str:
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def write(rel: str, texto: str) -> None:
    with io.open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
        fh.write(texto)


def vocabulario() -> dict:
    with io.open(VOCAB_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ── Renombrado de identificadores ───────────────────────────────────────────────

def mapa_ids(vocab: dict) -> dict:
    """alias (y nombre canónico) → identificador canónico."""
    mapa = {}
    for tabla in vocab["tablas"]:
        mapa[tabla["id"]] = tabla["id"]
        for alias in tabla.get("alias", []):
            mapa[alias] = tabla["id"]
    return mapa


# Extensiones de archivos publicados: nunca se renombran.
EXTENSIONES = r"(?:parquet|json|csv|xlsx|zip|wasm|js|mjs|md|html)"


def patron_id(nombre: str) -> re.Pattern:
    """Identificador suelto: ni pegado a una ruta ni a otro identificador.

    - `outputs/pensiones/afp_maestro_administradoras.parquet` queda intacto (va tras «/»).
    - `cat_seguros_maestro` queda intacto (va tras «_»).
    - `DATA_BUNDLES.afp_maestro[0]` y «securitizadoras_maestro.rut» sí se renombran.
    """
    return re.compile(
        r"(?<![/\w-])" + re.escape(nombre) + r"(?!\w|\.(?:" + EXTENSIONES + r")\b)"
    )


def renombrar_ids(texto: str, mapa: dict, contador: dict) -> str:
    for viejo in sorted(mapa, key=len, reverse=True):
        nuevo = mapa[viejo]
        if viejo == nuevo:
            continue
        texto, n = patron_id(viejo).subn(nuevo, texto)
        if n:
            contador[viejo] = contador.get(viejo, 0) + n
    return texto


# ── Nombres visibles ────────────────────────────────────────────────────────────

def nombre_visible(vocab: dict, id_vista: str) -> str | None:
    for tabla in vocab["tablas"]:
        if tabla["id"] == id_vista:
            return tabla["nombre"]
    return None


def etiqueta_tipo(vocab: dict, id_vista: str) -> str | None:
    for tabla in vocab["tablas"]:
        if tabla["id"] == id_vista:
            return vocab["tipos"].get(tabla["tipo"], "")
    return None


def descripcion(vocab: dict, id_vista: str) -> str | None:
    for tabla in vocab["tablas"]:
        if tabla["id"] == id_vista:
            return tabla.get("descripcion")
    return None


def reescribir_entradas(texto: str, vocab: dict, contador: dict, con_campos_extra=False) -> str:
    """Pone el nombre canónico en cada entrada `{ id: "...", name: "..." }`.

    `con_campos_extra` agrega (o actualiza) `detalle` y `descripcion` en los
    catálogos del visor y del explorador.
    """
    patron = re.compile(r'(?P<pre>\bid:\s*"(?P<id>[a-z0-9_]+)"(?P<medio>[\s\S]{0,200}?)\bname:\s*")(?P<nombre>[^"]*)(?P<post>")')

    def reemplazo(match: re.Match) -> str:
        id_vista = match.group("id")
        canonico = nombre_visible(vocab, id_vista)
        if not canonico:
            return match.group(0)
        if canonico != match.group("nombre"):
            contador[f"nombre:{id_vista}"] = contador.get(f"nombre:{id_vista}", 0) + 1
        return match.group("pre") + canonico + match.group("post")

    texto = patron.sub(reemplazo, texto)

    if con_campos_extra:
        # `{ id: "...", name: "<canónico>" }` → agrega detalle y descripción si faltan.
        patron_corto = re.compile(r'\{\s*id:\s*"(?P<id>[a-z0-9_]+)"\s*,\s*name:\s*"[^"]+"\s*\}')

        def ampliar(match: re.Match) -> str:
            id_vista = match.group("id")
            tipo = etiqueta_tipo(vocab, id_vista)
            desc = descripcion(vocab, id_vista)
            if tipo is None:
                return match.group(0)
            contador[f"detalle:{id_vista}"] = contador.get(f"detalle:{id_vista}", 0) + 1
            return (
                f'{{ id: "{id_vista}", name: "{nombre_visible(vocab, id_vista)}", '
                f'detalle: "{tipo}", descripcion: "{desc}" }}'
            )

        texto = patron_corto.sub(ampliar, texto)
    return texto


def reescribir_sectores_por_bloque(texto: str, vocab: dict, patron_contenido: str, contador: dict) -> str:
    """Reemplaza la etiqueta de sector usando los ids de tabla que contiene el bloque."""
    sectores = {t["id"]: t["sector"] for t in vocab["tablas"]}

    def reemplazo(match: re.Match) -> str:
        bloque = match.group(0)
        ids = re.findall(r'\bid:\s*"([a-z0-9_]+)"', bloque)
        for id_vista in ids:
            sector = sectores.get(id_vista)
            if sector:
                etiqueta = vocab["sectores"][sector]
                nuevo, n = re.subn(r'(?P<pre>' + patron_contenido + r':\s*")[^"]*(")',
                                   lambda m: m.group("pre") + etiqueta + m.group(2), bloque, count=1)
                if n:
                    contador[f"sector:{sector}"] = contador.get(f"sector:{sector}", 0) + 1
                return nuevo
        return bloque

    return re.sub(r'\{\s*group:\s*"[\s\S]*?\n  \},', reemplazo, texto)


# Carpetas que agrupan varias tablas: su id es `cat_<prefijo>_<contenido>`.
# Las carpetas con una sola tabla usan directamente `cat_<tabla_id>`.
NODOS_MULTITABLA = {
    "c1835_seguros_cartera": "cat_seguros_cartera_1835",
    "c1835_seguros_derivados": "cat_seguros_derivados_1835",
    "c1333_ffmm_cartera": "cat_ffmm_cartera_1333",
    "c1333_ffmm": "cat_ffmm_derivados_1333",
    "fi_cartera": "cat_fi_cartera",
    "fi_derivados_pactos": "cat_fi_derivados_pactos",
    "circ_macro_series": "cat_macro_series",
}


# Declaración de un nodo del árbol: `id` seguido de su `type`.
NODO_DECL = re.compile(r'id: "(?P<id>[a-z0-9_]+)"[^\n]*\n?\s*type: "(?P<tipo>[a-z]+)"')


def nodos_arbol(texto: str, ids_vista: set) -> list:
    """Devuelve (inicio, fin, id, tipo, tablas) de cada nodo del explorador."""
    coincidencias = [m for m in NODO_DECL.finditer(texto) if m.group("id") not in ids_vista]
    nodos = []
    for i, marca in enumerate(coincidencias):
        fin = coincidencias[i + 1].start() if i + 1 < len(coincidencias) else len(texto)
        bloque = texto[marca.start():fin]
        tablas = [t for t in re.findall(r'id: "([a-z0-9_]+)"', bloque) if t in ids_vista]
        nodos.append((marca.start(), fin, marca.group("id"), marca.group("tipo"), tablas))
    return nodos


def id_de_nodo(id_viejo: str, tablas: list):
    """Id canónico: `cat_<tabla_id>` cuando la carpeta abre una sola tabla."""
    if len(set(tablas)) == 1:
        return "cat_" + tablas[0]
    return NODOS_MULTITABLA.get(id_viejo)


def normalizar_nodos_arbol(texto: str, vocab: dict, contador: dict) -> str:
    """Ids de nodo y etiquetas de carpeta del explorador.

    Cada carpeta se identifica con el id canónico de la tabla que abre
    (`cat_<tabla_id>`) y toda lista de entidades se rotula igual.
    """
    porid = {t["id"]: t for t in vocab["tablas"]}
    salida, ultimo = [], 0
    for inicio, fin, id_viejo, tipo_nodo, tablas in nodos_arbol(texto, set(porid)):
        if tipo_nodo != "circular" or not tablas:
            continue
        nuevo = texto[inicio:fin]
        id_nuevo = id_de_nodo(id_viejo, tablas)
        if id_nuevo and id_viejo != id_nuevo:
            nuevo = re.sub(r'(id: ")' + re.escape(id_viejo) + r'(")',
                           lambda m: m.group(1) + id_nuevo + m.group(2), nuevo, count=1)
            contador["nodo:" + id_viejo] = contador.get("nodo:" + id_viejo, 0) + 1
        tipo_tabla = porid[tablas[0]]["tipo"]
        if tipo_tabla.startswith("lista_entidades"):
            etiqueta = "Lista de Entidades" + (" · Registro" if tipo_tabla.endswith("_registro") else "")
            nuevo = re.sub(r'(\blabel:\s*")[^"]*(")', lambda m: m.group(1) + etiqueta + m.group(2), nuevo, count=1)
        salida.append(texto[ultimo:inicio])
        salida.append(nuevo)
        ultimo = fin
    salida.append(texto[ultimo:])
    return "".join(salida)


def normalizar_diccionario(texto: str, vocab: dict, contador: dict) -> str:
    """El diccionario mezcla entradas de una línea y de varias: se reescriben por id.

    En vez de intentar delimitar cada objeto, se toma la ventana que va de un `id`
    al siguiente y dentro de ella se corrigen `name`, `viewName` y `sectorLabel`.
    Así funciona igual con las entradas de una línea y con las que ocupan 30.
    """
    ids = {t["id"] for t in vocab["tablas"]}
    sectores = {t["id"]: t["sector"] for t in vocab["tablas"]}
    marcas = list(re.finditer(r'"?\bid"?\s*:\s*"([a-z0-9_]+)"', texto))
    salida = []
    cursor = 0

    for indice, marca in enumerate(marcas):
        id_vista = marca.group(1)
        if id_vista not in ids:
            continue
        fin_ventana = marcas[indice + 1].start() if indice + 1 < len(marcas) else len(texto)
        ventana = texto[marca.end():fin_ventana]
        canonico = nombre_visible(vocab, id_vista)
        ventana = fijar_clave(ventana, "name", canonico)
        ventana = fijar_clave(ventana, "viewName", id_vista)
        sector = sectores.get(id_vista)
        if sector:
            etiqueta = vocab["sectores"][sector]
            ventana = fijar_clave(ventana, "sectorLabel", etiqueta)
        cobertura = cobertura_de(vocab, id_vista)
        if cobertura and clave_objeto("registros").search(ventana):
            ventana = fijar_clave(ventana, "registros", cobertura)
        contador[f"diccionario:{id_vista}"] = contador.get(f"diccionario:{id_vista}", 0) + 1
        salida.append(texto[cursor:marca.end()])
        salida.append(ventana)
        cursor = fin_ventana

    salida.append(texto[cursor:])
    return "".join(salida)


def clave_objeto(nombre: str) -> re.Pattern:
    """Clave de objeto con o sin comillas: el diccionario mezcla `name:` y `"name":`."""
    return re.compile(r'(?P<pre>"?\b' + nombre + r'"?\s*:\s*")(?P<valor>[^"]*)(?P<post>")')


def fijar_clave(ventana: str, nombre: str, valor: str) -> str:
    return clave_objeto(nombre).sub(
        lambda m: m.group("pre") + valor + m.group("post"), ventana, count=1)



# Nombres visibles antiguos que pueden quedar en prosa (por ejemplo, dentro de la
# descripción de una columna). El diccionario los cita al explicar las llaves.
NOMBRES_ANTIGUOS = {
    "lista_administradoras": "lista_entidades",
    "lista_instituciones": "lista_entidades",
    "lista_emisiones": "lista_entidades",
    "registro_unico": "lista_entidades_registro",
    "cmf_balance_b1_b2": "balance",
    "cmf_resultados_r1": "resultados",
    "balance_serie_ifrs_cmf": "balance",
    "resultados_serie_ifrs_cmf": "resultados",
}


def limpiar_nombres_antiguos(texto: str, contador: dict) -> str:
    for viejo, nuevo in NOMBRES_ANTIGUOS.items():
        patron = re.compile(r"(?<![\w-])" + re.escape(viejo) + r"(?![\w])")
        texto, n = patron.subn(nuevo, texto)
        if n:
            contador[f"nombre_antiguo:{viejo}"] = contador.get(f"nombre_antiguo:{viejo}", 0) + n
    return texto


def cobertura_de(vocab: dict, id_vista: str) -> str | None:
    for tabla in vocab["tablas"]:
        if tabla["id"] == id_vista:
            return tabla.get("cobertura")
    return None


def normalizar_sidebar(texto: str, vocab: dict, contador: dict) -> str:
    """Nombres de tabla, cobertura y etiqueta de sector en el árbol del explorador."""
    texto = reescribir_entradas(texto, vocab, contador, con_campos_extra=False)

    # La línea de cobertura (`rows`) también es vocabulario: se toma del catálogo.
    def cobertura(match: re.Match) -> str:
        valor = cobertura_de(vocab, match.group("id"))
        if not valor:
            return match.group(0)
        contador[f"cobertura:{match.group('id')}"] = contador.get(f"cobertura:{match.group('id')}", 0) + 1
        return f'{match.group("pre")}{valor}{match.group("post")}'

    texto = re.sub(
        r'(?P<pre>id:\s*"(?P<id>[a-z0-9_]+)"[\s\S]{0,200}?\brows:\s*")(?P<valor>[^"]*)(?P<post>")',
        cobertura, texto)

    # Nodos de sector: `id: "sector_<clave>"` con su `label`.
    def nodo_sector(match: re.Match) -> str:
        clave = match.group("clave")
        if clave not in vocab["sectores"]:
            return match.group(0)
        etiqueta = vocab["sectores"][clave]
        contador[f"sector:{clave}"] = contador.get(f"sector:{clave}", 0) + 1
        return f'{match.group("pre")}{etiqueta}{match.group("post")}'

    patron = re.compile(
        r'id:\s*"sector_(?P<clave>[a-z_]+)"(?P<medio>[\s\S]{0,160}?)label:\s*"(?P<label>[^"]*)(")'
    )
    texto = re.sub(
        r'(id:\s*"sector_(?P<clave>[a-z_]+)"(?P<medio>[\s\S]{0,160}?)label:\s*")(?P<label>[^"]*)(")',
        lambda m: m.group(1) + vocab["sectores"].get(m.group("clave"), m.group("label")) + m.group(5),
        texto)
    return texto


def reescribir_grupos_visor(texto: str, vocab: dict, contador: dict) -> str:
    """Cada `group:` del visor toma el nombre canónico del sector de sus tablas."""
    sectores = {t["id"]: t["sector"] for t in vocab["tablas"]}

    def reemplazo(match: re.Match) -> str:
        bloque = match.group(0)
        for id_vista in re.findall(r'\bid:\s*"([a-z0-9_]+)"', bloque):
            sector = sectores.get(id_vista)
            if sector:
                etiqueta = vocab["sectores"][sector]
                contador[f"sector:{sector}"] = contador.get(f"sector:{sector}", 0) + 1
                return re.sub(r'(group:\s*")[^"]*(")',
                              lambda m: m.group(1) + etiqueta + m.group(2), bloque, count=1)
        return bloque

    return re.sub(r'\{\s*group:\s*"[\s\S]*?\n  \},', reemplazo, texto)


def bloque_alias(vocab: dict) -> str:
    lineas = []
    for tabla in vocab["tablas"]:
        alias = tabla.get("alias") or []
        if alias:
            valores = ", ".join(f'"{a}"' for a in alias)
            lineas.append(f"  {tabla['id']}: [{valores}],")
    cuerpo = "\n".join(lineas) if lineas else "  // (sin nombres anteriores)"
    return (
        "  // BEGIN VOCABULARIO ALIAS\n"
        f"{cuerpo}\n"
        "  // END VOCABULARIO ALIAS"
    )


def normalizar_alias(texto: str, vocab: dict) -> str:
    inicio = texto.index("  // BEGIN VOCABULARIO ALIAS")
    fin = texto.index("  // END VOCABULARIO ALIAS") + len("  // END VOCABULARIO ALIAS")
    return texto[:inicio] + bloque_alias(vocab) + texto[fin:]


def aplicar(escribir: bool = True) -> dict:
    vocab = vocabulario()
    mapa = mapa_ids(vocab)
    contador: dict = {}
    resultados = {}

    for rel in TARGETS:
        original = read(rel)
        texto = renombrar_ids(original, mapa, contador)
        texto = limpiar_nombres_antiguos(texto, contador)
        if rel.endswith("sidebar.js"):
            texto = normalizar_sidebar(texto, vocab, contador)
            texto = normalizar_nodos_arbol(texto, vocab, contador)
        elif rel.endswith("data_viewer.js"):
            texto = reescribir_grupos_visor(texto, vocab, contador)
            texto = reescribir_entradas(texto, vocab, contador, con_campos_extra=True)
        elif rel.endswith("data_dictionary.js"):
            texto = normalizar_diccionario(texto, vocab, contador)
        elif rel.endswith("erd_graph.js"):
            texto = reescribir_entradas(texto, vocab, contador, con_campos_extra=False)
        elif rel.endswith("duckdb_client.js"):
            texto = normalizar_alias(texto, vocab)
        if texto != original:
            resultados[rel] = True
            if escribir:
                write(rel, texto)
    return contador


# ── Comprobación ───────────────────────────────────────────────────────────────

def comprobar() -> list[str]:
    """Devuelve la lista de problemas de vocabulario (vacía si todo está al día)."""
    vocab = vocabulario()
    mapa = mapa_ids(vocab)
    problemas: list[str] = []

    for rel in TARGETS:
        texto = read(rel)
        # El bloque de alias declara a propósito los nombres anteriores: se revisa
        # aparte, contra el vocabulario, y no se cuenta como uso indebido.
        texto = re.sub(r"// BEGIN VOCABULARIO ALIAS[\s\S]*?// END VOCABULARIO ALIAS", "", texto)
        for alias, canonico in mapa.items():
            if alias == canonico:
                continue
            if patron_id(alias).search(texto):
                problemas.append(f"{rel}: sigue usando «{alias}» (canónico: {canonico})")
        for viejo, nuevo in NOMBRES_ANTIGUOS.items():
            if re.search(r"(?<![\w-])" + re.escape(viejo) + r"(?![\w])", texto):
                problemas.append(f"{rel}: sigue usando el nombre «{viejo}» (canónico: {nuevo})")

    # Nombres visibles por archivo
    esperados = {t["id"]: t["nombre"] for t in vocab["tablas"]}
    for rel in ("docs/js/sidebar.js", "docs/js/data_viewer.js", "docs/js/erd_graph.js"):
        texto = read(rel)
        for match in re.finditer(r'\bid:\s*"([a-z0-9_]+)"(?P<medio>[\s\S]{0,200}?)\bname:\s*"([^"]*)"', texto):
            id_vista, nombre = match.group(1), match.group(3)
            if id_vista in esperados and nombre != esperados[id_vista]:
                problemas.append(f"{rel}: {id_vista} se llama «{nombre}» y debe ser «{esperados[id_vista]}»")

    # Ids de nodo del explorador: `cat_<tabla_id>` (o el mapa de carpetas múltiples).
    sidebar = read("docs/js/sidebar.js")
    ids_vista = {t["id"] for t in vocab["tablas"]}
    for _, _, id_nodo, tipo_nodo, tablas in nodos_arbol(sidebar, ids_vista):
        if tipo_nodo != "circular" or not tablas:
            continue
        esperado = id_de_nodo(id_nodo, tablas) or id_nodo
        if id_nodo != esperado:
            problemas.append("sidebar.js: el nodo " + id_nodo + " debe llamarse " + esperado)

    for match in re.finditer(r'id:\s*"([a-z0-9_]+)"[\s\S]{0,200}?\brows:\s*"([^"]*)"', sidebar):
        id_vista, rows = match.groups()
        esperado = cobertura_de(vocab, id_vista)
        if esperado and rows != esperado:
            problemas.append(f"sidebar.js: la cobertura de {id_vista} dice «{rows}» y debe ser «{esperado}»")

    dic = read("docs/js/data_dictionary.js")
    for match in re.finditer(r'"id":\s*"([a-z0-9_]+)",\s*"name":\s*"([^"]+)"', dic):
        id_vista, nombre = match.groups()
        if id_vista in esperados and nombre != esperados[id_vista]:
            problemas.append(f"data_dictionary.js: {id_vista} se llama «{nombre}» y debe ser «{esperados[id_vista]}»")

    # Alias declarados en el motor
    motor = read("docs/js/duckdb_client.js")
    for tabla in vocab["tablas"]:
        for alias in tabla.get("alias", []):
            if f'"{alias}"' not in motor:
                problemas.append(f"duckdb_client.js: falta el alias SQL «{alias}» de {tabla['id']}")

    # Toda lista de entidades se llama lista_entidades
    for tabla in vocab["tablas"]:
        if tabla["tipo"].startswith("lista_entidades") and not tabla["nombre"].endswith(tabla["tipo"]):
            problemas.append(f"vocabulario.json: {tabla['id']} no sigue la regla lista_entidades")

    return problemas


def main() -> int:
    if "--check" in sys.argv:
        problemas = comprobar()
        if problemas:
            print("VOCABULARIO INCONSISTENTE:")
            for problema in problemas[:40]:
                print("  -", problema)
            return 1
        vocab = vocabulario()
        print(f"Vocabulario al día: {len(vocab['tablas'])} tablas, "
              f"{len(vocab['sectores'])} sectores, {len(vocab['tipos'])} tipos de tabla.")
        return 0

    contador = aplicar(escribir=True)
    print("Vocabulario aplicado.")
    for clave, valor in sorted(contador.items()):
        print(f"  {clave}: {valor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
