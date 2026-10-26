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
 *   node scripts/audit_unidad_observacion.js --detalle  # JSONL por objeto, sin inferir unidades
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

  const apiPorClave = new Map();
  for (const objeto of objetosApi) {
    const claves = [objeto.id, objeto.sql_view, ...(Array.isArray(objeto.aliases) ? objeto.aliases : [])];
    for (const clave of claves.filter((valor) => typeof valor === "string" && valor.trim())) {
      const existente = apiPorClave.get(clave);
      if (existente && existente.id !== objeto.id) {
        errores.push(`clave API ambigua para manifiesto ${clave}: ${existente.id} / ${objeto.id}`);
      } else {
        apiPorClave.set(clave, objeto);
      }
    }
  }

  const manifiestoPorApiId = new Map();
  const manifiestosSinApi = [];
  for (const tabla of tablas) {
    const claves = [tabla.id, tabla.view_name, tabla.name]
      .filter((valor) => typeof valor === "string" && valor.trim());
    const candidatos = [...new Map(claves.map((clave) => [apiPorClave.get(clave)?.id, apiPorClave.get(clave)])).values()]
      .filter(Boolean);
    if (candidatos.length === 0) {
      manifiestosSinApi.push(tabla);
    } else if (candidatos.length > 1) {
      errores.push(`manifiesto ${tabla.id} coincide con varios objetos API: ${candidatos.map((objeto) => objeto.id).join(", ")}`);
    } else if (manifiestoPorApiId.has(candidatos[0].id)) {
      errores.push(`varios manifiestos coinciden con el objeto API ${candidatos[0].id}`);
    } else {
      manifiestoPorApiId.set(candidatos[0].id, tabla);
    }
  }

  const webPorId = new Map((diccionario || []).map((objeto) => [objeto.id, objeto]));
  const detalle = objetosApi.map((objeto) => {
    const tabla = manifiestoPorApiId.get(objeto.id) || null;
    const web = webPorId.get(objeto.id) || {};
    const unidadApi = typeof objeto.unidad === "string" ? objeto.unidad.trim() : "";
    const unidadManifest = typeof tabla?.metadatos?.unidad === "string"
      ? tabla.metadatos.unidad.trim()
      : "";
    return {
      id: objeto.id,
      vista_api: typeof objeto.sql_view === "string" ? objeto.sql_view : "",
      alias_api: Array.isArray(objeto.aliases) ? objeto.aliases.join("|") : "",
      id_manifest_coincidente: tabla?.id || "",
      coincidencia_manifest: tabla ? "unívoca_por_id_vista_o_alias" : "sin_match_unívoco",
      unidad_api_declarada: unidadApi,
      unidad_manifest_declarada: unidadManifest,
      registros_diccionario_web: typeof web.registros === "string" ? web.registros.trim() : "",
    };
  }).sort((a, b) => a.id.localeCompare(b.id));

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
    detalle,
    manifiestosSinApi: manifiestosSinApi.map((tabla) => ({
      id: tabla.id || "",
      vista: tabla.view_name || "",
      nombre: tabla.name || "",
      unidad_manifest_declarada: typeof tabla?.metadatos?.unidad === "string"
        ? tabla.metadatos.unidad.trim()
        : "",
    })),
    manifiestosConMatch: manifiestoPorApiId.size,
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
      || resultado.detalle.length !== resultado.objetosApi
      || new Set(resultado.detalle.map((objeto) => objeto.id)).size !== resultado.objetosApi
      || resultado.detalle.some((objeto) => typeof objeto.registros_diccionario_web !== "string")
      || resultado.manifiestosConMatch + resultado.manifiestosSinApi.length !== resultado.tablasManifest
      || resultado.detalle.some((objeto) => !["unívoca_por_id_vista_o_alias", "sin_match_unívoco"].includes(objeto.coincidencia_manifest))
    ) {
      console.error("FALLA AUTOPRUEBA: clasificación o inventario por objeto alterados");
      return 1;
    }
    console.log("OK AUTOPRUEBA: clasifica etiquetas y conserva una fila de declaraciones por ID API");
  }

  if (process.argv.includes("--detalle")) {
    for (const objeto of resultado.detalle) {
      console.log(JSON.stringify({ tipo: "objeto_api", ...objeto }));
    }
    for (const tabla of resultado.manifiestosSinApi) {
      console.log(JSON.stringify({ tipo: "entrada_etl_sin_match_api_univoco", ...tabla }));
    }
    return 0;
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
