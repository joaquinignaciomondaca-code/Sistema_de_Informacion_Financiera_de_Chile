# Servidor HTTP de consultas SIF Chile (fase 3).
# Contexto de build: raíz del repositorio.
#   docker build -f servidor/Dockerfile -t sif-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SIF_API_HOST=0.0.0.0 \
    SIF_API_PORT=8000

WORKDIR /srv

COPY servidor/requirements.txt /srv/servidor/requirements.txt
COPY sdk/python /srv/sdk/python
RUN pip install --no-cache-dir -r /srv/servidor/requirements.txt \
    && pip install --no-cache-dir -e /srv/sdk/python

COPY servidor /srv/servidor

# En modo remoto (por defecto) el proceso no necesita disco local: DuckDB lee los
# Parquet del sitio por HTTP Range. En modo local se monta docs/ en /datos y se
# fija SIF_CHILE_BASE=/datos (ver compose.yaml).
RUN mkdir -p /datos && chown nobody:nogroup /datos
USER nobody

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4).read()"

CMD ["python", "-m", "servidor"]
