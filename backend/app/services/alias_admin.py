from backend.app.core.opensearch_client import get_client

def get_alias_state(alias: str):
    es = get_client()
    alias_data = es.indices.get_alias(name=alias)
    indices = []
    write_index = None
    for idx, meta in alias_data.items():
        is_write = meta["aliases"][alias].get("is_write_index", False)
        indices.append({"index": idx, "is_write_index": is_write})
        if is_write:
            write_index = idx
    explain = None
    if write_index:
        try:
            explain_raw = es.transport.perform_request("GET", f"/_plugins/_ism/explain/{write_index}")
            explain = explain_raw.get(write_index)
        except Exception:
            explain = {"error": "explain_failed"}
    return {"alias": alias, "indices": indices, "write_index": write_index, "explain": explain}