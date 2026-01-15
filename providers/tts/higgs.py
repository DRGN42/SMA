from __future__ import annotations

import base64
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import shutil

import requests

from providers.base import TTSProvider


class HiggsTTS(TTSProvider):
    def __init__(
        self,
        service_url: str,
        voice_id: str,
        mode: str = "cli",
        command_template: str | None = None,
        voice_wav_path: str | None = None,
        voice_text_path: str | None = None,
        endpoint: str = "/synthesize",
        timeout_s: int = 120,
    ):
        self.service_url = service_url.rstrip("/")
        self.voice_id = voice_id
        self.mode = mode
        self.command_template = command_template
        self.voice_wav_path = voice_wav_path
        self.voice_text_path = voice_text_path
        self.endpoint = endpoint
        self.timeout_s = timeout_s

    def synthesize(self, text: str, voice_id: str, speed: float, output_wav_path: str) -> str:
        if self.mode == "http":
            return self._synthesize_http(text, voice_id, speed, output_wav_path)
        if self.mode == "cli":
            return self._synthesize_cli(text, voice_id, speed, output_wav_path)
        raise ValueError(f"Unsupported Higgs mode: {self.mode}")

    def _synthesize_cli(self, text: str, voice_id: str, speed: float, output_wav_path: str) -> str:
        if not self.command_template:
            raise ValueError("Higgs CLI mode requires command_template")
        output_path = Path(output_wav_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as handle:
            handle.write(text)
            text_path = handle.name

        try:
            command = self.command_template.format_map(
                {
                    "text": text,
                    "text_path": text_path,
                    "voice_id": voice_id or self.voice_id,
                    "voice_wav": self.voice_wav_path or "",
                    "voice_text": self.voice_text_path or "",
                    "output_path": str(output_path),
                    "speed": speed,
                }
            )
            args = shlex.split(command, posix=os.name != "nt")
            executable = args[0] if args else ""
            if executable and not (Path(executable).exists() or shutil.which(executable)):
                raise FileNotFoundError(
                    f"Higgs CLI not found: {executable}. "
                    "Provide a full path in higgs_command or add it to PATH."
                )
            subprocess.run(args, check=True)
        finally:
            try:
                os.unlink(text_path)
            except FileNotFoundError:
                pass
        return str(output_path)

    def _synthesize_http(self, text: str, voice_id: str, speed: float, output_wav_path: str) -> str:
        url = f"{self.service_url}{self.endpoint}"
        files = {}
        data = {
            "text": text,
            "voice_id": voice_id or self.voice_id,
            "speed": speed,
        }
        if self.voice_wav_path and Path(self.voice_wav_path).exists():
            files["voice_wav"] = open(self.voice_wav_path, "rb")
        if self.voice_text_path and Path(self.voice_text_path).exists():
            files["voice_text"] = open(self.voice_text_path, "rb")
        try:
            response = requests.post(url, data=data, files=files or None, timeout=self.timeout_s)
            response.raise_for_status()
        finally:
            for handle in files.values():
                handle.close()

        output_path = Path(output_wav_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content_type = response.headers.get("Content-Type", "")
        if "audio" in content_type:
            output_path.write_bytes(response.content)
            return str(output_path)

        payload = response.json()
        if "audio_base64" in payload:
            output_path.write_bytes(base64.b64decode(payload["audio_base64"]))
            return str(output_path)
        if "audio_url" in payload:
            audio_response = requests.get(payload["audio_url"], timeout=self.timeout_s)
            audio_response.raise_for_status()
            output_path.write_bytes(audio_response.content)
            return str(output_path)

        raise ValueError("Higgs HTTP response did not include audio content")
