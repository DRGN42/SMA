from __future__ import annotations

import time
from typing import Optional

import requests

from core.parsing import parse_poem_html
from core.models import Poem
from providers.base import ContentSource


class HorDePoemSource(ContentSource):
    def __init__(self, base_url: str, timeout_s: int = 10, retries: int = 3, sleep_s: float = 1.5):
        self.base_url = base_url
        self.timeout_s = timeout_s
        self.retries = retries
        self.sleep_s = sleep_s

    def fetch_random_poem(self) -> Poem:
        last_exception: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            try:
                response = requests.get(self.base_url, timeout=self.timeout_s)
                response.raise_for_status()
                return parse_poem_html(response.url, response.text)
            except requests.RequestException as exc:
                last_exception = exc
                time.sleep(self.sleep_s * attempt)
        if last_exception:
            raise last_exception
        raise RuntimeError("Failed to fetch poem")
