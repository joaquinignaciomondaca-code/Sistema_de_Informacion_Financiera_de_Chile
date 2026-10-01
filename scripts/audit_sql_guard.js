#!/usr/bin/env node
/**
 * Prueba de la guardia de solo lectura de la consola SQL (docs/js/sql_guard.js).
 *
 * Comprueba que lo que destruye o fabrica datos en la sesión del visitante queda
 * fuera, y que las consultas legítimas —incluidas las que mencionan esas palabras
 * dentro de comillas o en un comentario— siguen pasando.
 *
 * No necesita jsdom: evalúa el módulo en un ámbito propio con un `window` falso.
 *
 * Uso: node scripts/audit_sql_guard.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const RUTA = path.join(__dirname, "..", "docs", "js", "sql_guard.js");
const fallas = [];
const ok = (cond, msg) => {
  console.log((cond ? "OK    " : "FALLA ") + msg);
  if (!cond) fallas.push(msg);
};

const ventana = { window: {} };
vm.createContext(ventana);
try {
  vm.runInContext(fs.readFileSync(RUTA, "utf8"), ventana, { filename: RUTA });
} catch (err) {
  console.log("FALLA  no se pudo cargar docs/js/sql_guard.js: " + err.message);
  process.exit(1);
}
const guardia = ventana.window.SIFSqlGuard;
ok(!!guardia && typeof guardia.validar === "function", "el módulo expone SIFSqlGuard.validar()");

const acepta = (sql, msg) => ok(guardia.validar(sql).ok === true, "acepta: " + msg);
const rechaza = (sql, msg) => {
  const r = guardia.validar(sql);
  ok(r.ok === false && typeof r.motivo === "string" && r.motivo.length > 20, "rechaza: " + msg);
};

// --- Lo que el visitante (o un enlace ajeno) no debe poder ejecutar -----------
rechaza("DROP VIEW agf_balance;", "DROP VIEW de una tabla publicada");
rechaza("drop view ccaf_resultados", "DROP VIEW en minúsculas");
rechaza("DROP TABLE macro_uf;", "DROP TABLE");
rechaza("DELETE FROM agf_balance WHERE periodo = '2025-12';", "DELETE de filas");
rechaza("UPDATE agf_balance SET valor = 0;", "UPDATE de cifras");
rechaza("INSERT INTO agf_balance VALUES ('2026-06','99999999','FALSO','x','CLP','ESF C/NC',1,'Cuenta',1,NULL,1,'TAX CI',true);",
        "INSERT de una fila fabricada");
rechaza("CREATE OR REPLACE VIEW agf_balance AS SELECT 1 AS periodo, 999 AS valor;",
        "suplantación de una tabla real por datos inventados");
rechaza("CREATE TABLE falso AS SELECT * FROM agf_balance;", "CREATE TABLE AS");
rechaza("SELECT * INTO copia FROM agf_balance;", "CTAS con SELECT ... INTO");
rechaza("copy (select * from agf_balance) to 'salida.parquet';", "COPY a archivo");
rechaza("ATTACH 'otra.db';", "ATTACH de otra base");
rechaza("INSTALL httpfs; LOAD httpfs;", "instalación de extensiones");
rechaza("ALTER TABLE agf_balance RENAME TO otra;", "ALTER TABLE");
rechaza("TRUNCATE agf_balance;", "TRUNCATE");
rechaza("VACUUM;", "VACUUM");
rechaza("SET threads = 8;", "SET de configuración");
rechaza("CALL duckdb_extensions();", "CALL");
rechaza("", "consulta vacía");
rechaza("   ", "consulta en blanco");
rechaza("-- solo un comentario\n", "solo un comentario");

// --- Lo que sí debe pasar -----------------------------------------------------
acepta("SELECT * FROM agf_balance LIMIT 10;", "SELECT con punto y coma final");
acepta("select periodo, valor from ccaf_balance where rut = '81826800'", "SELECT simple");
acepta("WITH x AS (SELECT 1 AS n) SELECT * FROM x;", "CTE con WITH");
acepta("DESCRIBE agf_resultados;", "DESCRIBE");
acepta("SHOW TABLES;", "SHOW TABLES");
acepta("EXPLAIN SELECT * FROM macro_uf;", "EXPLAIN");
acepta("SUMMARIZE SELECT * FROM macro_uf;", "SUMMARIZE");
acepta("PRAGMA version;", "PRAGMA");
acepta("PIVOT macro_uf ON periodo USING sum(valor);", "PIVOT");
acepta("VALUES (1), (2);", "VALUES");

// --- Las palabras prohibidas dentro de texto o comentarios no bloquean --------
acepta("SELECT cuenta FROM agf_balance WHERE cuenta LIKE '%drop%';", "‘drop’ dentro de un literal");
acepta("SELECT 'INSERT INTO falso' AS nota;", "‘INSERT INTO’ como texto");
acepta("SELECT * FROM agf_balance -- DROP VIEW agf_balance;\nLIMIT 5;", "DROP escondido en un comentario de línea");
acepta("SELECT /* COPY TO archivo */ * FROM agf_balance LIMIT 1;", "COPY dentro de un comentario de bloque");
acepta("SELECT 'no cierra; DROP VIEW x' AS nota FROM agf_balance LIMIT 1;", "comillas sin cerrar no confunden al limpiador");
acepta("SELECT 'it''s drop view' AS nota;", "comilla escapada dentro de un literal");

// --- Encadenar sentencias no cuela -------------------------------------------
rechaza("SELECT 1; DROP VIEW agf_balance;", "SELECT seguido de DROP");
rechaza("SELECT 1; SELECT 2;", "dos sentencias aunque ambas lean");

// --- Mensaje útil ------------------------------------------------------------
const motivo = guardia.validar("DROP VIEW agf_balance;").motivo;
ok(/solo lectura/i.test(motivo), "el rechazo explica que la consola es de solo lectura");
ok(/DROP/.test(motivo), "el rechazo nombra la sentencia que se intentó");

console.log(fallas.length
  ? `\n${fallas.length} comprobaciones fallaron`
  : `\nGuardia SQL: todas las comprobaciones OK`);
process.exit(fallas.length ? 1 : 0);
