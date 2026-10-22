# Servidor Quack propio (fase 3, **no desplegado**)

El sitio es estático: GitHub Pages sirve archivos y no ejecuta procesos, y GitHub
Actions no recibe tráfico entrante. Por eso la fase 3 se resolvió donde sí cabe
—los 156 resultados precalculados, ver [`../README.md`](../README.md)— y esta
página deja la otra mitad: **cómo levantar un servidor DuckDB propio** si algún
día hay demanda, con lo que hay que decidir antes de encenderlo.

> **Estado:** receta escrita y contrastada con la documentación oficial de
> DuckDB 2.0; **no ejecutada dentro del repositorio**. El entorno de desarrollo
> donde se escribió bloquea `extensions.duckdb.org`, así que aquí no hay
> evidencia de una consulta remota real. No se presenta como verificado.

## Qué resuelve, y qué no

- **Resuelve:** SQL ad-hoc sobre los 521 MB publicados sin descargarlos, para
  clientes DuckDB (Python, CLI, R). Es el caso de alguien que quiere preguntar
  «dame el top 20 por emisor en el último trimestre» sin bajar nada.
- **No resuelve:** el navegador (ya consulta en local con DuckDB-WASM) ni
  cualquier cliente que no entienda el protocolo Quack. No sustituye a las 156
  consultas publicadas, que son gratuitas y no tienen servidor que mantener.
- **Cuesta:** una máquina pequeña (2 vCPU / 2 GB), un dominio o subdominio y un
  certificado. Del orden de 5–15 USD al mes según dónde viva, más el tiempo de
  vigilarlo. Ese costo es la razón por la que la fase 3 quedó como decisión
  aparte y no como parte de la v1.

## Servidor

DuckDB 2.0 trae el protocolo Quack: la instancia que llama a `quack_serve` pasa
a atender a otros DuckDB por HTTP. Sirve lo que la sesión ve, incluidos los
Parquet remotos del sitio.

```sql
INSTALL quack;  LOAD quack;                 -- se autocargan al primer uso
-- Todo lo que la sesión ve queda accesible:
--   ATTACH 'quack:host:9494' AS sif (TOKEN '…');
CALL quack_serve('quack:127.0.0.1:9494', token = 'CAMBIAR_ESTE_TOKEN');
```

Tres decisiones que van antes del comando:

1. **Sólo lectura.** Quack también admite escrituras remotas
   (`INSERT INTO remoto.t`). El servidor debe abrir la base en modo lectura
   (`duckdb -readonly datos.duckdb`) o autorizar por función a cada token; si se
   publica con escritura, un cliente puede modificar lo que otros leen.
2. **TLS delante, no dentro.** La recomendación oficial es escuchar en
   `127.0.0.1` y poner un proxy que termine TLS (Caddy, nginx). El servidor
   acepta `allow_other_hostname = true` para escuchar fuera, pero entonces
   emite un certificado autofirmado que nadie va a aceptar en producción.
3. **Cuotas y observabilidad.** Un `SELECT * FROM ffmm_cartera_nacional` sin
   `LIMIT` son 2,3 millones de filas saliendo por la red del servidor. Sin tope
   de filas, límite por IP y un `/health`, el primer curioso deja el servicio
   caído.

## Piezas mínimas

| Pieza | Para qué | Como mínimo |
|---|---|---|
| `Dockerfile` | imagen con DuckDB 2.0 y `servidor.py` | `python:3.12-slim` + `pip install duckdb==2.0.0` |
| `servidor.py` | abre la base en lectura y llama a `quack_serve` | 30 líneas, sin framework |
| `compose.yaml` | el proceso y su reinicio | `restart: unless-stopped`, puerto sólo en `127.0.0.1` |
| `Caddyfile` | TLS automático y límite de tamaño | `reverse_proxy 127.0.0.1:9494` |
| *healthcheck* | ¿está vivo? | `FROM quack_query('quack:127.0.0.1', 'SELECT 1', token=…)` cada 60 s |
| *presupuesto* | ¿cuánto salió? | log de consultas del proxy y alerta por GB |

Están los tres primeros en esta carpeta como punto de partida. Son un borrador
ejecutable, no una configuración probada: faltan las pruebas que sí tienen el
SDK, el servidor MCP y el contrato.

## Cliente

```bash
pip install duckdb==2.0.0
```

```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL quack; LOAD quack;")
filas = con.execute("""
    FROM quack_query(
        'quack:sif.example.com',
        'SELECT pais_emisor, count(*) AS n FROM ffmm_cartera_extranjera GROUP BY 1 ORDER BY n DESC',
        token = 'CAMBIAR_ESTE_TOKEN'
    )
""").fetchall()
```

## Qué cambiaría en el contrato

Nada de lo publicado cambia: el servidor es **otra forma de leer** los mismos
Parquet. Si algún día se despliega, se añaden tres cosas fuera del contrato
estático —una ruta `/api/v1/servidor.json` que anuncie el host, el token pedido
por un formulario y un SLA escrito— y eso sí obliga a revisar las frases que hoy
dicen «sin servidor de consulta» en `README.md`, `llms.txt` y `openapi.json`.
