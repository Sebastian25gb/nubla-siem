import os
import socket

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_OPENSEARCH_ROLLOVER_TESTS", "0") != "1",
    reason="Set RUN_OPENSEARCH_ROLLOVER_TESTS=1 to run rollover script tests",
)


def _is_reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False


def test_rollover_check_imports():
    # El test solo asegura que el script carga y expone main
    import importlib.util
    import pathlib

    path = pathlib.Path("scripts/rollover_tenant_index.py").resolve()
    spec = importlib.util.spec_from_file_location("rollover_tenant_index", path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    assert hasattr(mod, "main")


def test_opensearch_reachable_or_skip():
    host = os.getenv("OPENSEARCH_HOST", "opensearch:9200")
    if "://" in host:
        host = host.split("://", 1)[1]
    if ":" in host:
        h, p = host.split(":", 1)
        port = int(p)
    else:
        h, port = host, 9200
    if not _is_reachable(h, port):
        pytest.skip("OpenSearch not reachable")
    assert True
