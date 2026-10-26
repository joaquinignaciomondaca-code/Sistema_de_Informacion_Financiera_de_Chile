#!/usr/bin/env node
"use strict";

/**
 * Contrasta las fuentes primarias del catálogo API con el campo `origen` del
 * diccionario visible en la web. Es una comprobación de atribución editorial,
 * no una auditoría de condiciones legales ni prueba de que el proveedor sea la
 * única entidad mencionada en el texto.
 *
 * Uso:
 *   node scripts/audit_fuentes_publicadas.js
 *   node scripts/audit_fuentes_publicadas.js --autoprueba
 */
const fs = require("node:fs");
const path = require("node:path");
const { leerDiccionario } = require("./lib/data_dictionary");

const ROOT = path.resolve(__dirname, "..");
const FUENTES = {
  CMF: /\bCMF\b|Comisión para el Mercado Financiero/i,
  BCCh: /\bBCCh\b|Banco Central/i,
  SPensiones: /\bSPensiones\b|Superintendencia de Pensiones/i,
};

function leerJson(relativo) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relativo), "utf8"));
}

function auditar(catalogo, diccionario) {
  const errores = [];
  const objetos = catalogo?.objetos;
  if (!Array.isArray(objetos)) return ["catalog.json no contiene la lista objetos"];
  if (!Array.isArray(diccionario)) return ["DATA_DICTIONARY no es una lista"];

  const idsApi = objetos.map((objeto) => objeto?.id).filter(Boolean);
  const idsWeb = diccionario.map((objeto) => objeto?.id).filter(Boolean);
  const duplicados = (ids) => [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))].sort();
  const duplicadosApi = duplicados(idsApi);
  const duplicadosWeb = duplicados(idsWeb);
  if (duplicadosApi.length) errores.push(`IDs duplicados en API: ${duplicadosApi.join(", ")}`);
  if (duplicadosWeb.length) errores.push(`IDs duplicados en el diccionario web: ${duplicadosWeb.join(", ")}`);

  const apiPorId = new Map(objetos.map((objeto) => [objeto.id, objeto]));
  const webPorId = new Map(diccionario.map((objeto) => [objeto.id, objeto]));
  const faltanEnWeb = [...apiPorId.keys()].filter((id) => !webPorId.has(id)).sort();
  const sobranEnWeb = [...webPorId.keys()].filter((id) => !apiPorId.has(id)).sort();
  if (faltanEnWeb.length || sobranEnWeb.length) {
    errores.push(`IDs API/diccionario distintos: faltan=${faltanEnWeb.join(",")}; sobran=${sobranEnWeb.join(",")}`);
  }

  for (const [id, api] of apiPorId) {
    const web = webPorId.get(id);
    if (!web) continue;
    const fuente = String(api.fuente || "").trim();
    const patron = FUENTES[fuente];
    if (!patron) {
      errores.push(`${id}: fuente API no reconocida por la auditoría (${fuente || "vacía"})`);
      continue;
    }
    if (!String(web.origen || "").trim()) {
      errores.push(`${id}: el diccionario web no declara origen`);
    } else if (!patron.test(web.origen)) {
      errores.push(`${id}: origen web no identifica la fuente API ${fuente}`);
    }
  }
  return errores;
}

function main() {
  const catalogo = leerJson("docs/api/v2/catalog.json");
  const diccionario = leerDiccionario(ROOT);
  const errores = auditar(catalogo, diccionario);

  if (process.argv.includes("--autoprueba")) {
    const mutado = diccionario.map((objeto) => ({ ...objeto }));
    const primero = mutado.find((objeto) => catalogo.objetos.some((api) => api.id === objeto.id));
    if (!primero) throw new Error("autoprueba sin objeto para mutar");
    const idMutado = primero.id;
    primero.origen = "Fuente retirada para autoprueba";
    const detectaDeriva = auditar(catalogo, mutado).some((error) => error.startsWith(`${idMutado}:`));
    if (!detectaDeriva) {
      console.error("FALLA AUTOPRUEBA: no detectó la fuente alterada");
      return 1;
    }
    console.log(`OK AUTOPRUEBA: detecta deriva de fuente en ${idMutado}`);
  }

  if (errores.length) {
    for (const error of errores) console.error(`FALLA: ${error}`);
    return 1;
  }
  console.log(
    `FUENTES WEB OK: ${catalogo.objetos.length} IDs API alineados con ` +
    `${diccionario.length} entradas del diccionario y su fuente primaria`
  );
  return 0;
}

try {
  process.exitCode = main();
} catch (error) {
  console.error(`FALLA: ${error.message}`);
  process.exitCode = 1;
}
