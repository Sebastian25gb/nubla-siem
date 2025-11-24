from backend.app.processing.normalizer import normalize


def test_host_to_tenant_mapping_has_host_preserved(monkeypatch):
    monkeypatch.setenv("REQUIRE_TENANT", "false")
    raw = {"message": 'date=2025-11-21 time=07:29:29 devname="DelawareHotel" msg="something"'}
    out = normalize(raw)
    assert out["host"] == "DelawareHotel"
    # El normalizer NO hace el mapping; mapping ocurre en consumer. Aquí solo confirmamos que tendremos host para mapear.
    assert out.get("tenant_id") in ("default", "DelawareHotel", None)
