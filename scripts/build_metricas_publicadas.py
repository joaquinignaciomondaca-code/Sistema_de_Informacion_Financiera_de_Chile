#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcilia métricas del manifiesto ETL, API v2 y catálogo de descargas.

Genera `docs/metricas_publicadas.json` desde los tres artefactos vigentes. No
trata sus conteos como intercambiables: documenta qué unidad mide cada uno y
falla si filas, bytes, IDs o archivos se desalinean entre el contrato API y las
descargas. También comprueba que el README no desactualice el desglose por sector,
el total de consultas sugeridas ni el inventario/calendario de workflows.

Uso:
    python3 scripts/build_metricas_publicadas.py
    python3 scripts/build_metricas_publicadas.py --check
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "metricas_publicadas.json"


def cargar_json(ruta: Path) -> dict[str, Any]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"No se pudo leer {ruta.relative_to(ROOT)}: {exc}") from exc


def cargar_catalogo_descargas() -> dict[str, Any]:
    ruta = DOCS / "js" / "download_catalog.js"
    try:
        texto = ruta.read_text(encoding="utf-8")
        prefijo = "window.DOWNLOAD_CATALOG ="
        payload = texto.split(prefijo, 1)[1].strip()
        if not payload.endswith(";"):
            raise ValueError("falta el punto y coma final del objeto generado")
        return json.loads(payload[:-1].strip())
    except (OSError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"No se pudo leer el catálogo de descargas: {exc}") from exc


