from __future__ import annotations

from providers.base import Publisher


class NoopPublisher(Publisher):
    def publish(self, video_path: str, metadata_path: str) -> None:
        return None
