"""Integra solo EEFF FI publicados/validados en los catálogos estáticos.

Los bloques delimitados pertenecen al publicador; el resto del sitio no se toca.
Se regenera sobre la cabeza vigente de la rama, fuera del commit de datos, para
no chocar con otros publicadores. No registra vistas antes del primer cierre.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from fi.scripts import eeff_xml as xml
from pipelines.auto import estable

RAIZ = Path(__file__).resolve().parents[2]
MARCAS = {
    "duckdb_client.js": "VIEWS",
    "data_viewer.js": "VIEWER",
    "data_dictionary.js": "DICTIONARY",
    "sidebar.js": "NAVIGATION",
}
COBERTURA = "Trimestral · contextos separados"
DESCRIPCIONES = {
    "balance": "Estado de situación financiera de fondos de inversión FIRES/FINRE, cuenta por cuenta (42 líneas por contexto). TotalPasivo de la fuente incluye patrimonio: el pasivo exigible es TotalPasivoCorriente + TotalPasivoNoCorriente. Miles de la moneda de presentación, sin conversión.",
    "resultados": "Estado de resultados integrales de fondos de inversión FIRES/FINRE, cuenta por cuenta (30 líneas por contexto). Se separan acumulado del ejercicio, trimestre y sus comparativos; no se suman entre sí. Miles de la moneda de presentación, gastos con signo original.",
}
ORIGEN = "CMF — XML IFRS FIEF (Circular 1998) de cada fondo, enlazado en entidad.php?tipoentidad=FIRES|FINRE&pestania=29. Cotejo con las tablas de su ficha; no es una auditoría independiente del PDF firmado."
DEFINICIONES = {
    "periodo": (
        "PK",
        "Cierre del archivo AAAA-MM. En comparativos no es la fecha de la cifra: usar fecha_fin_contexto.",
    ),
    "run_fondo": (
        "FK",
        "RUN del fondo, sin DV; une directamente con fi.lista_entidades.",
    ),
    "run_fondo_dv": (
        "Atributo",
        "RUN con DV módulo 11. El DV recibido se conserva separado.",
    ),
    "dv_fondo_fuente": (
        "Dato fuente",
        "Dígito verificador literal del XML; las discrepancias quedan como aviso.",
    ),
    "nombre_fondo": (
        "Dimensión",
        "Nombre reportado en el XML; puede ser abreviado y diferir del maestro.",
    ),
    "tipo_entidad": (
        "Dimensión",
        "FIRES rescatable / FINRE no rescatable, según registro CMF.",
    ),
    "rut_agf": (
        "FK",
        "RUT de la administradora reportada, sin DV; une con agf.lista_entidades.",
    ),
    "razon_social_agf": (
        "Dimensión",
        "Nombre de administradora declarado en este envío.",
    ),
    "moneda": (
        "Dimensión",
        "Moneda de presentación: CLP, USD, EUR o COP; no sumar monedas distintas.",
    ),
    "moneda_cmf": (
        "Dato fuente",
        "Código CMF literal ($$ pesos, PROM dólar, EUR euro, COP peso colombiano).",
    ),
    "contexto": (
        "PK",
        "Contexto original. PeriodoActual = saldo/acumulado actual; PeriodoAnualAnterior = balance al diciembre anterior; PeriodoAnterior = acumulado comparable; TrimestreActual/TrimestreAnterior = solo el trimestre. SaldoInicialTerceraColumna = apertura IFRS cuando se informa. Filtrar el contexto antes de agregar.",
    ),
    "fecha_inicio_contexto": (
        "Fecha",
        "Inicio declarado del contexto. Para el saldo de apertura, la única fecha del XML.",
    ),
    "fecha_fin_contexto": (
        "Fecha",
        "Corte/fin declarado de las cifras; en apertura es el mismo instante de FechaInicio.",
    ),
    "tipo_periodo": (
        "Dimensión",
        "saldo, acumulado o trimestre; evita confundir stocks y flujos.",
    ),
    "seccion": (
        "Dimensión",
        "Rubro del estado: corriente/no corriente, patrimonio, ingresos, gastos u otros integrales.",
    ),
    "tipo_linea": ("Dimensión", "detalle o total. No sumar detalles con sus totales."),
    "orden": (
        "Atributo",
        "Orden de presentación de la cuenta en la ficha CMF, dentro de cada tabla/contexto.",
    ),
    "codigo_cuenta": (
        "PK",
        "Código FIEF literal. La clave de fila es periodo + run_fondo + contexto + codigo_cuenta.",
    ),
    "cuenta": (
        "Dimensión",
        "Glosa del modelo CMF. TotalPasivo se explicita como pasivo más patrimonio.",
    ),
    "nota": (
        "Atributo",
        "Referencia a nota del XML, si existe. No se extrae su texto PDF.",
    ),
    "valor_miles_mf": (
        "Métrica",
        "Entero exacto del XML, en miles de su moneda. No convertido, redondeado ni rellenado. No sumar contextos.",
    ),
    "fuente_archivo": (
        "Dato fuente",
        "Nombre del FIEF original; la URL se reconstruye con RUN, período y la ruta CMF fiifr/xml.",
    ),
    "enviado_cmf": (
        "Fecha",
        "Fecha/hora de envío leída del nombre del archivo; hora local declarada, sin inventar zona.",
    ),
    "sha256_archivo": (
        "Dato fuente",
        "SHA-256 de los bytes originales del XML descargado.",
    ),
    "cotejo_ficha": (
        "Atributo",
        "coincide = importe cotejado exactamente con su concepto y columna HTML. sin_columna = contexto del XML no expuesto por la ficha (por ejemplo trimestres en el cierre anual), validado contablemente pero no cotejable allí.",
    ),
}


def _js(obj):
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    return re.sub(r'(?m)^(\s*)"([A-Za-z_]\w*)":', r"\1\2:", s)


def bloque(texto, marca, contenido):
    inicio, fin = f"// BEGIN AUTO FI EEFF {marca}", f"// END AUTO FI EEFF {marca}"
    if texto.count(inicio) != 1 or texto.count(fin) != 1:
        raise ValueError(f"bloque FI EEFF {marca} ausente o repetido")
    a, b = texto.index(inicio) + len(inicio), texto.index(fin)
    return texto[:a] + "\n" + contenido + "\n  " + texto[b:]


def consultas(tabla):
    if tabla == "balance":
        return [
            {
                "label": "Mayores patrimonios en pesos, último cierre (MM$)",
                "query": "SELECT run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS patrimonio_mm FROM fi_balance WHERE contexto = 'PeriodoActual' AND codigo_cuenta = 'TotalPatrimonioNeto' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM fi_balance) ORDER BY valor_miles_mf DESC LIMIT 20;",
            },
            {
                "label": "Balance actual del mayor fondo en pesos, último cierre",
                "query": "SELECT periodo, nombre_fondo, orden, seccion, cuenta, valor_miles_mf FROM fi_balance WHERE contexto = 'PeriodoActual' AND periodo = (SELECT max(periodo) FROM fi_balance) AND run_fondo = (SELECT run_fondo FROM fi_balance WHERE contexto = 'PeriodoActual' AND moneda = 'CLP' AND codigo_cuenta = 'TotalPatrimonioNeto' AND periodo = (SELECT max(periodo) FROM fi_balance) ORDER BY valor_miles_mf DESC LIMIT 1) ORDER BY orden;",
            },
            {
                "label": "Cobertura de balances por cierre y contexto",
                "query": "SELECT periodo, contexto, moneda, count(DISTINCT run_fondo) AS fondos FROM fi_balance GROUP BY periodo, contexto, moneda ORDER BY periodo DESC, contexto, moneda;",
            },
        ]
    return [
        {
            "label": "Mayores resultados acumulados en pesos, último cierre (MM$)",
            "query": "SELECT run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS resultado_mm FROM fi_resultados WHERE contexto = 'PeriodoActual' AND codigo_cuenta = 'ResultadoDelEjercicio' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM fi_resultados) ORDER BY valor_miles_mf DESC LIMIT 20;",
        },
        {
            "label": "Resultado SOLO del trimestre en pesos, según XML (MM$)",
            "query": "SELECT periodo, run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS resultado_trimestre_mm, cotejo_ficha FROM fi_resultados WHERE contexto = 'TrimestreActual' AND codigo_cuenta = 'ResultadoDelEjercicio' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM fi_resultados) ORDER BY valor_miles_mf DESC LIMIT 20;",
        },
        {
            "label": "Comisiones acumuladas por cierre y moneda, sin mezclar contextos",
            "query": "SELECT periodo, moneda, count(DISTINCT run_fondo) AS fondos, -sum(valor_miles_mf) AS comision_miles_moneda FROM fi_resultados WHERE contexto = 'PeriodoActual' AND codigo_cuenta = 'ComisionDeAdministracion' GROUP BY periodo, moneda ORDER BY periodo DESC, moneda;",
        },
    ]


def actualizar_catalogos(raiz=RAIZ, salida=None):
    raiz = Path(raiz)
    salida = Path(salida) if salida is not None else raiz / "docs/outputs/fi"
    manifests = {}
    for t in ("balance", "resultados"):
        p = salida / f"fi_{t}/manifest.json"
        if not p.exists():
            return False
        m = json.loads(p.read_text(encoding="utf-8"))
        if not m["periodos"] or not m["total_records"]:
            return False
        if any(not (raiz / "docs" / f).is_file() for f in m["files"]):
            raise ValueError("manifiesto FI apunta a particiones ausentes")
        manifests[t] = m
    if manifests["balance"]["periodos"] != manifests["resultados"]["periodos"]:
        raise ValueError("períodos distintos entre las dos tablas FI")
    vocabp = raiz / "docs/vocabulario.json"
    vocab = json.loads(vocabp.read_text(encoding="utf-8"))
    for t in manifests:
        tid = f"fi_{t}"
        if not any(v["id"] == tid for v in vocab["tablas"]):
            vocab["tablas"].append(
                {
                    "id": tid,
                    "alias": [],
                    "nombre": f"fi.{t}",
                    "tipo": t,
                    "sector": "fi",
                    "descripcion": DESCRIPCIONES[t],
                    "cobertura": COBERTURA,
                }
            )
    porid = {v["id"]: v for v in vocab["tablas"]}
    views, viewer, dictionary, navigation, erd, links, entradas = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for i, (t, m) in enumerate(manifests.items()):
        tid, nombre = f"fi_{t}", porid[f"fi_{t}"]["nombre"]
        ruta = f"outputs/fi/fi_{t}/manifest.json"
        per, fecha = m["periodos"], m["updated_at"][:10]
        descripcion = (
            DESCRIPCIONES[t]
            + " Solo se publican contextos completos y que cuadran. Los comparativos rechazados/ausentes se declaran en el manifiesto, no se rellenan con ceros."
        )
        columnas = [
            {
                "name": c,
                "type": "BIGINT"
                if c == "valor_miles_mf"
                else "INTEGER"
                if c == "orden"
                else "VARCHAR",
                "role": DEFINICIONES[c][0],
                "significado": DEFINICIONES[c][1],
                "contable": "Valor contable" if c == "valor_miles_mf" else "No aplica",
            }
            for c in xml.COLUMNAS
        ]
        views.append(f'  {{ name: "{tid}", manifest: "{ruta}" }},')
        viewer.append(
            _js(
                {
                    "id": tid,
                    "name": nombre,
                    "detalle": "Balance trimestral"
                    if t == "balance"
                    else "Estado de resultados trimestral",
                    "descripcion": descripcion,
                }
            )
            + ","
        )
        dictionary.append(
            _js(
                {
                    "id": tid,
                    "name": nombre,
                    "viewName": tid,
                    "sector": "fi",
                    "sectorLabel": vocab["sectores"]["fi"],
                    "norma": "IFRS · XML CMF FIEF (Circular 1998)",
                    "corte": f"{per[0]} a {per[-1]} · {len(per)} cierres publicados",
                    "frecuencia": "Trimestral",
                    "frescura": "Se actualiza sola 3 veces al mes",
                    "modo": "Automático · incremental; identidades y cotejo antes de publicar",
                    "ultimaActualizacion": fecha,
                    "registros": COBERTURA,
                    "origen": ORIGEN,
                    "descripcion": descripcion,
                    "advertencia": "El archivo puede traer varios contextos para la misma cuenta. Elegir PeriodoActual para el saldo/acumulado actual; no sumar contextos ni monedas. sin_columna no significa cotejado contra HTML. Las exclusiones y huecos están en fi_eeff_control.json y manifest.json.",
                    "columnas": columnas,
                }
            )
            + ","
        )
        navigation.append(
            _js(
                {
                    "id": f"cat_{tid}",
                    "type": "circular",
                    "label": "Balance trimestral IFRS · CMF"
                    if t == "balance"
                    else "Estado de Resultados trimestral IFRS · CMF",
                    "badge": f"{len(per)} cierres validados",
                    "badgeType": "data",
                    "status": "active",
                    "sector": "fi",
                    "chips": consultas(t),
                    "tables": [
                        {
                            "id": tid,
                            "name": nombre,
                            "rows": COBERTURA,
                            "file": "",
                            "files": [ruta],
                        }
                    ],
                }
            )
            + ","
        )
        # Nodo resumido: el diccionario permite ver las 25 columnas completas.
        erd.append(
            _js(
                {
                    "id": tid,
                    "name": nombre,
                    "sector": "fi",
                    "color": "var(--accent-mint)",
                    "x": 1620 + i * 300,
                    "y": 850,
                    "w": 270,
                    "h": 248,
                    "rows": COBERTURA,
                    "file": ruta,
                    "cols": [
                        {"name": "periodo", "pk": True, "type": "VARCHAR"},
                        {"name": "run_fondo", "fk": True, "type": "VARCHAR"},
                        {"name": "contexto", "pk": True, "type": "VARCHAR"},
                        {"name": "codigo_cuenta", "pk": True, "type": "VARCHAR"},
                        {"name": "rut_agf", "fk": True, "type": "VARCHAR"},
                        {"name": "moneda", "type": "VARCHAR"},
                        {"name": "valor_miles_mf", "type": "BIGINT"},
                    ],
                }
            )
            + ","
        )
        links += [
            f'  {{ from: "fi_lista_entidades", to: "{tid}", key: "run_fondo" }},',
            f'  {{ from: "agf_lista_entidades", to: "{tid}", key: "rut = rut_agf" }},',
        ]
        entradas.append(
            {
                "id": tid,
                "name": nombre,
                "view_name": tid,
                "sector": "fi",
                "sector_label": "Fondos de Inversión",
                "norma": "IFRS · XML CMF (Circular 1998)",
                "corte": f"{per[0]} a {per[-1]}",
                "frescura": f"Último cierre: {per[-1]}",
                "modo": "Automático · 3 veces al mes, incremental",
                "ultima_actualizacion": fecha,
                "file_parquet": ruta,
                "registros_reales": m["total_records"],
                "descripcion": descripcion,
                "origen": ORIGEN,
            }
        )
    contenidos = {
        "duckdb_client.js": "\n".join(views),
        "data_viewer.js": "\n".join(viewer),
        "data_dictionary.js": "\n".join(dictionary),
        "sidebar.js": "\n".join(navigation),
    }
    nuevos = {}
    for name, contenido in contenidos.items():
        p = raiz / "docs/js" / name
        nuevos[p] = bloque(p.read_text(encoding="utf-8"), MARCAS[name], contenido)
    erdp = raiz / "docs/js/erd_graph.js"
    nuevos[erdp] = bloque(
        bloque(erdp.read_text(encoding="utf-8"), "ERD", "\n".join(erd)),
        "LINKS",
        "\n".join(links),
    )
    mp = raiz / "data_manifest.json"
    man = json.loads(mp.read_text(encoding="utf-8"))
    quitar = {e["id"] for e in entradas}
    man["tables"] = [t for t in man["tables"] if t["id"] not in quitar] + entradas
    man.update(
        total_tables=len(man["tables"]),
        total_records=sum(int(t.get("registros_reales") or 0) for t in man["tables"]),
        updated_at=manifests["balance"]["updated_at"][:10],
    )
    # El inventario registra tablas realmente publicadas, no promesas de carga.
    invp = raiz / "pipelines/auto/inventario.json"
    if invp.exists():
        inv = json.loads(invp.read_text(encoding="utf-8"))
        for tid in ("fi_balance", "fi_resultados"):
            inv["tablas"][tid] = {"workflow": "fi_eeff.yml"}
        inv["tablas"] = dict(sorted(inv["tablas"].items()))
    # Todos los bloques se comprueban ANTES de modificar archivos compartidos.
    if invp.exists():
        estable.escribir_json(invp, inv)
    estable.escribir_json(vocabp, vocab)
    estable.escribir_json(mp, man)
    cambiaron = False
    for p, texto in nuevos.items():
        if p.read_text(encoding="utf-8") != texto:
            p.write_text(texto, encoding="utf-8")
            cambiaron = True
    if cambiaron:
        indexp = raiz / "docs/index.html"
        if indexp.exists():
            token = hashlib.sha256("".join(nuevos.values()).encode()).hexdigest()[:12]
            index = indexp.read_text(encoding="utf-8")
            index = re.sub(
                r'(src="js/(?:duckdb_client|data_viewer|data_dictionary|sidebar|erd_graph)\.js\?v=)[^\"]*',
                lambda m: m.group(1) + "fi-eeff-" + token,
                index,
            )
            indexp.write_text(index, encoding="utf-8")
    return cambiaron


if __name__ == "__main__":
    actualizar_catalogos()
