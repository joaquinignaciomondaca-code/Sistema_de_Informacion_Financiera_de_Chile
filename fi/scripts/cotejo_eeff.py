"""Cotejo determinista FIEF ↔ tablas de balance/resultados de su ficha CMF.

Compara cuentas en su posición/concepto y contexto, no busca cifras en cualquier
columna. La ficha se genera desde el envío CMF: este cotejo confirma la lectura y
presentación, no constituye una auditoría independiente contra el PDF firmado.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from bs4 import BeautifulSoup

from fi.scripts import eeff_xml as xml

TITULOS = {
    "balance": "estado de situacion financiera",
    "resultados": "estado de resultados integrales",
}
COLUMNAS_CTX = {
    "balance": {
        "PeriodoActual": 3,
        "PeriodoAnualAnterior": 4,
        "SaldoInicialTerceraColumna": 5,
    },
    "resultados": {
        "PeriodoActual": 3,
        "PeriodoAnterior": 4,
        "TrimestreActual": 5,
        "TrimestreAnterior": 6,
    },
}
UNIDAD_FICHA = {
    "CLP": "miles de pesos",
    "USD": "miles de dolar",
    "EUR": "miles de euro",
    "COP": "miles de pesos colombianos",
}
GLOSAS_FICHA = {
    "TotalPasivo": "Total pasivo",
    "OtrosIngresosPerdidasDeLaOperacion": "Otros",
    "CambiosNetosEnValorRazonableDeActivosFinancierosYPasivosFinancierosAValorRazonableConEfectoEnResultados": "Cambios netos en valor razonable de activos financieros y pasivos financieros a valor razonable con efecto en resultados",
}


def normalizar(texto):
    s = "".join(
        c
        for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    ).lower()
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.replace("admistracion", "administracion").replace(
        "inversione valorizadas", "inversiones valorizadas"
    )
    return re.sub(r"[^a-z0-9]", "", s)


def numero(txt):
    t = str(txt).strip().replace("\u2212", "-").replace("\xa0", "")
    if t in ("", "-", "—"):
        return None
    if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,0+)?", t):
        raise xml.ErrorFuente(f"importe de ficha no entero/chileno: {txt!r}")
    return int(t.split(",")[0].replace(".", ""))


def cotejar(raw: bytes, reg: dict) -> dict:
    soup = BeautifulSoup(xml.decodificar(raw), "html.parser")
    tablas = {}
    for t in soup.find_all("table"):
        th = [
            c.get_text(" ", strip=True)
            for c in t.find_all("th")
            if c.find_parent("table") is t
        ]
        for tabla, titulo in TITULOS.items():
            if not any(normalizar(x).startswith(normalizar(titulo)) for x in th):
                continue
            if tabla in tablas:
                raise xml.ErrorFuente(f"ficha con dos tablas de {tabla}")
            rows = []
            for tr in t.find_all("tr"):
                if tr.find_parent("table") is not t:
                    continue
                cells = tr.find_all(["td", "th"], recursive=False)
                textos = [c.get_text(" ", strip=True) for c in cells]
                if len(textos) >= 5 and textos[0] == "" and textos[1]:
                    rows.append(textos)
            tablas[tabla] = (th, rows)
    if set(tablas) != set(TITULOS):
        raise xml.ErrorFuente("la ficha no contiene las dos tablas de EEFF esperadas")
    actual = xml.fin_periodo(reg["periodo"]).strftime("%d/%m/%Y")
    verificaciones, sin_columnas = {}, {}
    for tabla, (th, rows) in tablas.items():
        if not any(actual in x for x in th):
            raise xml.ErrorFuente(
                f"{tabla}: fecha de ficha distinta de {reg['periodo']}"
            )
        unidad = UNIDAD_FICHA[reg["moneda"]]
        titulo = next(
            x for x in th if normalizar(x).startswith(normalizar(TITULOS[tabla]))
        )
        # No quitar aquí el paréntesis: contiene la unidad.
        titulo_unidad = "".join(
            c
            for c in unicodedata.normalize("NFKD", titulo.lower())
            if not unicodedata.combining(c)
        )
        if unidad not in " ".join(titulo_unidad.split()):
            raise xml.ErrorFuente(
                f"{tabla}: moneda/escala de ficha no coincide con {reg['moneda']}"
            )
        if len(rows) != len(xml.CATALOGO[tabla]):
            raise xml.ErrorFuente(
                f"{tabla}: ficha con {len(rows)} cuentas, esperadas {len(xml.CATALOGO[tabla])}"
            )
        verificaciones[tabla] = {ctx: 0 for ctx in reg["tablas"][tabla]}
        sin_columnas[tabla] = [
            ctx
            for ctx in reg["tablas"][tabla]
            if all(COLUMNAS_CTX[tabla][ctx] >= len(row) for row in rows)
        ]
        if "PeriodoActual" in sin_columnas[tabla]:
            raise xml.ErrorFuente(f"{tabla}: falta la columna del ejercicio actual")
        for (_, codigo, glosa, _, _), row in zip(xml.CATALOGO[tabla], rows):
            esperado = GLOSAS_FICHA.get(codigo, glosa)
            if normalizar(row[1]) != normalizar(esperado):
                raise xml.ErrorFuente(
                    f"{tabla}/{codigo}: concepto de ficha distinto: {row[1]!r}"
                )
            for ctx, cuentas in reg["tablas"][tabla].items():
                if ctx in sin_columnas[tabla]:
                    continue
                col = COLUMNAS_CTX[tabla][ctx]
                if col >= len(row):
                    raise xml.ErrorFuente(
                        f"{tabla}/{ctx}: falta la columna en la ficha"
                    )
                valor = numero(row[col])
                if valor != cuentas[codigo]:
                    raise xml.ErrorFuente(
                        f"cotejo {tabla}/{ctx}/{codigo}: XML {cuentas[codigo]} ≠ ficha {valor}"
                    )
                verificaciones[tabla][ctx] += 1
    return {
        "estado": "validado",
        "cuentas": verificaciones,
        "sin_columna_en_ficha": sin_columnas,
        "sha256_ficha": hashlib.sha256(raw).hexdigest(),
    }
