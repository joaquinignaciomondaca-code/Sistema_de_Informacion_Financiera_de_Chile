#!/usr/bin/env node
"use strict";

/**
 * Inventaría qué describen los campos de unidad/registro, sin inferir unidades
 * desde filas, nombres de columnas o claves. Los grupos son léxicos y no
 * certifican que la descripción sea cierta en los archivos fuente.
 *
 * Uso:
 *   node scripts/audit_unidad_observacion.js
 *   node scripts/audit_unidad_observacion.js --autoprueba
 */
const fs = require("node:fs");
const path = require("node:path");
const { leerDiccionario } = require("./lib/data_dictionary");

const ROOT = path.resolve(__dirname, "..");
const CATEGORIAS = ["unidad_explicita", "frecuencia_o_formato", "alcance_o_transformacion", "sin_datos", "otros"];

function leerJson(relativo) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relativo), "utf8"));
}

function clasificar(texto) {
  const valor = String(texto || "").trim();
  if (/^una fila por\b/i.test(valor)) return "unidad_explicita";
  if (/^sin datos$/i.test(valor)) return "sin_datos";
  if (/^(mensual|trimestral|anual|serie ifrs|fecu ifrs|balance)\b/i.test(valor)) {
    return "frecuencia_o_formato";
  }
  if (/^(sólo|solo|campos relevantes)\b/i.test(valor)) return "alcance_o_transformacion";
  return "otros";
}

function inventariar(api, manifiesto, diccionario) {
  const errores = [];
  const objetosApi = Array.isArray(api?.objetos) ? api.objetos : [];
  const tablas = Array.isArray(manifiesto?.tables) ? manifiesto.tables : [];
  if (!objetosApi.length) errores.push("catalog.json sin objetos");
  if (!tablas.length) errores.push("data_manifest.json sin tablas");
  if (!Array.isArray(diccionario)) errores.push("diccionario web no es una lista");

  const idsApi = new Set(objetosApi.map((objeto) => objeto.id));
  const idsWeb = new Set((diccionario || []).map((objeto) => objeto.id));
  const idsFaltantes = [...idsApi].filter((id) => !idsWeb.has(id));
  const idsExtra = [...idsWeb].filter((id) => !idsApi.has(id));
  if (idsFaltantes.length || idsExtra.length) {
    errores.push(`IDs API/diccionario desalineados: faltan=${idsFaltantes}; sobran=${idsExtra}`);
  }

  const conteos = Object.fromEntries(CATEGORIAS.map((categoria) => [categoria, 0]));
  const vacios = [];
  for (const objeto of diccionario || []) {
    if (typeof objeto.registros !== "string" || !objeto.registros.trim()) {
      vacios.push(objeto.id || "sin ID");
      continue;
    }
    conteos[clasificar(objeto.registros)] += 1;
  }
  if (vacios.length) errores.push(`entradas web sin campo registros: ${vacios.join(", ")}`);

  return {
    errores,
    objetosApi: objetosApi.length,
    entradasWeb: (diccionario || []).length,
    registrosDescritos: (diccionario || []).length - vacios.length,
    conteos,
    unidadesManifest: tablas.filter((tabla) => {
      const unidad = tabla?.metadatos?.unidad;
      return typeof unidad === "string" && unidad.trim();
    }).length,
    tablasManifest: tablas.length,
    unidadApi: objetosApi.filter((objeto) => {
      const unidad = objeto?.unidad;
      return typeof unidad === "string" && unidad.trim();
    }).length,
  };
}

function main() {
  const resultado = inventariar(
    leerJson("docs/api/v2/catalog.json"),
    leerJson("data_manifest.json"),
    leerDiccionario(ROOT),
  );
  if (resultado.errores.length) {
    for (const error of resultado.errores) console.error(`FALLA: ${error}`);
    return 1;
  }

  if (process.argv.includes("--autoprueba")) {
    if (
      clasificar("Una fila por entidad") !== "unidad_explicita"
      || clasificar("Mensual · desde 2024-12") !== "frecuencia_o_formato"
      || clasificar("Campos relevantes · conserva las filas") !== "alcance_o_transformacion"
      || clasificar("Sin datos") !== "sin_datos"
    ) {
      console.error("FALLA AUTOPRUEBA: clasificación de etiquetas alterada");
      return 1;
    }
    console.log("OK AUTOPRUEBA: distingue unidad, frecuencia/formato, alcance y vacío");
  }

  const c = resultado.conteos;
  console.log(
    `UNIDAD — inventario no semántico: ${resultado.entradasWeb} objetos web; `
    + `${c.unidad_explicita} expresiones «Una fila por», `
    + `${c.frecuencia_o_formato} descriptores de frecuencia/formato, `
    + `${c.alcance_o_transformacion} descriptores de alcance/transformación, `
    + `${c.sin_datos} vacíos y ${c.otros} otros; `
    + `metadatos.unidad en ${resultado.unidadesManifest}/${resultado.tablasManifest} tablas ETL, `
    + `campo unidad en ${resultado.unidadApi}/${resultado.objetosApi} objetos API. `
    + "La clasificación textual no verifica la unidad real de observación."
  );
  return 0;
}

try {
  process.exitCode = main();
} catch (error) {
  console.error(`FALLA: ${error.message}`);
  process.exitCode = 1;
}