def entero(valor: Any) -> int:
    return int(valor or 0)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def auditar_tabla_readme(
    sectores: dict[str, dict[str, Any]],
    consultas_total: int,
    fuentes_por_sector: dict[str, set[str]],
    objetos_api: int,
    filas_api: int,
    principal: dict[str, int],
    fuera: dict[str, int],
) -> list[str]:
    """Comprueba que las cifras y cortes de la tabla sectorial no se desactualicen."""
    ruta = ROOT / "README.md"
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"No se pudo leer README.md para auditar sus métricas: {exc}"]

    texto_readme = "\n".join(lineas)
    if f"**{consultas_total} consultas sugeridas**" not in texto_readme:
        return [f"README.md: no declara las {consultas_total} consultas sugeridas del catálogo"]

    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    workflows_con_horario = [
        ruta for ruta in workflows
        if re.search(r"(?m)^\s*schedule:\s*$", ruta.read_text(encoding="utf-8"))
    ]
    cabecera_workflows = "| Flujo | Frecuencia (UTC) | Publica |"
    if cabecera_workflows not in lineas:
        return ["README.md: no se encontró el calendario de workflows"]
    inicio_workflows = lineas.index(cabecera_workflows)
    try:
        fin_workflows = lineas.index("</details>", inicio_workflows)
    except ValueError:
        return ["README.md: el bloque del calendario de workflows no se cierra"]
    nombres_listados = re.findall(
        r"\| `([^`]+\.yml)` \|", "\n".join(lineas[inicio_workflows:fin_workflows])
    )

    encabezado = "| Sector | Elementos | Filas (suma por objeto) | Serie | Fuente |"
    try:
        inicio = lineas.index(encabezado)
    except ValueError:
        return ["README.md: no se encontró la tabla sectorial con su encabezado contractual"]

    aliases = {"FinTech": "Fintech y Finanzas Abiertas"}
    filas_readme: dict[str, tuple[int, int, str, str]] = {}
    total_readme: tuple[int, int] | None = None
    for linea in lineas[inicio + 2:]:
        if not linea.startswith("|"):
            if filas_readme:
                break
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) != 5 or set(celdas[0]) <= {"-", ":", " "}:
            continue
        etiqueta = celdas[0].replace("**", "").strip()
        try:
            elementos = int(re.sub(r"\D", "", celdas[1]))
            filas = int(re.sub(r"\D", "", celdas[2]))
        except ValueError:
            continue
        if etiqueta.lower() == "total":
            total_readme = (elementos, filas)
            break
        etiqueta = aliases.get(etiqueta, etiqueta)
        filas_readme[etiqueta] = (elementos, filas, celdas[3], celdas[4])

    errores_readme: list[str] = []
    nombres_workflows = [ruta.name for ruta in workflows]
    faltan_workflows = sorted(set(nombres_workflows) - set(nombres_listados))
    sobran_workflows = sorted(set(nombres_listados) - set(nombres_workflows))
    if faltan_workflows or sobran_workflows or len(nombres_listados) != len(nombres_workflows):
        errores_readme.append(
            "README.md: calendario de workflows distinto de los archivos fuente "
            f"(faltan={faltan_workflows}, sobran={sobran_workflows})"
        )
    cantidad_workflows = len(workflows)
    cantidad_programados = len(workflows_con_horario)
    resumen_programacion = (
        f"({cantidad_programados} con horario; "
        f"{cantidad_workflows - cantidad_programados} sin `schedule`)"
    )
    if f"**{cantidad_workflows} workflows**" not in texto_readme or resumen_programacion not in texto_readme:
        errores_readme.append("README.md: total de workflows o cobertura de horarios desactualizados")

    por_etiqueta = {info["etiqueta"]: (clave, info) for clave, info in sectores.items()}
    no_encontrados = sorted(set(por_etiqueta) - set(filas_readme))
    inesperados = sorted(set(filas_readme) - set(por_etiqueta))
    if no_encontrados or inesperados:
        errores_readme.append(
            "README.md: la tabla sectorial no cubre exactamente el catálogo "
            f"(faltan={no_encontrados}, sobran={inesperados})"
        )
    for etiqueta in sorted(set(por_etiqueta) & set(filas_readme)):
        clave, esperado = por_etiqueta[etiqueta]
        elementos, filas, serie, fuentes_readme = filas_readme[etiqueta]
        if elementos != esperado["elementos"] or filas != esperado["filas"]:
            errores_readme.append(
                f"README.md: {etiqueta} declara {elementos} elementos/{filas} filas; "
                f"el catálogo indica {esperado['elementos']}/{esperado['filas']}"
            )
        periodo = esperado.get("periodo")
        if clave != "macro" and periodo:
            for extremo in ("desde", "hasta"):
                fecha = periodo.get(extremo)
                if fecha and fecha not in serie:
                    errores_readme.append(
                        f"README.md: el corte {extremo} de {etiqueta} ({fecha}) no aparece en la serie declarada"
                    )
        fuentes_esperadas = set(fuentes_por_sector.get(clave, set()))
        fuentes_publicadas = set().union(*fuentes_por_sector.values()) if fuentes_por_sector else set()
        fuentes_declaradas = {
            fuente for fuente in fuentes_publicadas
            if re.search(rf"(?<!\w){re.escape(fuente)}(?!\w)", fuentes_readme, re.IGNORECASE)
        }
        fuentes_ausentes = sorted(fuentes_esperadas - fuentes_declaradas)
        fuentes_sobrantes = sorted(fuentes_declaradas - fuentes_esperadas)
        if fuentes_ausentes or fuentes_sobrantes:
            errores_readme.append(
                f"README.md: fuentes declaradas para {etiqueta} distintas del catálogo; "
                f"faltan={fuentes_ausentes}, sobran={fuentes_sobrantes} en «{fuentes_readme}»"
            )
    total_esperado = (
        sum(info["elementos"] for info in sectores.values()),
        sum(info["filas"] for info in sectores.values()),
    )
    if total_readme != total_esperado:
        errores_readme.append(
            f"README.md: total sectorial {total_readme} no coincide con {total_esperado}"
        )

    resumen_api = re.search(
        r"El catálogo API suma\s+([\d.]+)\s+objetos y\s+([\d.]+)\s+filas",
        texto_readme,
        re.IGNORECASE,
    )
    esperado_api = (objetos_api, filas_api)
    declarado_api = (
        tuple(int(re.sub(r"\D", "", valor)) for valor in resumen_api.groups())
        if resumen_api else None
    )
    if declarado_api != esperado_api:
        errores_readme.append(
            f"README.md: resumen narrativo API {declarado_api} no coincide con {esperado_api}"
        )

    resumen_alcance = re.search(
        r"De esos\s+([\d.]+)\s+elementos,\s+([\d.]+)\s+están en niveles principales\s+"
        r"\(([\d.]+)\s+filas;[^)]*\)\s+y\s+([\d.]+)\s+en archivo/registro\s+"
        r"\(([\d.]+);",
        texto_readme,
        re.IGNORECASE,
    )
    esperado_alcance = (
        principal["conjuntos"] + fuera["conjuntos"],
        principal["conjuntos"],
        principal["filas"],
        fuera["conjuntos"],
        fuera["filas"],
    )
    declarado_alcance = (
        tuple(int(re.sub(r"\D", "", valor)) for valor in resumen_alcance.groups())
        if resumen_alcance else None
    )
    if declarado_alcance != esperado_alcance:
        errores_readme.append(
            f"README.md: resumen narrativo de Descargas {declarado_alcance} "
            f"no coincide con {esperado_alcance}"
        )
    return errores_readme


def fuentes_para_readme(
    manifiesto: dict[str, Any], fuentes_api: dict[str, set[str]]
) -> dict[str, set[str]]:
    """Combina la atribución API con fuentes corroboradas en el origen ETL.

    `fuente` en el API es la atribución primaria. Para el registro de sistemas
    de pago, el manifiesto además atribuye expresamente la LBTR al BCCh, junto
    con los registros CMF; solo esa contribución explícita se añade. No se
    infieren fuentes desde menciones de reguladores, leyes o enlaces.
    """
    resultado = {sector: set(fuentes) for sector, fuentes in fuentes_api.items()}
    for tabla in manifiesto.get("tables", []):
        if tabla.get("sector") != "sistemas_pago":
            continue
        metadata = tabla.get("metadatos", {}) or {}
        fuente_texto = str(metadata.get("fuente", ""))
        origen = str(tabla.get("origen", ""))
        if (
            "BCCh para la LBTR" in fuente_texto
            and re.search(r"LBTR\s*\(BCCh\)", origen, re.IGNORECASE)
        ):
            resultado.setdefault("sistemas_pago", set()).add("BCCh")
    return resultado


