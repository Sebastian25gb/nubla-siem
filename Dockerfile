FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copiar la carpeta docs completa para mantener la misma ruta que espera docker-compose
COPY docs/ /app/docs/

# Instalar dependencias mínimas que usa el exporter (prometheus client, opensearch client y requests)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir prometheus_client==0.20.0 opensearch-py==2.5.0 requests==2.32.5 \
    && apt-get remove -y gcc libffi-dev \
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

EXPOSE 9108

# Ejecutamos la ruta que docker-compose usa: python docs/operational/metrics/exporter.py
CMD ["python", "docs/operational/metrics/exporter.py"]