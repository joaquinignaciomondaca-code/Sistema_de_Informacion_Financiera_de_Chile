"""Vista previa local de docs/ sin caché de navegador ni intermediarios.

Uso: python -m scripts.preview_no_cache --port 8000
No publica datos ni cambia el sitio desplegado.

Soporta peticiones HTTP Range (un solo rango), igual que GitHub Pages: DuckDB-Wasm
lee los Parquet por trozos (pie de archivo + grupos de filas) y, sin Range, cada
consulta descargaría el archivo completo (algunos superan 70 MB).
"""
import os
import re
from argparse import ArgumentParser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)$")


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        self._range = None
        header = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not header or not os.path.isfile(path):
            return super().send_head()
        match = RANGE_RE.match(header.strip())
        size = os.path.getsize(path)
        if not match or (not match.group(1) and not match.group(2)):
            return super().send_head()  # rango múltiple o mal formado: respuesta completa
        if match.group(1):
            start = int(match.group(1))
            end = min(int(match.group(2)), size - 1) if match.group(2) else size - 1
        else:  # sufijo: últimos N bytes
            start, end = max(size - int(match.group(2)), 0), size - 1
        if start >= size or start > end:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        handle = open(path, "rb")
        handle.seek(start)
        self._range = end - start + 1
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self._range))
        self.end_headers()
        return handle

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_range", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    docs = Path(__file__).resolve().parents[1] / "docs"
    with ThreadingHTTPServer(("0.0.0.0", args.port), partial(NoCacheHandler, directory=str(docs))) as server:
        print(f"Vista previa sin caché en 0.0.0.0:{args.port} ({docs})", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
