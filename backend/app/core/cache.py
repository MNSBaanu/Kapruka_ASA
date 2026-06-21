from time import time
from typing import Any
from app.config import settings


class TTLCache:
    def __init__(self, ttl: int = settings.cache_ttl_seconds):
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        expires_at, value = self._store[key]
        if time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time() + self._ttl, value)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


mcp_cache = TTLCache()
