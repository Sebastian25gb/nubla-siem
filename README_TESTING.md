# Pruebas y registro de resultados

Este documento explica cómo ejecutar las pruebas localmente y cómo se registran los resultados en CI.

## Ejecutar tests localmente
Desde la raíz del repo y con el virtualenv activado:
```bash
source .venv/bin/activate
PYTHONPATH=. python -m pytest -q backend/app/tests
```

Para generar JUnit XML y coverage localmente:
```bash
PYTHONPATH=. coverage run -m pytest --junitxml=test-results/junit.xml --cov=backend --cov-report=xml:coverage.xml
```

## GitHub Actions
- El workflow `.github/workflows/ci.yml` ejecuta pytest y genera:
  - `test-results/junit.xml` (artifact)
  - `coverage.xml` (artifact)

Los artifacts quedan disponibles en la página del workflow en GitHub Actions (descargables).

## Registro histórico de resultados (recomendado)
- Los artifacts de CI actúan como registro; además puede integrarse un servidor de reportes (Allure/ReportPortal) o subir coverage a Codecov.

## Monitor DLQ
- Hay un script `scripts/check_dlq.sh` que consulta la API Management de RabbitMQ y hace POST a webhook si hay alerta.
- Recomendación: agregar como cron job o systemd timer para ejecutarlo cada 5 minutos y recoger logs en `/var/log/check_dlq.log`.
