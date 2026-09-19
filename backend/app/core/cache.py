from time import time
from typing import Any
from app.config import settings

MAX_ENTRIES = 2000


class TTLCache:
    def __init__(self, ttl: int = settings.cache_ttl_seconds, max_entries: int = MAX_ENTRIES):
        self._ttl = ttl
        self._max_entries = max_entries
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        expires_at, value = self._store[key]
        if time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if len(self._store) >= self._max_entries:
            self._evict()
        self._store[key] = (time() + (ttl or self._ttl), value)

    def _evict(self) -> None:
        now = time()
        for key in [k for k, (exp, _) in self._store.items() if exp < now]:
            del self._store[key]
        while len(self._store) >= self._max_entries:
            del self._store[next(iter(self._store))]

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


mcp_cache = TTLCache()