def auditar_procedencia_y_modalidades_readme(
    manifiesto: dict[str, Any], api: dict[str, Any]
) -> list[str]:
    """Comprueba que el README conserve los matices de procedencia y modalidad."""
    try:
        texto = (ROOT / "README.md").read_text(encoding="utf-8")
    except OSError as exc:
        return [f"No se pudo leer README.md para auditar fuentes y modalidades: {exc}"]
    texto_lower = texto.lower()
    errores: list[str] = []

    objetos = api.get("objetos", [])
    ccaf = next((o for o in objetos if o.get("id") == "ccaf_lista_entidades"), {})
    procedencia = ccaf.get("procedencia", {})
    editorial = procedencia.get("procedencia_editorial", {})
    universo = editorial.get("universo_inicial", [])
    instituciones = sorted({
        str(item.get("institucion", "")).strip()
        for item in universo if item.get("institucion")
    })
    parrafos = re.split(r"\n\s*\n", texto.lower())
    contexto_ccaf = next(
        (p for p in parrafos if "universo inicial" in p and all(i.lower() in p for i in instituciones)),
        "",
    )
    if not instituciones or not contexto_ccaf:
        errores.append(
            "README.md: falta un contexto que atribuya el universo inicial de CCAF "
            f"a las instituciones editoriales del catálogo ({instituciones})"
        )
    if "registro de valores" not in contexto_ccaf or "suseso" not in contexto_ccaf:
        errores.append(
            "README.md: la procedencia histórica CCAF debe distinguir listados SUSESO "
            "y Registro de Valores CMF"
        )
    actuales = procedencia.get("fuentes_directas_actuales", [])
    recursos_actuales = " ".join(
        str(item.get("recurso", "")) for item in actuales if item.get("recurso")
    ).lower()
    if "txt ifrs" in recursos_actuales and "txt ifrs" not in texto_lower:
        errores.append("README.md: no describe el TXT IFRS como fuente directa actual para altas CCAF")

    etiquetas = {"automatico": "Automático", "hibrido": "Híbrido", "manual": "Manual"}
    requisitos = {
        "automatico": ("programad",),
        "hibrido": ("fuentes no estructuradas", "reproducibles", "fuera de actions"),
        "manual": ("intervención", "compilador reproducible"),
    }
    clasificacion = manifiesto.get("classification", {})
    for modo in clasificacion:
        etiqueta = etiquetas.get(str(modo).lower())
        if not etiqueta or etiqueta.lower() not in texto_lower:
            errores.append(f"README.md: falta la modalidad de procesamiento {modo!r}")
            continue
        faltan = [termino for termino in requisitos.get(str(modo).lower(), ()) if termino not in texto_lower]
        if faltan:
            errores.append(
                f"README.md: la descripción de {etiqueta} omite matices del manifiesto: {faltan}"
            )

    oraciones = re.split(r"(?<=[.!?])\s+", texto_lower)
    for tabla in manifiesto.get("tables", []):
        modo = str(tabla.get("modo", "")).lower()
        if not modo.startswith("híbrido"):
            continue
        nombre = str(tabla.get("name") or tabla.get("id") or "")
        tokens = [token for token in re.split(r"[._\s]+", nombre.lower()) if len(token) > 2]
        mencionada = any(
            "híbrido" in oracion and all(token in oracion for token in tokens)
            for oracion in oraciones
        )
        if not mencionada:
            errores.append(
                f"README.md: no identifica como híbrido el conjunto {nombre!r} que así figura en data_manifest.json"
            )
    return errores


