FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
# Usuario no root
RUN useradd -m appuser
USER appuser

# Por defecto arranca la API; el consumer define su command en compose
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]