// Diagnóstico reproducible del motor DuckDB-Wasm en un navegador headless.
//
// Uso (desde la raíz del repo, con el sitio servido en http://127.0.0.1:8080/):
//   npm install --no-save puppeteer-core @sparticuz/chromium
//   node scripts/diagnostico_motor_sql.mjs [url] [timeoutSegundos]
//
// Para cada escenario mide cuánto tarda en quedar listo (window.DuckDBClient.isReady)
// y qué estado deja el motor. Escenarios:
//   normal      - todo disponible.
//   sin_mjs     - falla la copia local del módulo y los CDN (fallo rápido esperado).
//   worker_404  - el worker del motor responde 404 (esperado: sin error, puede colgarse).
//   wasm_404    - el .wasm responde 404 (esperado: sin error, puede colgarse).
// Los CDN externos se bloquean en todos los escenarios para que la prueba sea determinista.
//
// Nota: en algunos hosts Linux sin librerías del sistema, @sparticuz/chromium necesita
// LD_LIBRARY_PATH apuntando a sus propias librerías; ver docs/notas/diagnostico_motor_sql_2026-10-20.md.

import puppeteer from "puppeteer-core";
import chromium from "@sparticuz/chromium";

const url = process.argv[2] || "http://127.0.0.1:8080/index.html";
const timeoutS = Number(process.argv[3] || 30);

const ESCENARIOS = {
  normal: () => null,
  sin_mjs: (u) => (u.includes("vendor/duckdb/duckdb-browser.mjs") ? { status: 404, body: "nf" } : null),
  worker_404: (u) => (u.includes("duckdb-browser-eh.worker.js") ? { status: 404, body: "nf" } : null),
  wasm_404: (u) => (u.includes("duckdb-eh.wasm") ? { status: 404, body: "nf" } : null),
};

async function correr(nombre, reglaFalla) {
  const browser = await puppeteer.launch({
    executablePath: await chromium.executablePath(),
    args: chromium.args,
    headless: true,
  });
  try {
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on("request", (r) => {
      const u = r.url();
      if (u.includes("cdn.jsdelivr.net") || u.includes("esm.sh")) return r.abort("failed");
      const falla = reglaFalla(u);
      if (falla) return r.respond(falla);
      return r.continue();
    });
    const t0 = Date.now();
    await page.goto(url, { waitUntil: "load" });
    const tLoad = Date.now() - t0;
    let listo = true;
    await page
      .waitForFunction(() => window.DuckDBClient && window.DuckDBClient.isReady, {
        timeout: timeoutS * 1000,
        polling: 100,
      })
      .catch(() => { listo = false; });
    const tListo = Date.now() - t0;
    const estado = await page.evaluate(() => {
      const c = window.DuckDBClient || {};
      return {
        engineAvailable: c.engineAvailable ?? null,
        engineSource: c.engineSource ?? null,
        engineError: c.engineError ?? null,
        attempts: (c.attempts || []).map((a) => `${a.label}: ${a.error}`),
        views: c.registeredFiles ? c.registeredFiles.size : null,
      };
    });
    let consulta = null;
    if (estado.engineAvailable) {
      consulta = await page.evaluate(async () => {
        const t = performance.now();
        const r = await window.DuckDBClient.query("SELECT count(*) AS n FROM seguros_lista_entidades");
        return { ok: r.success, filas: r.rows && r.rows[0] ? r.rows[0].n : null, ms: Math.round(performance.now() - t) };
      });
    }
    return { escenario: nombre, listo, tLoadMs: tLoad, tListoMs: listo ? tListo : null, estado, consulta };
  } finally {
    await browser.close();
  }
}

const resultados = [];
for (const [nombre, regla] of Object.entries(ESCENARIOS)) {
  resultados.push(await correr(nombre, regla));
}
console.log(JSON.stringify(resultados, null, 2));
