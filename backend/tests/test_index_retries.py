import pytest

from backend.app.repository.elastic import INDEX_RETRIES, index_event


class DummyES:
    def __init__(self, fail_times: int = 0):
        self._fail_times = fail_times
        self.calls = 0

    def index(self, index, body, params=None):
        self.calls += 1
        if self.calls <= self._fail_times:
            raise RuntimeError("simulated failure")
        return {"result": "created"}


def test_index_event_retries():
    es = DummyES(fail_times=2)
    before = INDEX_RETRIES._value.get()
    resp = index_event(
        es, index="logs-test", body={"message": "retry test"}, retries=3, backoff_seconds=0.0005
    )
    after = INDEX_RETRIES._value.get()
    assert resp["result"] == "created"
    # Dos reintentos (attempt 0 y 1 fallan; attempt 2 éxito)
    assert (after - before) == 2, f"Incremento esperado 2, delta real={after-before}"
    assert es.calls == 3


def test_index_event_exhaust_retries():
    es = DummyES(fail_times=5)
    before = INDEX_RETRIES._value.get()
    with pytest.raises(RuntimeError):
        index_event(
            es, index="logs-test", body={"message": "fail all"}, retries=2, backoff_seconds=0.0005
        )
    after = INDEX_RETRIES._value.get()
    # Dos reintentos (attempt 0 y 1), luego intento final que falla y levanta excepción
    assert (after - before) == 2, f"Incremento esperado 2, delta real={after-before}"
    assert es.calls == 3
