from __future__ import annotations

from providers.base import TTSProvider


class HiggsTTS(TTSProvider):
    def __init__(self, service_url: str, voice_id: str):
        self.service_url = service_url
        self.voice_id = voice_id

    def synthesize(self, text: str, voice_id: str, speed: float, output_wav_path: str) -> str:
        raise NotImplementedError(
            "Higgs Audio v2 Integration ist ein Stub. "
            "Verbinde hier deine lokale Higgs-API oder CLI."
        )
