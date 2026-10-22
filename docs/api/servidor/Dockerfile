# Borrador, no verificado: ver README.md de esta carpeta.
FROM python:3.12-slim

RUN pip install --no-cache-dir duckdb==2.0.0

WORKDIR /srv
COPY servidor.py .

# Escucha sólo en loopback: el TLS lo pone el proxy de delante.
ENV SIF_QUACK_BIND=127.0.0.1:9494
EXPOSE 9494
HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
  CMD python -c "import duckdb,os;duckdb.connect().execute(\"INSTALL quack;LOAD quack;FROM quack_query('quack:127.0.0.1:9494','SELECT 1',token=os.environ['SIF_QUACK_TOKEN'],disable_ssl=true)\")"

USER nobody
CMD ["python", "servidor.py"]
