from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from time import time
from typing import Any

from app.config import get_settings


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, default_ttl_seconds: int, max_entries: int = 512) -> None:
        self.default_ttl_seconds = max(1, default_ttl_seconds)
        self.max_entries = max_entries
        self._entries: dict[str, CacheEntry] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            if entry.expires_at <= time():
                self._entries.pop(key, None)
                return None
            return deepcopy(entry.value)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> Any:
        with self._lock:
            self._prune_expired_locked()
            if len(self._entries) >= self.max_entries:
                oldest_key = min(self._entries, key=lambda item_key: self._entries[item_key].expires_at)
                self._entries.pop(oldest_key, None)

            ttl = max(1, ttl_seconds or self.default_ttl_seconds)
            stored_value = deepcopy(value)
            self._entries[key] = CacheEntry(value=stored_value, expires_at=time() + ttl)
            return deepcopy(stored_value)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            targets = [key for key in self._entries if key.startswith(prefix)]
            for key in targets:
                self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _prune_expired_locked(self) -> None:
        now = time()
        expired = [key for key, entry in self._entries.items() if entry.expires_at <= now]
        for key in expired:
            self._entries.pop(key, None)


settings = get_settings()
api_cache = TTLCache(default_ttl_seconds=getattr(settings, "temp_cache_ttl_seconds", 20))
