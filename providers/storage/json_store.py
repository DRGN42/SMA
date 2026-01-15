from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from providers.base import StorageProvider


class JsonURLStore(StorageProvider):
    def __init__(self, path: str, ttl_days: int = 30):
        self.path = Path(path)
        self.ttl_days = ttl_days
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def is_recent_url(self, url: str) -> bool:
        data = self._load()
        if url not in data:
            return False
        last_used = datetime.fromisoformat(data[url])
        return datetime.utcnow() - last_used < timedelta(days=self.ttl_days)

    def mark_url_used(self, url: str) -> None:
        data = self._load()
        data[url] = datetime.utcnow().isoformat()
        self._save(data)

    def _load(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
