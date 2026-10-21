// Sirve docs/ en local aproximando el hosting público (Vercel / GitHub Pages):
//   * soporte de peticiones de rango (206 Partial Content), que DuckDB usa para leer Parquet;
//     http.server de Python no lo tiene y hace que DuckDB caiga a "full HTTP read";
//   * compresión gzip para texto, JS y WebAssembly (el hosting público comprime estos tipos);
//   * las cabeceras de docs/vercel.json (Cache-Control: no-store para outputs/*.parquet).
//
// Uso: node scripts/servir_sitio_local.mjs [puerto=8080] [host=0.0.0.0]
// No tiene dependencias. Es una aproximación: el hosting real puede diferir en compresión y caché.

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "docs");
const PUERTO = Number(process.argv[2] || 8080);
const HOST = process.argv[3] || "0.0.0.0";

const TIPOS = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".wasm": "application/wasm",
  ".parquet": "application/vnd.apache.parquet",
  ".csv": "text/csv; charset=utf-8",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
};
const COMPRIMIBLES = new Set([".html", ".js", ".mjs", ".css", ".json", ".svg", ".txt", ".md", ".wasm", ".csv"]);

// Equivalente a docs/vercel.json.
function cabecerasExtra(archivo) {
  if (/[\\/]outputs[\\/].*\.parquet$/.test(archivo)) return { "Cache-Control": "no-store" };
  return {};
}

function resolverArchivo(urlPath) {
  let p = decodeURIComponent(new URL(urlPath, "http://x").pathname);
  if (p.endsWith("/")) p += "index.html";
  const archivo = path.normalize(path.join(RAIZ, p));
  if (!archivo.startsWith(RAIZ)) return null;
  if (fs.existsSync(archivo) && fs.statSync(archivo).isDirectory()) return path.join(archivo, "index.html");
  return archivo;
}

const servidor = http.createServer((req, res) => {
  const archivo = resolverArchivo(req.url);
  if (!archivo || !fs.existsSync(archivo) || !fs.statSync(archivo).isFile()) {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("404 no encontrado");
    return;
  }
  const ext = path.extname(archivo).toLowerCase();
  const tipo = TIPOS[ext] || "application/octet-stream";
  const tam = fs.statSync(archivo).size;
  const base = { "Content-Type": tipo, "Accept-Ranges": "bytes", ...cabecerasExtra(archivo) };

  const rango = req.headers.range && /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
  if (rango && req.method !== "HEAD") {
    let ini = rango[1] === "" ? tam - Number(rango[2]) : Number(rango[1]);
    let fin = rango[2] === "" || rango[1] === "" ? tam - 1 : Number(rango[2]);
    if (ini < 0 || ini >= tam || fin < ini) {
      res.writeHead(416, { "Content-Range": `bytes */${tam}` });
      res.end();
      return;
    }
    fin = Math.min(fin, tam - 1);
    res.writeHead(206, { ...base, "Content-Range": `bytes ${ini}-${fin}/${tam}`, "Content-Length": fin - ini + 1 });
    fs.createReadStream(archivo, { start: ini, end: fin }).pipe(res);
    return;
  }

  const aceptaGzip = /\bgzip\b/.test(req.headers["accept-encoding"] || "");
  if (aceptaGzip && COMPRIMIBLES.has(ext) && tam > 1024 && req.method !== "HEAD") {
    res.writeHead(200, { ...base, "Content-Encoding": "gzip", Vary: "Accept-Encoding" });
    fs.createReadStream(archivo).pipe(zlib.createGzip({ level: 6 })).pipe(res);
    return;
  }
  res.writeHead(200, { ...base, "Content-Length": tam });
  if (req.method === "HEAD") return res.end();
  fs.createReadStream(archivo).pipe(res);
});

servidor.listen(PUERTO, HOST, () => {
  console.log(`Sitio local en http://${HOST}:${PUERTO}/ (raíz: docs/)`);
});
