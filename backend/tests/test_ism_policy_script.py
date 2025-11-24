import importlib.util
import os
import pathlib

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_OPENSEARCH_ISM_TESTS", "0") != "1",
    reason="Set RUN_OPENSEARCH_ISM_TESTS=1 to run ISM tests",
)


def test_import_apply_ism():
    path = pathlib.Path("scripts/apply_ism_policy.py").resolve()
    spec = importlib.util.spec_from_file_location("apply_ism_policy", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(mod)  # type: ignore
    assert hasattr(mod, "main")
