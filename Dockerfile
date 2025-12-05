# Dockerfile para metrics-exporter en la raíz del repo
# Ejecuta: python docs/operational/metrics/exporter.py
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencias de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Copiamos el repo completo porque el script vive en docs/operational/metrics/exporter.py
COPY . /app

# Puerto del exporter (9108) según docker-compose
EXPOSE 9108

CMD ["python", "docs/operational/metrics/exporter.py"]