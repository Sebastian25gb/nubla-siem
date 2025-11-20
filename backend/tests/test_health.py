import pytest
from fastapi.testclient import TestClient

from backend.app.main import app  # Ajustar import si main.py está en backend/app/main.py


@pytest.mark.unit
def test_health_endpoint():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    # Ajustar al JSON real si devuelve {"status": "ok"}:
    data = r.json()
    assert "status" in data
