import pytest
from backend.app.processing.normalizer import normalize

def test_normalize_kv_eventtime():
    # eventtime en ns que corresponde a 2025-11-12T14:38:19.127000+00:00
    ns = 1762958299127000000
    raw = {
        "message": f'devname=DelawareHotel msg="anomaly" eventtime={ns} severity=CRITICAL'
    }
    out = normalize(raw)
    assert out["host"] == "DelawareHotel"
    assert out["message"] == "anomaly"
    assert out["severity"] == "critical"
    assert out["@timestamp"].startswith("2025-11-12T14:38:19.127")

def test_normalize_quoted_values_and_ips():
    raw = {"message": 'devname="Host B" msg="hello world" srcip=1.2.3.4 dstip=5.6.7.8'}
    out = normalize(raw)
    assert out["host"] == "Host B"
    assert out["message"] == "hello world"
    assert out["source"]["ip"] == "1.2.3.4"
    assert out["destination"]["ip"] == "5.6.7.8"

def test_severity_fallback_and_defaults():
    raw = {"message": "devname=H msg=test"}
    out = normalize(raw)
    assert out["host"] == "H"
    # Si no hay severity, cae a "info"
    assert out["severity"] == "info"
    assert "tenant_id" in out
    assert "@timestamp" in out

def test_passthrough_no_message_and_non_dict():
    raw1 = {"not_message": "x"}
    assert normalize(raw1) == raw1
    raw2 = "plain string payload"
    assert normalize(raw2) == raw2