import json
from pathlib import Path

DEFAULT_MAP_PATH = Path("config/host_tenant_map.json")


def load_mapping(path: Path = DEFAULT_MAP_PATH) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k.lower(): v for k, v in data.items()}
    except Exception:
        return {}
    return {}


HOST_TENANT_MAP = load_mapping()


def map_host_to_tenant(host: str) -> str | None:
    if not host:
        return None
    key = host.strip().lower().replace(" ", "-")
    return HOST_TENANT_MAP.get(key)
