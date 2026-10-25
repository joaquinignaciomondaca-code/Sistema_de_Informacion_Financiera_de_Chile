"use strict";

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function extraerDiccionario(texto) {
  const marcador = "const DATA_DICTIONARY = ";
  const marcadorInicio = texto.indexOf(marcador);
  if (marcadorInicio < 0) throw new Error("no se encontró DATA_DICTIONARY");
  const inicio = texto.indexOf("[", marcadorInicio + marcador.length);
  if (inicio < 0) throw new Error("no se encontró el arreglo DATA_DICTIONARY");

  let profundidad = 0;
  let comilla = "";
  let escapado = false;
  let comentarioLinea = false;
  let comentarioBloque = false;
  let fin = -1;
  for (let i = inicio; i < texto.length; i += 1) {
    const actual = texto[i];
    const siguiente = texto[i + 1];
    if (comentarioLinea) {
      if (actual === "\n") comentarioLinea = false;
      continue;
    }
    if (comentarioBloque) {
      if (actual === "*" && siguiente === "/") {
        comentarioBloque = false;
        i += 1;
      }
      continue;
    }
    if (comilla) {
      if (escapado) escapado = false;
      else if (actual === "\\") escapado = true;
      else if (actual === comilla) comilla = "";
      continue;
    }
    if (actual === "/" && siguiente === "/") {
      comentarioLinea = true;
      i += 1;
      continue;
    }
    if (actual === "/" && siguiente === "*") {
      comentarioBloque = true;
      i += 1;
      continue;
    }
    if (actual === "\"" || actual === "'" || actual === "`") {
      comilla = actual;
      continue;
    }
    if (actual === "[") profundidad += 1;
    else if (actual === "]") {
      profundidad -= 1;
      if (profundidad === 0) {
        fin = i;
        break;
      }
      if (profundidad < 0) throw new Error("corchetes desbalanceados en DATA_DICTIONARY");
    }
  }
  if (fin < 0) throw new Error("DATA_DICTIONARY no tiene cierre de arreglo");
  const expresion = texto.slice(inicio, fin + 1);
  const diccionario = vm.runInNewContext(`(${expresion})`);
  if (!Array.isArray(diccionario)) throw new Error("DATA_DICTIONARY no evalúa a una lista");
  return diccionario;
}

function leerDiccionario(raiz) {
  const ruta = path.join(raiz, "docs/js/data_dictionary.js");
  return extraerDiccionario(fs.readFileSync(ruta, "utf8"));
}

module.exports = { extraerDiccionario, leerDiccionario };
