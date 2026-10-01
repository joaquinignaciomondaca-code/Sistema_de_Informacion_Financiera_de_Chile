/**
 * Guardia de solo lectura de la consola SQL.
 *
 * El motor corre dentro del navegador del visitante (DuckDB-Wasm en memoria, sobre
 * Parquet servidos por HTTP), así que ninguna consulta puede tocar los archivos
 * publicados ni el repositorio. Pero **sí** puede romper la sesión de quien la
 * escribe —y la de quien abre un enlace compartido—, porque DuckDB acepta
 * sentencias de escritura sobre su catálogo en memoria:
 *
 *   DROP VIEW agf_balance;                       → la tabla desaparece de la pestaña
 *   CREATE OR REPLACE VIEW agf_balance AS ...    → la tabla pasa a mostrar datos inventados
 *   CREATE TABLE falso AS SELECT ...; INSERT ... → filas fabricadas con la misma piel que las reales
 *
 * Ese es el riesgo real: no la pérdida del dato publicado (eso no puede pasar),
 * sino la suplantación del dato en pantalla. Y se agrava porque `checkUrlHash()`
 * ejecuta automáticamente lo que venga en `#sql=`, de modo que un enlace puede
 * ejecutar sentencias en el navegador de otra persona.
 *
 * Este módulo es la única puerta de entrada: `DuckDBClient.query()` lo consulta
 * antes de enviar cualquier SQL al motor. La política es una lista blanca —solo
 * se ejecuta lo que empieza con una palabra de lectura— y no una lista negra,
 * porque una lista negra siempre se queda corta.
 *
 * Se aplica **después** de quitar comentarios y literales de texto, para que una
 * cuenta o un valor que contenga la palabra "drop" no bloquee una consulta
 * legítima, y para que un comentario no pueda esconder una sentencia.
 *
 * Uso:  SIFSqlGuard.validar(sql) → { ok: boolean, motivo: string }
 */
"use strict";

(function (global) {
  // Sentencias que solo leen. Todo lo demás queda fuera.
  const PERMITIDAS = [
    "SELECT", "WITH", "VALUES", "TABLE", "DESCRIBE", "DESC", "SHOW",
    "EXPLAIN", "SUMMARIZE", "PRAGMA", "PIVOT", "UNPIVOT"
  ];

  // Palabras que convierten una consulta en escritura aunque no vayan al inicio.
  // `SELECT ... INTO tabla` crea una tabla (CTAS) sin que suene a escritura.
  const ESCRITURA_SUELTA = /\b(INTO|COPY|ATTACH|DETACH|INSTALL|LOAD)\b/i;

  // Quita comentarios y literales para quedarse con el esqueleto de la sentencia.
  // Los literales se reemplazan por un marcador que conserva la longitud para no
  // desplazar posiciones (así los mensajes de error siguen apuntando al lugar).
  function limpiar(sql) {
    let s = String(sql == null ? "" : sql);
    let out = "";
    let i = 0;
    while (i < s.length) {
      const dos = s.slice(i, i + 2);
      if (dos === "--") {                                  // comentario de línea
        const fin = s.indexOf("\n", i);
        i = fin === -1 ? s.length : fin + 1;
        out += "\n";
        continue;
      }
      if (dos === "/*") {                                  // comentario de bloque
        const fin = s.indexOf("*/", i + 2);
        i = fin === -1 ? s.length : fin + 2;
        out += " ";
        continue;
      }
      const c = s[i];
      if (c === "'" || c === '"') {                        // literal o identificador
        const cierre = c === "'" ? "'" : '"';
        let j = i + 1;
        while (j < s.length) {
          if (s[j] === cierre) {
            // '' dentro de un literal es una comilla escapada, no el cierre.
            if (cierre === "'" && s[j + 1] === "'") { j += 2; continue; }
            break;
          }
          if (s[j] === "\\") { j += 2; continue; }
          j++;
        }
        out += " " + "·".repeat(Math.max(1, j - i)) + " ";
        i = j + 1;
        continue;
      }
      out += c;
      i++;
    }
    return out;
  }

  // Parte el SQL en sentencias por `;` fuera de literales (ya limpias).
  function sentencias(esqueleto) {
    return esqueleto
      .split(";")
      .map((t) => t.replace(/\s+/g, " ").trim())
      .filter((t) => t.length > 0);
  }

  function primeraPalabra(sentencia) {
    const m = sentencia.match(/^([A-Za-z_][A-Za-z0-9_]*)/);
    return m ? m[1].toUpperCase() : "";
  }

  /**
   * Decide si una consulta puede ejecutarse.
   * Devuelve `{ ok: true }` o `{ ok: false, motivo }` con un mensaje en español
   * pensado para mostrarse tal cual en la terminal.
   */
  function validar(sql) {
    const original = String(sql == null ? "" : sql);
    if (!original.trim()) return { ok: false, motivo: "La consulta está vacía." };

    const esqueleto = limpiar(original);
    const partes = sentencias(esqueleto);

    if (partes.length === 0) {
      return { ok: false, motivo: "La consulta está vacía o es solo un comentario." };
    }
    if (partes.length > 1) {
      return {
        ok: false,
        motivo: "Solo se ejecuta una sentencia por vez y esta trae " + partes.length +
                ". La consola es de solo lectura: no se permite encadenar sentencias " +
                "con «;» (ahí es donde una consulta inocente podría esconder un DROP o un INSERT)."
      };
    }

    const sentencia = partes[0];
    const verbo = primeraPalabra(sentencia);

    if (!verbo) {
      return { ok: false, motivo: "No se reconoce el inicio de la consulta." };
    }
    if (PERMITIDAS.indexOf(verbo) === -1) {
      return {
        ok: false,
        motivo: "Esta consola es de solo lectura y «" + verbo + "» no está permitido. " +
                "Se aceptan consultas que empiecen con " +
                PERMITIDAS.slice(0, 6).join(", ") + " (entre otras de lectura). " +
                "Nada de lo que se escriba aquí puede modificar los datos publicados, " +
                "pero sí podría alterar lo que ves en tu propia pestaña: por eso se bloquea."
      };
    }
    if (ESCRITURA_SUELTA.test(sentencia)) {
      const hallada = (sentencia.match(ESCRITURA_SUELTA) || [""])[0].toUpperCase();
      return {
        ok: false,
        motivo: "La consulta empieza con «" + verbo + "» pero contiene «" + hallada +
                "», que escribe en la base (por ejemplo SELECT ... INTO crea una tabla). " +
                "Esta consola es de solo lectura."
      };
    }
    return { ok: true, motivo: "" };
  }

  const guardia = { validar, limpiar, PERMITIDAS };
  global.SIFSqlGuard = guardia;
  if (typeof module !== "undefined" && module.exports) module.exports = guardia;
})(typeof window !== "undefined" ? window : globalThis);
