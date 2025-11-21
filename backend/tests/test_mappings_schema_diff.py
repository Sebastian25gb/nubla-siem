from scripts.diagnostics.check_mappings_vs_schema import (
    compute_diff,
    extract_schema_fields,
    flatten_mapping,
)


def test_compute_diff_detects_missing_and_extra():
    fake_schema = {
        "properties": {
            "tenant_id": {"type": "keyword"},
            "severity": {"type": "keyword"},
            "message": {"type": "text"},
            "source": {
                "properties": {
                    "ip": {"type": "ip"},
                    "port": {"type": "integer"},
                }
            },
        }
    }
    fake_mapping = {
        "logs-default": {
            "mappings": {
                "properties": {
                    "tenant_id": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "message": {"type": "text"},
                    "source": {"properties": {"ip": {"type": "ip"}}},
                    "destination": {"properties": {"ip": {"type": "ip"}}},
                }
            }
        }
    }

    schema_fields = extract_schema_fields(fake_schema)
    mapping_fields = flatten_mapping(fake_mapping)
    diff = compute_diff(schema_fields, mapping_fields)

    assert "source.port" in diff["missing_in_mapping"]
    assert "destination.ip" in diff["extra_in_mapping"]
    assert not diff["type_mismatches"]


def test_compute_diff_type_mismatch():
    fake_schema = {"properties": {"event": {"properties": {"count": {"type": "long"}}}}}
    fake_mapping = {
        "logs-default": {
            "mappings": {"properties": {"event": {"properties": {"count": {"type": "keyword"}}}}}
        }
    }

    schema_fields = extract_schema_fields(fake_schema)
    mapping_fields = flatten_mapping(fake_mapping)
    diff = compute_diff(schema_fields, mapping_fields)

    assert diff["type_mismatches"]
    assert diff["type_mismatches"][0]["field"] == "event.count"
