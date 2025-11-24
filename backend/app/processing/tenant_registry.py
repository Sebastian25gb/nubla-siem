import json
import os
from pathlib import Path
from typing import Any, Dict, Set

# Ruta por defecto relativa al repo; permite override por env
DEFAULT_TENANTS_PATH = os.getenv("TENANTS_REGISTRY_PATH", "config/tenants.json")


class TenantRegistry:
    def __init__(self, path: str = DEFAULT_TENANTS_PATH):
        self.path = Path(path)
        self._tenants: Set[str] = set()
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        if not self.path.exists():
            self._tenants = set()
            self._meta = {}
            self._loaded = True
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                parsed_set: Set[str] = set()
                meta: Dict[str, Dict[str, Any]] = {}
                for item in data:
                    if isinstance(item, str):
                        tid = item.strip()
                        if tid:
                            parsed_set.add(tid)
                    elif isinstance(item, dict) and "id" in item:
                        tid = str(item["id"]).strip()
                        if tid:
                            parsed_set.add(tid)
                            meta[tid] = item
                self._tenants = parsed_set
                self._meta = meta
            else:
                self._tenants = set()
                self._meta = {}
        except Exception:
            self._tenants = set()
            self._meta = {}
        self._loaded = True

    def reload(self) -> None:
        self._loaded = False
        self.load()

    def all(self) -> Set[str]:
        if not self._loaded:
            self.load()
        return set(self._tenants)

    def metadata(self, tenant_id: str) -> Dict[str, Any]:
        if not self._loaded:
            self.load()
        return dict(self._meta.get(tenant_id, {}))

    def is_valid(self, tenant_id: str) -> bool:
        if not tenant_id or not isinstance(tenant_id, str):
            return False
        if not self._loaded:
            self.load()
        return tenant_id in self._tenants


# Singleton-ish instance for simple imports
_registry = TenantRegistry()


def get_registry() -> TenantRegistry:
    return _registry


def is_valid_tenant(tenant_id: str) -> bool:
    return get_registry().is_valid(tenant_id)
