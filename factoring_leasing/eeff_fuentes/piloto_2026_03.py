"""Diez EEFF de factoring, marzo 2026, leídos del PDF de Información Financiera.

No es la visualización HTML ni ver_archivo.php. Si una línea no salió del PDF,
no está aquí. Tanner y Eurocapital quedan parciales: el recorte a 30 páginas
no alcanzó el desglose de notas, y la carátula completa de Tanner no se
releyó. Las notas con montos confirmados son solo Security, Nota 4 y Nota 5.
"""

from pathlib import Path

PERIODO = "2026-03"
FECHA = "2026-03-31"
FUENTE = "CMF PDF Estados financieros (Informacion Financiera, pestania=3)"


def _url(auth, send):
    return (
        "https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs/safec_ifrs_verarchivo.php"
        f"?auth={auth}&send={send}"
    )


def _ficha(rut, tipo):
    cuerpo = rut.split("-")[0]
    return (
        "https://www.cmfchile.cl/institucional/mercados/entidad.php"
        f"?mercado=V&rut={cuerpo}&grupo=&tipoentidad=RVEMI&vig=VI&control=svs"
        f"&pestania=3&mm=03&aa=2026&tipo={tipo}&tipo_norma=IFRS"
    )


PILOTO = []
