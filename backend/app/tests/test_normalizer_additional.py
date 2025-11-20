import pytest
from backend.app.processing.normalizer import normalize

def test_malformed_kv_values():
    raw = {"message": 'devname=HostX msg="ok" badkey= srcip="1.2.3.4"'}
    out = normalize(raw)
    assert out["host"] == "HostX"
    assert out["message"] == "ok"
    kv = out["original"]["raw_kv"]
    # badkey queda con valor vacío o no aparece; validamos caso consistente
    assert ("badkey" not in kv) or (kv.get("badkey") == "")

def test_eventtime_invalid_fallback_to_now():
    raw = {"message": 'devname=H msg=test eventtime=notanumber'}
    out = normalize(raw)
    assert "@timestamp" in out

def test_ports_and_attackid():
    raw = {"message": 'devname=Host msg="attack event" srcip=1.2.3.4 dstip=5.6.7.8 srcport=443 dstport=1111 attackid=285212772 attack=udp_flood count=42 proto=udp'}
    out = normalize(raw)
    assert out["source"]["port"] == "443"
    assert out["destination"]["port"] == "1111"
    assert out["threat"]["id"] == "285212772"
    assert out["threat"]["name"] == "udp_flood"
    assert out["event"]["count"] == "42"

def test_severity_original():
    raw = {"message": 'devname=A msg=hello severity=CRITICAL'}
    out = normalize(raw)
    assert out["severity_original"] == "CRITICAL"
    # severity aún uppercase aquí, pipeline la bajará
    assert out["severity"] == "CRITICAL"