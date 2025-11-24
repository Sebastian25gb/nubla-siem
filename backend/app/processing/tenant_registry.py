import json
import os
from pathlib import Path
from typing import Set

# Ruta por defecto relativa al repo; permite override por env
DEFAULT_TENANTS_PATH = os.getenv("TENANTS_REGISTRY_PATH", "config/tenants.json")


class TenantRegistry:
    def __init__(self, path: str = DEFAULT_TENANTS_PATH):
        self.path = Path(path)
        self._tenants: Set[str] = set()
        self._loaded = False

    def load(self) -> None:
        if not self.path.exists():
            # No existe: keep empty set and don't crash
            self._tenants = set()
            self._loaded = True
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                self._tenants = set(str(x).strip() for x in data if x is not None)
            else:
                self._tenants = set()
        except Exception:
            self._tenants = set()
        self._loaded = True

    def reload(self) -> None:
        self._loaded = False
        self.load()

    def all(self) -> Set[str]:
        if not self._loaded:
            self.load()
        return set(self._tenants)

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