def construir() -> dict[str, Any]:
    manifiesto = cargar_json(ROOT / "data_manifest.json")
    api = cargar_json(DOCS / "api" / "v2" / "catalog.json")
    consultas = cargar_json(DOCS / "api" / "v2" / "queries.json")
    descargas = cargar_catalogo_descargas()
    with (DOCS / "api" / "reconciliacion.csv").open(encoding="utf-8-sig", newline="") as fh:
        reconciliacion = list(csv.DictReader(fh))

    tablas = manifiesto.get("tables")
    objetos = api.get("objetos")
    if not isinstance(tablas, list) or not isinstance(objetos, list):
        raise SystemExit("El manifiesto ETL o el catálogo API no tiene la estructura esperada")
    ids_tablas = [t.get("id") for t in tablas]
    ids_objetos = [o.get("id") for o in objetos]
    if None in ids_tablas or len(set(ids_tablas)) != len(ids_tablas):
        raise SystemExit("data_manifest.json contiene IDs de tabla faltantes o duplicados")
    if None in ids_objetos or len(set(ids_objetos)) != len(ids_objetos):
        raise SystemExit("catalog.json contiene IDs de objeto faltantes o duplicados")

    grupos = descargas.get("grupos")
    if not isinstance(grupos, list):
        raise SystemExit("download_catalog.js no contiene grupos de elementos")
    elementos = [item for grupo in grupos for item in grupo.get("items", [])]
    ids_descargas = [i.get("id") for i in elementos]
    if None in ids_descargas or len(set(ids_descargas)) != len(ids_descargas):
        raise SystemExit("download_catalog.js contiene IDs faltantes o duplicados")
    por_descarga = {i["id"]: i for i in elementos}

    totales_api = api.get("totales", {})
    if len(objetos) != entero(totales_api.get("objetos")):
        raise SystemExit("catalog.json: `totales.objetos` no coincide con la lista de objetos")
    if set(ids_objetos) != set(ids_descargas):
        faltan_descargas = sorted(set(ids_objetos) - set(ids_descargas))
        sobran_descargas = sorted(set(ids_descargas) - set(ids_objetos))
        raise SystemExit(
            "API y descargas exponen IDs distintos; "
            f"faltan en descargas={faltan_descargas}, sobran={sobran_descargas}"
        )
    if {r.get("objeto") for r in reconciliacion} != set(ids_objetos):
        raise SystemExit("reconciliacion.csv no cubre exactamente los IDs del catálogo API")
    puentes = Counter(r.get("puente") for r in reconciliacion)
    if len(reconciliacion) != len(objetos):
        raise SystemExit("reconciliacion.csv y catalog.json tienen distinta cantidad de objetos")

    particiones_por_objeto: dict[str, dict[str, Any]] = {}
    rutas_totales_api: set[str] = set()
    rutas_totales_descargas: set[str] = set()
    errores: list[str] = []
    for objeto in objetos:
        oid = objeto["id"]
        descarga = por_descarga[oid]
        rel = Path("api") / "v2" / "partitions" / f"{oid}.json"
        manifiesto_partes = cargar_json(DOCS / rel)
        partes_api = manifiesto_partes.get("particiones", [])
        total_partes = manifiesto_partes.get("total", {})
        rutas_api = {p.get("archivo") for p in partes_api}
        rutas_descarga = {a.get("ruta") for a in descarga.get("archivos", [])}
        rutas_totales_api.update(rutas_api)
        rutas_totales_descargas.update(rutas_descarga)
        if rutas_api != rutas_descarga:
            errores.append(f"{oid}: las rutas API y descargas difieren")
        checks = (
            ("filas catálogo/descargas", entero(objeto.get("filas")), entero(descarga.get("filas"))),
            ("bytes catálogo/descargas", entero(objeto.get("bytes")), entero(descarga.get("bytes"))),
            ("particiones catálogo/descargas", entero(objeto.get("particiones")), entero(descarga.get("archivosN"))),
            ("filas catálogo/particiones", entero(objeto.get("filas")), entero(total_partes.get("filas"))),
            ("bytes catálogo/particiones", entero(objeto.get("bytes")), entero(total_partes.get("bytes"))),
            ("archivos catálogo/particiones", entero(objeto.get("particiones")), entero(total_partes.get("archivos"))),
            ("rutas/particiones", len(partes_api), entero(objeto.get("particiones"))),
        )
        for nombre, api_valor, descarga_valor in checks:
            if api_valor != descarga_valor:
                errores.append(f"{oid}: {nombre} difiere (API={api_valor}, descargas={descarga_valor})")
        particiones_por_objeto[oid] = manifiesto_partes

    # Cada tabla ETL debe tener representación pública. Las renombradas se enlazan
    # por `aliases`; la única entrada de origen que se convierte en dos objetos es
    # bancos_cmf_lineas, materializada como dos salidas filtradas.
    ids_etl = set(ids_tablas)
    objetos_por_fuente: Counter[str] = Counter()
    for objeto in objetos:
        oid = objeto["id"]
        if oid in ids_etl:
            fuente = oid
        else:
            alias_fuente = [a for a in objeto.get("aliases", []) if a in ids_etl]
            if len(alias_fuente) > 1:
                errores.append(f"{oid}: más de una tabla ETL candidata por alias: {alias_fuente}")
                continue
            if alias_fuente:
                fuente = alias_fuente[0]
            elif objeto.get("deriva_de") in ids_etl:
                fuente = objeto["deriva_de"]
            else:
                errores.append(f"{oid}: no se pudo vincular a una tabla de data_manifest.json")
                continue
        objetos_por_fuente[fuente] += 1
    sin_representar = sorted(ids_etl - set(objetos_por_fuente))
    si_no_uno = {k: v for k, v in objetos_por_fuente.items() if v != 1}
    if sin_representar:
        errores.append(f"Tablas ETL sin objeto API: {sin_representar}")
    splits = {k: v for k, v in si_no_uno.items() if v > 1}
    if splits != {"bancos_cmf_lineas": 2}:
        errores.append(f"Cambió el mapeo tabla ETL → objetos API; revisar definiciones: {si_no_uno}")
    if sum(objetos_por_fuente.values()) != len(objetos):
        errores.append("El mapeo ETL → API no cubre todos los objetos exactamente una vez")

    # El usuario pidió que balance y resultados de banca no expongan el mismo
    # Parquet combinado B1+B2+R1 bajo dos nombres. Comprueba archivos separados en
    # API y en Descargas, no sólo los rótulos.
    rutas_balance = {p.get("archivo") for p in particiones_por_objeto["bancos_balance"]["particiones"]}
    rutas_resultados = {p.get("archivo") for p in particiones_por_objeto["bancos_resultados"]["particiones"]}
    if not rutas_balance or not rutas_resultados or rutas_balance & rutas_resultados:
        errores.append("Banca: balance y resultados comparten archivos o no tienen particiones")
    if not all(p.startswith("outputs/bancos/balance_b1_b2/") for p in rutas_balance):
        errores.append("Banca: `bancos_balance` no apunta sólo a archivos B1/B2 separados")
    if not all(p.startswith("outputs/bancos/resultados_r1/") for p in rutas_resultados):
        errores.append("Banca: `bancos_resultados` no apunta sólo a archivos R1 separados")
    filtros_banca = {
        "bancos_balance": "familia_archivo_fuente IN ('B1', 'B2')",
        "bancos_resultados": "familia_archivo_fuente = 'R1'",
    }
    for oid, filtro_esperado in filtros_banca.items():
        if particiones_por_objeto[oid].get("filtro") != filtro_esperado:
            errores.append(f"Banca: el filtro publicado de {oid} cambió; revisar la descripción")
        if not por_descarga[oid].get("descargaFiltrada"):
            errores.append(f"Banca: Descargas no marca {oid} como salida filtrada")

    tablas_filas = sum(entero(t.get("registros_reales")) for t in tablas)
    filas_api = sum(entero(o.get("filas")) for o in objetos)
    bytes_api = sum(entero(o.get("bytes")) for o in objetos)
    filas_descargas = sum(entero(i.get("filas")) for i in elementos)
    bytes_descargas = sum(entero(i.get("bytes")) for i in elementos)
    filas_manifiesto_declaradas = entero(manifiesto.get("total_records"))
    if len(tablas) != entero(manifiesto.get("total_tables")):
        errores.append("data_manifest.json: `total_tables` no coincide con la lista")
    if tablas_filas != filas_manifiesto_declaradas:
        errores.append("data_manifest.json: `total_records` no coincide con las filas de sus tablas")
    if filas_api != entero(totales_api.get("filas")) or bytes_api != entero(totales_api.get("bytes")):
        errores.append("catalog.json: los totales no coinciden con la suma de sus objetos")
    if len(objetos) != entero(descargas.get("conjuntos")) or len(elementos) != entero(descargas.get("conjuntos")):
        errores.append("download_catalog.js: `conjuntos` no coincide con sus elementos")
    if filas_descargas != entero(descargas.get("filas")) or bytes_descargas != entero(descargas.get("bytes")):
        errores.append("download_catalog.js: sus totales no coinciden con la suma de sus elementos")
    if not (tablas_filas == filas_api == filas_descargas == filas_manifiesto_declaradas):
        errores.append(
            "Las filas totales difieren entre manifiesto ETL, API y descargas: "
            f"{filas_manifiesto_declaradas}/{filas_api}/{filas_descargas}"
        )
    if bytes_api != bytes_descargas:
        errores.append(f"Los bytes API/descargas difieren: {bytes_api}/{bytes_descargas}")
    if rutas_totales_api != rutas_totales_descargas:
        errores.append("Los archivos únicos referenciados en API y Descargas difieren")

    # DuckDB precarga cuatro Parquet compactos específicos para algunas consultas.
    # Son copias de lectura, no recursos API ni filas adicionales de cobertura.
    duckdb_js = (DOCS / "js" / "duckdb_client.js").read_text(encoding="utf-8")
    query_files = set(re.findall(r'queryFile:\s*"([^"]+)"', duckdb_js))
    manifests_sql = sorted((DOCS / "outputs" / "sql_query").glob("*.manifest.json"))
    compactos_sql: list[dict[str, Any]] = []
    rutas_compactas: set[str] = set()
    for ruta_manifest in manifests_sql:
        item = cargar_json(ruta_manifest)
        ruta = str(item.get("file", ""))
        fisico = DOCS / ruta
        rutas_compactas.add(ruta)
        if not ruta or ruta not in query_files:
            errores.append(f"{ruta_manifest.name}: el Parquet no figura en queryFile de duckdb_client.js")
        if not fisico.is_file():
            errores.append(f"{ruta_manifest.name}: no existe el Parquet {ruta}")
        elif entero(item.get("bytes")) != fisico.stat().st_size:
            errores.append(f"{ruta_manifest.name}: bytes del manifiesto no coinciden con el archivo")
        compactos_sql.append({
            "ruta": ruta,
            "filas": entero(item.get("records")),
            "bytes": entero(item.get("bytes")),
        })
    if query_files != rutas_compactas:
        errores.append(
            "Las queryFile de DuckDB y los manifiestos SQL compactos difieren: "
            f"queryFile={sorted(query_files)}, manifiestos={sorted(rutas_compactas)}"
        )
    if rutas_compactas & rutas_totales_api:
        errores.append("Un Parquet compacto SQL se cuenta también como partición de API")
    filas_compactas = sum(i["filas"] for i in compactos_sql)
    bytes_compactos = sum(i["bytes"] for i in compactos_sql)

    estados = Counter(o.get("estado") for o in objetos)
    con_archivo = sum(1 for o in objetos if entero(o.get("particiones")) > 0)
    con_filas = sum(1 for o in objetos if entero(o.get("filas")) > 0)
    sin_archivo = len(objetos) - con_archivo
    archivo_sin_filas = sum(
        1 for o in objetos if entero(o.get("particiones")) > 0 and entero(o.get("filas")) == 0
    )
    consultas_total = len(consultas.get("consultas", []))
    if con_archivo != entero(totales_api.get("con_datos")):
        errores.append("catalog.json: `con_datos` no coincide con objetos con particiones")
    if con_filas != entero(totales_api.get("con_filas")):
        errores.append("catalog.json: `con_filas` no coincide con objetos con filas")
    if sin_archivo != entero(totales_api.get("vacios")):
        errores.append("catalog.json: `vacios` no coincide con objetos sin archivo")
    if estados["derivado"] != entero(totales_api.get("derivados")):
        errores.append("catalog.json: `derivados` no coincide con los objetos derivados")
    if estados["vacio"] != entero(totales_api.get("vacios")):
        errores.append("catalog.json: `vacios` no coincide con el estado de los objetos")
    if consultas_total != entero(consultas.get("total")):
        errores.append("queries.json: `total` no coincide con la lista de consultas")
    if consultas_total != entero(totales_api.get("consultas")):
        errores.append("El total de consultas no coincide entre queries.json y catalog.json")

    alcance = descargas.get("alcance", {})
    resumen_visible = alcance.get("visible", {})
    resumen_fuera = alcance.get("fuera", {})
    niveles = alcance.get("niveles", [])
    ids_niveles_visibles = set(alcance.get("visibles", []))
    ocultos = [i for i in elementos if i.get("oculto")]
    variantes = [i for i in elementos if i.get("varianteDe")]
    visibles = [i for i in elementos if not i.get("oculto") and i.get("nivel") in ids_niveles_visibles]
    fuera_foco = [i for i in elementos if not i.get("oculto") and i.get("nivel") not in ids_niveles_visibles]

    def cifras(items: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "conjuntos": len(items),
            "filas": sum(entero(i.get("filas")) for i in items),
            "bytes": sum(entero(i.get("bytes")) for i in items),
        }

    def suma_ocultos(campo: str) -> int:
        return sum(entero(i.get(campo)) for i in ocultos)

    visible = cifras(visibles)
    fuera = cifras(fuera_foco)
    sectores_alcance = alcance.get("sectores", {})
    claves_sector = {str(i.get("clave")) for i in elementos if not i.get("oculto")}
    periodos_por_sector: dict[str, list[str]] = {}
    fuentes_por_sector: dict[str, set[str]] = {}
    for objeto in objetos:
        sector = objeto.get("sector")
        fuente = str(objeto.get("fuente") or "").strip()
        if sector and fuente:
            fuentes_por_sector.setdefault(str(sector), set()).add(fuente)
        fechas_corte = re.findall(
            r"(?<!\d)(?:19|20)\d{2}-(?:0[1-9]|1[0-2])(?!\d)",
            str(objeto.get("corte") or ""),
        )
        if sector and fechas_corte:
            periodos_por_sector.setdefault(sector, []).extend(fechas_corte)
    sectores_reportados: dict[str, dict[str, Any]] = {}
    for clave_sector, info in sorted(sectores_alcance.items()):
        items_sector = [
            i for i in elementos
            if not i.get("oculto") and i.get("clave") == clave_sector
        ]
        conteo_sector = cifras(items_sector)
        fechas_sector = periodos_por_sector.get(clave_sector, [])
        periodo_api = (
            {"desde": min(fechas_sector), "hasta": max(fechas_sector)}
            if fechas_sector else None
        )
        periodo_catalogo = info.get("periodo")
        if periodo_catalogo and periodo_api and periodo_catalogo != periodo_api:
            errores.append(
                f"Sector {clave_sector}: el período del alcance difiere de los cortes declarados por API"
            )
        for campo in ("conjuntos", "filas", "bytes"):
            if conteo_sector[campo] != entero(info.get(campo)):
                errores.append(
                    f"Sector {clave_sector}: el alcance `{campo}` no coincide con sus elementos"
                )
        fuentes_sector = sorted(fuentes_por_sector.get(clave_sector, set()))
        sectores_reportados[clave_sector] = {
            "etiqueta": info.get("corta") or info.get("etiqueta"),
            "nivel": info.get("nivel"),
            "fuentes": fuentes_sector,
            "elementos": conteo_sector["conjuntos"],
            "filas": conteo_sector["filas"],
            "bytes": conteo_sector["bytes"],
            "periodo": periodo_catalogo or periodo_api,
        }
    if claves_sector != set(sectores_alcance):
        errores.append(
            "El catálogo de descargas contiene sectores no cubiertos o vacíos: "
            f"elementos={sorted(claves_sector)}, alcance={sorted(sectores_alcance)}"
        )
    sumas_sector = {
        "conjuntos": sum(i["elementos"] for i in sectores_reportados.values()),
        "filas": sum(i["filas"] for i in sectores_reportados.values()),
        "bytes": sum(i["bytes"] for i in sectores_reportados.values()),
    }
    if sumas_sector != {
        "conjuntos": visible["conjuntos"] + fuera["conjuntos"],
        "filas": visible["filas"] + fuera["filas"],
        "bytes": visible["bytes"] + fuera["bytes"],
    }:
        errores.append("Las sumas por sector no coinciden con los niveles visibles y fuera de foco")
    for campo in ("conjuntos", "filas", "bytes"):
        if visible[campo] != entero(resumen_visible.get(campo)):
            errores.append(f"El alcance visible no coincide con los elementos ({campo})")
        if fuera[campo] != entero(resumen_fuera.get(campo)):
            errores.append(f"El alcance fuera de foco no coincide con los elementos ({campo})")
    visible_niveles = sum(entero(n.get("conjuntos")) for n in niveles if n.get("visible"))
    fuera_niveles = sum(entero(n.get("conjuntos")) for n in niveles if not n.get("visible"))
    if visible_niveles != visible["conjuntos"]:
        errores.append("El total visible no coincide con la suma de niveles visibles")
    if fuera_niveles != fuera["conjuntos"]:
        errores.append("El total fuera de foco no coincide con la suma de niveles no visibles")
    if visible["conjuntos"] + fuera["conjuntos"] + len(ocultos) != len(elementos):
        errores.append("Los elementos de descargas no se reconcilian entre visibles, fuera y ocultos")
    if visible["filas"] + fuera["filas"] + suma_ocultos("filas") != filas_descargas:
        errores.append("Las filas por alcance no suman el total de descargas")
    if visible["bytes"] + fuera["bytes"] + suma_ocultos("bytes") != bytes_descargas:
        errores.append("Los bytes por alcance no suman el total de descargas")
    errores.extend(
        auditar_tabla_readme(
            sectores_reportados,
            consultas_total,
            fuentes_para_readme(manifiesto, fuentes_por_sector),
            len(objetos),
            filas_api,
            visible,
            fuera,
        )
    )
    errores.extend(auditar_procedencia_y_modalidades_readme(manifiesto, api))

    filas_mismo = tablas_filas == filas_api == filas_descargas
    bytes_mismos = bytes_api == bytes_descargas
    ids_ocultos = sorted(i["id"] for i in ocultos)

    reporte = {
        "contrato": "sif/metricas-publicadas",
        "version": "1.1.0",
        "data_release": api.get("data_release"),
        "definiciones": {
            "tablas_etl": "Entradas de data_manifest.json: unidades registradas por el pipeline de extracción; no equivalen a objetos lógicos de API ni a elementos de navegación.",
            "objetos_api": "Objetos lógicos de catalog.json. Incluyen vistas derivadas y nombres canónicos; una entrada ETL puede dar origen a más de un objeto.",
            "con_archivo": "Objetos API con una o más particiones publicadas; puede incluir un Parquet de cero filas.",
            "con_filas": "Objetos API cuyo conteo de filas es mayor que cero.",
            "elementos_descarga": "Elementos del catálogo de descargas, con IDs y archivos por objeto; las variantes se cuentan como elemento y se presentan junto a su objeto base.",
            "alcance_principal": "Elementos en niveles visibles (núcleo, instituciones y contexto), según el alcance editorial de docs/vocabulario.json.",
            "fuera_de_foco": "Elementos en niveles de archivo o registro; siguen publicados y disponibles según su ficha.",
            "por_sector": "Desglose de elementos no ocultos por sector. Filas y bytes son sumas por objeto, no registros globales únicos; período es el mínimo y máximo declarados en los cortes de API, no prueba continuidad temporal.",
            "ocultos": "Elementos retenidos en los contratos, pero fuera de la navegación por una razón editorial documentada.",
            "filas_por_objeto": "Suma de filas recibidas por objeto lógico. Puede contar de nuevo una ruta compartida entre vistas y no equivale a registros globalmente únicos.",
            "filas_unicas_esquemas": "En esquemas.json, suma filas de cada ruta Parquet física distinta una sola vez; no deduplica filas con valores idénticos.",
            "auxiliares_sql": "Parquet compactos que DuckDB usa para algunas consultas; son copias de lectura, no objetos adicionales ni filas únicas de cobertura.",
            "filas_almacenadas_en_runtime": "Suma física de filas en los archivos API y auxiliares SQL; incluye copias/solapes y no debe leerse como cobertura única.",
            "bytes": "Suma de tamaños de las particiones incluidas en el contrato; no es el tamaño de todo docs/ ni de todos los Parquet físicos.",
        },
        "fuentes": {
            "inventario_etl": {
                "artefacto": "data_manifest.json",
                "tablas": len(tablas),
                "filas": tablas_filas,
            },
            "api_v2": {
                "artefacto": "api/v2/catalog.json",
                "objetos": len(objetos),
                "por_estado": {clave: estados[clave] for clave in sorted(estados)},
                "con_archivo": con_archivo,
                "con_filas": con_filas,
                "sin_archivo": sin_archivo,
                "con_archivo_sin_filas": archivo_sin_filas,
                "filas": filas_api,
                "bytes": bytes_api,
                "particiones": sum(entero(o.get("particiones")) for o in objetos),
                "archivos_unicos": len(rutas_totales_api),
                "consultas": consultas_total,
                "data_release": api.get("data_release"),
            },
            "descargas": {
                "artefacto": "js/download_catalog.js",
                "elementos": len(elementos),
                "principal": {
                    "elementos": visible["conjuntos"],
                    "filas": visible["filas"],
                    "bytes": visible["bytes"],
                },
                "fuera_de_foco": {
                    "elementos": fuera["conjuntos"],
                    "filas": fuera["filas"],
                    "bytes": fuera["bytes"],
                },
                "ocultos": {
                    "elementos": len(ocultos),
                    "ids": ids_ocultos,
                    "filas": suma_ocultos("filas"),
                    "bytes": suma_ocultos("bytes"),
                },
                "variantes": len(variantes),
                "filas_total": filas_descargas,
                "bytes_total": bytes_descargas,
                "archivos_unicos": len(rutas_totales_descargas),
                "por_sector": sectores_reportados,
            },
            "auxiliares_sql": {
                "artefactos": "outputs/sql_query/*.manifest.json",
                "archivos": len(compactos_sql),
                "filas_materializadas": filas_compactas,
                "bytes": bytes_compactos,
                "excluidos_de_totales_api_y_descargas": True,
            },
        },
        "lecturas_duckdb": {
            "archivos_unicos": len(rutas_totales_api | rutas_compactas),
            "filas_almacenadas": filas_api + filas_compactas,
            "bytes": bytes_api + bytes_compactos,
            "nota": "Suma archivos del contrato y copias compactas de consulta; contiene filas repetidas entre recursos y no representa cobertura única.",
        },
        "puentes_reconciliacion": {clave: puentes[clave] for clave in sorted(puentes)},
        "relacion_inventario_api": {
            "tablas_etl": len(tablas),
            "objetos_api": len(objetos),
            "tablas_con_un_objeto": sum(1 for n in objetos_por_fuente.values() if n == 1),
            "tablas_que_se_dividen_en_varios_objetos": [
                {"tabla_etl": tabla, "objetos_api": cantidad}
                for tabla, cantidad in sorted(splits.items())
            ],
            "explicacion": "bancos_cmf_lineas se publica como dos objetos lógicos, bancos_balance y bancos_resultados, con archivos filtrados distintos; los alias cambian nombres, no crean objetos adicionales.",
        },
        "alineacion": {
            "ids_api_descargas_iguales": True,
            "filas_manifiesto_api_descargas_iguales": filas_mismo,
            "bytes_api_descargas_iguales": bytes_mismos,
            "archivos_unicos_api_descargas_iguales": rutas_totales_api == rutas_totales_descargas,
            "particiones_rutas_y_conteos_iguales_por_objeto": True,
            "balance_y_resultados_bancarios_usan_archivos_separados": True,
        },
    }
    if errores:
        detalle = "\n".join(f"- {error}" for error in errores)
        raise SystemExit("Las métricas publicadas no se reconcilian:\n" + detalle)
    return reporte


