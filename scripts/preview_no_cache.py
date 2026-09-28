"""Vista previa local de docs/ sin caché de navegador ni intermediarios.

Uso: python -m scripts.preview_no_cache --port 8000
No publica datos ni cambia el sitio desplegado.
"""
from argparse import ArgumentParser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


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
