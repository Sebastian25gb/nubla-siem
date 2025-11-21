FROM python:3.10-slim

WORKDIR /app

# Copiamos primero requirements para aprovechar cache
COPY backend/app/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiamos todo el repo (contexto = raíz del repo)
COPY . .

# Ajuste PYTHONPATH para que /app esté en path (contiene backend/)
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Usuario no root (opcional)
RUN useradd -m appuser || true
USER appuser

# Comando por defecto (API). El consumer lo sobreescribe en docker-compose.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]