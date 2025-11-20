from backend.app.processing.normalizer import normalize

def test_normalizer_numeric_cast():
    raw = {
        "message": (
            'devname=Host srcip=1.1.1.1 dstip=2.2.2.2 '
            'srcport=443 dstport=5500 count=7 proto=17 '
            'msg="pps 321 of prior second" severity=CRITICAL '
            'crscore=70 attack=udp_flood attackid=999'
        )
    }
    out = normalize(raw)
    assert out["source"]["port"] == 443
    assert out["destination"]["port"] == 5500
    assert out["event"]["count"] == 7
    assert out["flow"]["packets_per_second"] == 321
    assert out["threat"]["score"] == 70
    assert out["severity_original"] == "CRITICAL"
    assert out["severity"] == "critical"