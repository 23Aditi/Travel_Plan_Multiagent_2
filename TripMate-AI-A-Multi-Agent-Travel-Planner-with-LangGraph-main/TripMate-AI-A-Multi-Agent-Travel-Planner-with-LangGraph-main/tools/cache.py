import time
from typing import Any, Optional, Dict

class SimpleTTLCache:
    """Lightweight in-memory cache with Time-To-Live (TTL) expiration."""
    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0

    def _normalize_key(self, key: str) -> str:
        return key.strip().lower()

    def get(self, key: str) -> Optional[Any]:
        normalized = self._normalize_key(key)
        entry = self._store.get(normalized)
        if not entry:
            self.misses += 1
            return None

        if time.time() > entry["expires_at"]:
            del self._store[normalized]
            self.misses += 1
            return None

        self.hits += 1
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        normalized = self._normalize_key(key)
        ttl = ttl if ttl is not None else self.default_ttl
        self._store[normalized] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    def stats(self) -> Dict[str, int]:
        return {
            "cached_entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses
        }

# Global tool cache instance
tool_cache = SimpleTTLCache(default_ttl_seconds=3600)
