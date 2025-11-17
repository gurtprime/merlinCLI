"""SQLite-backed cache manager."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import Any


class CacheManager:
    def __init__(self, sqlite_path: Path) -> None:
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at REAL
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.sqlite_path)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value)
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock, self._connect() as conn:
            conn.execute(
                "REPLACE INTO cache(cache_key, payload, expires_at) VALUES(?,?,?)",
                (key, payload, expires_at),
            )
            conn.commit()

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "SELECT payload, expires_at FROM cache WHERE cache_key = ?", (key,)
            )
            row = cur.fetchone()
        if row is None:
            return None
        payload, expires_at = row
        if expires_at and expires_at < now:
            self.delete(key)
            return None
        return json.loads(payload)

    def delete(self, key: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
            conn.commit()

    def clear(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
