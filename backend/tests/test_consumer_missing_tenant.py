from backend.app.processing.consumer import validate_tenant


def test_validate_tenant_ok():
    evt = {"tenant_id": "acme"}
    assert validate_tenant(evt) is True


def test_validate_tenant_missing():
    assert validate_tenant({}) is False
    assert validate_tenant({"tenant_id": ""}) is False
    assert validate_tenant({"tenant_id": None}) is False
