"""Descarga el PDF del EEFF desde el buscador de Información Financiera (CMF).

La pista ya estaba en el repo y no se usaba:

- factoring_leasing/scripts/02_extract_factoring_leasing_notas_series.py
  `fetch_cmf_pdf_stream`: POST a pestania=3 con el formulario
  mm / aa / tipo / tipo_norma=IFRS y el enlace
  «Estados financieros (PDF)». Si no hay consolidado, reintenta individual.
- ccaf/scripts/pipeline_extract_ccaf_xbrl.py
  el href real vive en safec_ifrs_verarchivo.php.
- securitizadoras/scripts/stream_cmf_securitizadoras.py
  y retail/agf: la misma ficha, con tipo=I y si no hay [210000], tipo=C.
- corredoras_bolsa/scripts/02_extract_corredoras_eeff_repos.py
  el buscador es un POST aa/mm sobre pestania=3.

El PDF se escribe en un temporal y se borra al convertir a Markdown.
La API ver_archivo.php no entra aquí: eso es solo validación.
"""

from __future__ import annotations

import os
import re
import ssl
import tempfile
import time
import urllib.parse
import urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

PDF_LINK = re.compile(
    r'href=["\']([^"\']*safec_ifrs_verarchivo\.php[^"\']*)["\'][^>]*>\s*Estados financieros \(PDF\)',
    re.IGNORECASE,
)


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def url_informacion_financiera(rut_cuerpo: str, tipoentidad: str = "RVEMI") -> str:
    """Ficha CMF, pestaña Información Financiera (pestania=3)."""
    return (
        "https://www.cmfchile.cl/institucional/mercados/entidad.php"
        f"?mercado=V&rut={rut_cuerpo}&grupo=&tipoentidad={tipoentidad}"
        "&vig=VI&control=svs&pestania=3"
    )


ultimo_error = ""


def _leer(req: urllib.request.Request, timeout: int, intentos: int = 3) -> bytes | None:
    """Reintenta un corte de TLS. CMF a veces cierra el primer intento."""
    global ultimo_error
    ultimo = ""
    for n in range(intentos):
        try:
            with urllib.request.urlopen(req, context=_ssl_context(), timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            ultimo = f"{type(exc).__name__}: {exc}"
            ultimo_error = ultimo
            if n + 1 < intentos:
                time.sleep(2 * (n + 1))
    ultimo_error = ultimo or "sin respuesta"
    return None


def buscar_periodo(rut_cuerpo: str, year: int, month: int, tipo: str = "C", tipoentidad: str = "RVEMI") -> str | None:
    """Envía el buscador de periodos (Consolidado o Individual, IFRS)."""
    global ultimo_error
    url = url_informacion_financiera(rut_cuerpo, tipoentidad)
    data = urllib.parse.urlencode({
        "forma": "F",
        "mm": f"{int(month):02d}",
        "aa": str(year),
        "tipo": tipo,
        "tipo_norma": "IFRS",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    raw = _leer(req, timeout=30)
    if raw is None:
        return None
    html = raw.decode("latin-1", errors="ignore")
    if "No existe información" in html and "Estados financieros (PDF)" not in html:
        ultimo_error = f"CMF sin información {year}-{int(month):02d} tipo {tipo}"
        return None
    return html


def url_pdf_desde_html(html: str) -> str | None:
    match = PDF_LINK.search(html or "")
    if not match:
        return None
    href = match.group(1).replace("&amp;", "&")
    return urllib.parse.urljoin("https://www.cmfchile.cl/institucional/mercados/", href)


def descargar_pdf(rut_cuerpo: str, year: int, month: int, tipoentidad: str = "RVEMI", preferir: str = "C") -> tuple[bytes | None, str, str]:
    """Consolidado primero, salvo que la ficha ya conocida sea individual.

    Devuelve (bytes, tipo_usado, url_pdf).
    """
    orden = ("I", "C") if preferir == "I" else ("C", "I")
    for tipo in orden:
        html = buscar_periodo(rut_cuerpo, year, month, tipo, tipoentidad)
        if not html:
            continue
        pdf_url = url_pdf_desde_html(html)
        if not pdf_url:
            continue
        req = urllib.request.Request(pdf_url, headers={**HEADERS, "Referer": url_informacion_financiera(rut_cuerpo, tipoentidad)})
        blob = _leer(req, timeout=60)
        if not blob:
            continue
        if blob[:4] == b"%PDF" or len(blob) > 1000:
            return blob, ("Consolidado" if tipo == "C" else "Individual"), pdf_url
    return None, "", ""


def pdf_a_markdown(pdf_bytes: bytes) -> str:
    """Convierte el PDF en memoria. El archivo temporal se borra siempre."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(pdf_bytes)
        try:
            import pymupdf4llm
            return pymupdf4llm.to_markdown(path)
        except Exception:
            pass
        try:
            import fitz
            doc = fitz.open(path)
            partes = []
            for page in doc:
                partes.append(page.get_text("text"))
            doc.close()
            return "\n\n".join(partes)
        except Exception:
            pass
        import pdfplumber
        partes = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                partes.append(page.extract_text() or "")
        return "\n\n".join(partes)
    finally:
        if os.path.exists(path):
            os.remove(path)
