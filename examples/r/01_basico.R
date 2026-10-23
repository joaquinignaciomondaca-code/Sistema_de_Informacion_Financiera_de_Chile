#!/usr/bin/env Rscript
# Lo mismo que examples/python/01_ffmm_extranjero.py, sin SDK propio.
#
# Solo dos paquetes: DBI y duckdb. El contrato se usa tal cual: se descarga
# `api/v2/views.sql`, se cambia su única línea de configuración por la base que
# se quiera, se ejecutan las sentencias y las 105 vistas quedan disponibles.
#
#   Rscript examples/r/01_basico.R
#   SIF_CHILE_BASE=docs Rscript examples/r/01_basico.R     # copia local, sin red
#
# Qué comprueba: que el último período traiga posiciones en al menos tres países,
# que EE. UU. esté entre ellos y que el mayor supere el centenar. No fija cifras:
# las carteras cambian todos los meses.

suppressPackageStartupMessages({
  library(DBI)
  library(duckdb)
})

base <- Sys.getenv("SIF_CHILE_BASE",
  unset = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile")
base <- sub("/+$", "", base)
es_url <- grepl("^https?://", base)

leer <- function(relativa) {
  if (es_url) {
    readLines(url(paste0(base, "/", relativa)), warn = FALSE)
  } else {
    readLines(file.path(base, relativa), warn = FALSE)
  }
}

# 1. El DDL publicado, con la base de este script.
ddl <- leer("api/v2/views.sql")
ddl <- sub("^SET VARIABLE sif_base.*$", sprintf("SET VARIABLE sif_base = '%s';", base), ddl)

# 2. Una conexión en memoria y las vistas creadas.
con <- dbConnect(duckdb::duckdb())
on.exit(dbDisconnect(con, shutdown = TRUE))
if (es_url) {
  try(dbExecute(con, "INSTALL httpfs"), silent = TRUE)
  try(dbExecute(con, "LOAD httpfs"), silent = TRUE)
}

sentencias <- trimws(unlist(strsplit(paste(ddl, collapse = "\n"), ";", fixed = TRUE)))
sentencias <- sentencias[nzchar(sentencias)]
creadas <- 0L
for (sentencia in sentencias) {
  # Las cabeceras de comentario viajan pegadas a su CREATE VIEW.
  limpia <- trimws(gsub("(?m)^\\s*--.*$", "", sentencia, perl = TRUE))
  if (!nzchar(limpia)) next
  dbExecute(con, limpia)
  if (grepl("^CREATE OR REPLACE VIEW", limpia, ignore.case = TRUE)) creadas <- creadas + 1L
}
cat(sprintf("Vistas creadas desde el contrato: %d\n\n", creadas))

# 3. La consulta del README.
sql <- "
SELECT pais_emisor,
       count(*)                  AS posiciones,
       count(DISTINCT run_fondo) AS fondos
FROM ffmm_cartera_extranjera
WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera)
GROUP BY pais_emisor
ORDER BY posiciones DESC
"
filas <- dbGetQuery(con, sql)
periodo <- dbGetQuery(con, "SELECT max(periodo) AS p FROM ffmm_cartera_extranjera")$p

cat(sprintf("Fondos mutuos chilenos invertidos en el exterior - periodo %s\n\n", periodo))
print(filas, row.names = FALSE)

# 4. Comprobaciones, en el mismo espíritu que el ejemplo de Python.
stopifnot(nrow(filas) > 0)
stopifnot(nrow(filas) >= 3)
stopifnot("US" %in% filas$pais_emisor)
stopifnot(sum(filas$posiciones) >= 1000)
stopifnot(max(filas$posiciones) >= 100)

cat(sprintf("\nOK - %s posiciones en %d paises, %s\n",
            format(sum(filas$posiciones), big.mark = ","), nrow(filas), periodo))