def render(doc: dict[str, Any]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="falla si el artefacto no coincide")
    args = parser.parse_args()
    doc = construir()
    contenido = render(doc)
    if args.check:
        try:
            actual = OUT.read_text(encoding="utf-8")
        except OSError:
            actual = ""
        if actual != contenido:
            print("MÉTRICAS DESACTUALIZADAS: ejecuta scripts/build_metricas_publicadas.py", file=sys.stderr)
            return 1
        print("MÉTRICAS OK: inventario ETL, API v2 y descargas se reconcilian")
    else:
        OUT.write_text(contenido, encoding="utf-8")
        f = doc["fuentes"]
        cantidad_oculta = f["descargas"]["ocultos"]["elementos"]
        etiqueta_oculta = "oculto" if cantidad_oculta == 1 else "ocultos"
        print(
            "Métricas publicadas reconciliadas: "
            f"{f['inventario_etl']['tablas']} tablas ETL → {f['api_v2']['objetos']} objetos API; "
            f"{f['descargas']['principal']['elementos']} visibles + "
            f"{f['descargas']['fuera_de_foco']['elementos']} fuera + "
            f"{cantidad_oculta} {etiqueta_oculta}; "
            f"{fmt(f['api_v2']['filas'])} filas y {fmt(f['api_v2']['bytes'])} bytes alineados."
        )
        print(f"Escrito: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
