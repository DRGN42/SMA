from __future__ import annotations

import os
from pathlib import Path

import yaml

from config.models import AppConfig


def load_config(path: str) -> AppConfig:
    config_path = Path(path)
    payload = {}
    if config_path.exists():
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    env_overrides = {
        "llm": {
            "base_url": os.getenv("LLM_BASE_URL"),
            "model": os.getenv("LLM_MODEL"),
        },
        "tts": {
            "provider": os.getenv("TTS_PROVIDER"),
            "voice_id": os.getenv("TTS_VOICE_ID"),
            "higgs_url": os.getenv("TTS_HIGGS_URL"),
        },
        "t2i": {
            "provider": os.getenv("T2I_PROVIDER"),
        },
    }
    payload = _merge(payload, env_overrides)
    return AppConfig.model_validate(payload)


def _merge(base: dict, overrides: dict) -> dict:
    for key, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, dict):
            base[key] = _merge(base.get(key, {}), value)
        else:
            base[key] = value
    return base
