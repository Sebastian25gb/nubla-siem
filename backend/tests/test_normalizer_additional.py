from backend.app.processing.normalizer import normalize

def test_malformed_kv_values():
    raw = {"message": 'devname=H msg="x" srcip=1.1.1.1 dstip=2.2.2.2 srcport=abc dstport=NaN severity=MEDIUM'}
    out = normalize(raw)
    # Puertos inválidos no deben setearse
    assert "port" not in out.get("source", {})
    assert "port" not in out.get("destination", {})
    assert out["severity_original"] == "MEDIUM"
    assert out["severity"] == "medium"

def test_eventtime_invalid_fallback_to_now():
    raw = {"message": 'devname=H msg="x" eventtime=notanumber'}
    out = normalize(raw)
    # Debe existir @timestamp ISO8601
    assert "@timestamp" in out and isinstance(out["@timestamp"], str)
    assert "T" in out["@timestamp"]

def test_ports_and_attackid():
    raw = {"message": 'devname=Host msg="attack event" srcip=1.2.3.4 dstip=5.6.7.8 srcport=443 dstport=1111 attackid=285212772 attack=udp_flood count=42 proto=udp'}
    out = normalize(raw)
    # Puertos como enteros (alineado con schema)
    assert out["source"]["port"] == 443
    assert out["destination"]["port"] == 1111
    # Threat y count
    assert out["threat"]["id"] == "285212772"
    assert out["threat"]["name"] == "udp_flood"
    assert out["event"]["count"] == 42
    # Protocolo
    assert out["network"]["protocol"] == "udp"

def test_severity_original():
    raw = {"message": 'devname=A msg=hello severity=CRITICAL'}
    out = normalize(raw)
    assert out["severity_original"] == "CRITICAL"
    assert out["severity"] == "critical"