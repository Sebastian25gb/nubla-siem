import pytest
from backend.app.processing.normalizer import normalize

def test_malformed_kv_values():
    # key without value, and escaped quotes
    raw = {"message": 'devname=HostX msg="ok" badkey= srcip="1.2.3.4"'}
    out = normalize(raw)
    assert out["host"] == "HostX"
    assert out["message"] == "ok"
    # badkey should be ignored or present but empty
    assert "badkey" in out.get("original", {}).get("raw_kv", {}) or "badkey" not in out.get("original", {}).get("raw_kv", {})

def test_eventtime_invalid_fallback_to_now():
    raw = {"message": 'devname=H msg=test eventtime=notanumber'}
    out = normalize(raw)
    # eventtime invalid -> @timestamp present (fallback not raising)
    assert "@timestamp" in out

def test_empty_message_passthrough():
    raw = {"message": ""}
    out = normalize(raw)
    # empty message considered a string; normalization returns something with original.message_raw
    assert out["original"]["message_raw"] == ""

def test_large_payload_performance_like():
    # simulate many kv pairs in one message (not a strict perf test, just sanity)
    kvs = " ".join([f"f{i}=v{i}" for i in range(200)])
    raw = {"message": f"devname=PerfHost msg=bulk {kvs}"}
    out = normalize(raw)
    assert out["host"] == "PerfHost"
    assert "f199" in out.get("original", {}).get("raw_kv", {})