FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias para redis-cli, curl, y compilación de tensorflow
RUN apt-get update && apt-get install -y \
    redis-tools \
    curl \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]