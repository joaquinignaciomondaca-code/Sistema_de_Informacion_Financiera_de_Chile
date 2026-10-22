"""Procedencia, atribución y condiciones de uso de las fuentes publicadas.

Las tres fuentes que alimentan este sistema autorizan la republicación con una
condición común: **citar**. No piden autorización escrita, ni limitan el uso a
investigación. La única restricción fuerte detectada —«uso exclusivo para fines
de investigación, se solicita no distribuir»— está en el manual de la Base de
Cartera de los Fondos de Pensiones de la Superintendencia de Pensiones, y esa
base no se publica.

Este módulo centraliza el texto de la cita y el estado de la verificación para
que el catálogo, el descriptor Data Package, los esquemas y el sitio digan lo
mismo. Un texto escrito dos veces termina diciendo dos cosas.

Referencias verificadas el 2026-10-22:

* CMF, Descargo de Responsabilidades: «autoriza la reproducción total o parcial
  de la información contenida en este Website, siempre y cuando se mencione la
  fuente».
* BCCh, Términos y Condiciones de la API BDE: «Está permitido consultar,
  reproducir, difundir, publicar o adaptar la información contenida en la BDE,
  mencionando en todo momento que ella es propiedad del Banco». Las
  adaptaciones, además, deben declararse como propias de quien las realiza.
* SPensiones, Descargo de responsabilidades del sitio: «autoriza la utilización
  o reproducción total o parcial de la información contenida en este sitio, en
  citas o comentarios indicando su fuente».

Uso:

    from pipelines.api import fuentes as F
    F.fuente_de("macro")                      # "BCCh"
    F.atribucion_de("macro")["cita"]          # texto listo para publicar
    F.atribucion_de("macro", "macro_inflacion_implicita")["adaptacion"]  # True
"""
from __future__ import annotations

# Fuente por sector del contrato. El manifiesto ya declara el origen de cada
# tabla y coincide con este mapa en los 90 objetos (comprobado en la
# regeneración del 2026-10-22); el mapa existe para no depender de una cadena de
# texto libre cuando el manifiesto venga incompleto.
SECTOR_FUENTE = {
    "macro": "BCCh",
    "pensiones": "SPensiones",
}
FUENTE_POR_DEFECTO = "CMF"

FUENTES = {
    "CMF": {
        "titulo": "CMF — Comisión para el Mercado Financiero",
        "url": "https://www.cmfchile.cl",
        "url_terminos": "https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html",
        "documento": "Descargo de Responsabilidades",
        "cita": (
            "Fuente: Comisión para el Mercado Financiero (CMF). "
            "Reproducción autorizada citando la fuente."
        ),
        "condicion": "Mencionar la fuente en toda reproducción, total o parcial.",
        "estado": "verificada",
        "verificada": "2026-10-22",
    },
    "BCCh": {
        "titulo": "BCCh — Banco Central de Chile",
        "url": "https://si3.bcentral.cl",
        "url_terminos": "https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/terms_es.htm",
        "documento": "Términos y Condiciones de Uso de la API BDE",
        "cita": (
            "Fuente: Banco Central de Chile (Base de Datos Estadísticos). "
            "La información es propiedad del Banco Central de Chile."
        ),
        "condicion": (
            "Mencionar que la información es propiedad del Banco; las adaptaciones "
            "deben declararse como propias de quien las realiza; máximo 5 series "
            "simultáneas por segundo."
        ),
        "estado": "verificada",
        "verificada": "2026-10-22",
        "nota_adaptacion": (
            "Adaptación de elaboración propia sobre series del Banco Central de Chile; "
            "la adaptación es propiedad y responsabilidad exclusiva de este proyecto."
        ),
    },
    "SPensiones": {
        "titulo": "SPensiones — Superintendencia de Pensiones",
        "url": "https://www.spensiones.cl",
        "url_terminos": "https://www.spensiones.cl/portal/institucional/594/w3-article-5885.html",
        "documento": "Descargo de responsabilidades",
        "cita": (
            "Fuente: Superintendencia de Pensiones. "
            "Reproducción autorizada citando la fuente."
        ),
        "condicion": (
            "Mencionar la fuente. El alcance es sólo el listado de administradoras: "
            "la Base de Cartera de los Fondos de Pensiones no se publica."
        ),
        "estado": "verificada",
        "verificada": "2026-10-22",
    },
}

# Objetos cuyos valores calcula este proyecto sobre datos de la fuente. El BCCh
# exige que una adaptación publicada se declare como propia de quien la hace.
ADAPTACIONES = {
    "macro_inflacion_implicita": (
        "diferencia propia entre el rendimiento del bono en pesos y el del bono en UF "
        "del mismo plazo, calculada sobre las curvas que publica el Banco Central"
    ),
}


def fuente_de(sector: str | None) -> str:
    """Sigla de la fuente primaria de un sector del contrato."""
    return SECTOR_FUENTE.get(sector or "", FUENTE_POR_DEFECTO)


def atribucion_de(sector: str | None, objeto: str | None = None) -> dict:
    """Ficha de atribución de un objeto: quién es la fuente y cómo se cita.

    Devuelve un diccionario nuevo en cada llamada (nadie comparte el original) y
    con el campo `adaptacion` resuelto para el objeto concreto.
    """
    sigla = fuente_de(sector)
    ficha = FUENTES[sigla]
    motivo = ADAPTACIONES.get(objeto or "")
    salida = {
        "fuente": sigla,
        "titulo": ficha["titulo"],
        "url": ficha["url"],
        "url_terminos": ficha["url_terminos"],
        "documento": ficha["documento"],
        "cita": ficha["cita"],
        "condicion": ficha["condicion"],
        "estado": ficha["estado"],
        "verificada": ficha["verificada"],
        "adaptacion": bool(motivo),
    }
    if motivo:
        salida["nota_adaptacion"] = (
            f"{ficha['nota_adaptacion']} El cálculo consiste en {motivo}."
            if "nota_adaptacion" in ficha
            else f"Adaptación de elaboración propia: {motivo}."
        )
    return salida
