import json

from jsonschema import Draft7Validator

from backend.app.processing.normalizer import normalize
from backend.app.processing.utils import prepare_event

with open("backend/app/schema/ncs_v1.0.0.json", "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)

validator = Draft7Validator(SCHEMA)


def test_prepare_and_validate_minimal():
    raw = {
        "message": (
            "devname=Host srcip=1.1.1.1 dstip=2.2.2.2 "
            "srcport=443 dstport=5500 count=1 proto=17 "
            'msg="pps 10 of prior second" severity=CRITICAL'
        )
    }
    norm = normalize(raw)
    evt = prepare_event(norm)
    errors = list(validator.iter_errors(evt))
    assert not errors, f"Schema errors: {[e.message for e in errors]}"
    assert "@timestamp" in evt
    assert evt["dataset"] == "syslog.generic"
