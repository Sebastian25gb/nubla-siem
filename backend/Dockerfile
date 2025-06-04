FROM python:3.9-bullseye

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    redis-tools \
    curl \
    postgresql-client \
    && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "60", "--workers", "2"]