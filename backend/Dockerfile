FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    redis-tools \
    curl \
    build-essential \
    libpq-dev \
    libssl-dev \
    zlib1g-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y build-essential libpq-dev libssl-dev zlib1g-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]