from __future__ import annotations

import wave

from providers.base import TTSProvider


class DummyTTS(TTSProvider):
    def synthesize(self, text: str, voice_id: str, speed: float, output_wav_path: str) -> str:
        sample_rate = 44100
        duration_s = max(1.0, len(text) / 50.0)
        num_frames = int(sample_rate * duration_s)
        with wave.open(output_wav_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * num_frames)
        return output_wav_path
