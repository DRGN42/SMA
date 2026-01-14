#!/usr/bin/env python3
"""Generate TTS audio per chunk using a Higgs v2-compatible endpoint."""
from __future__ import annotations

import argparse
import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_ENDPOINT = "http://localhost:8002/v1/tts"


@dataclass(frozen=True)
class TTSConfig:
    mode: str
    endpoint: str
    voice: str
    audio_format: str
    sample_rate: int
    model_path: str
    tokenizer_path: str
    device: str


def request_tts_http(text: str, config: TTSConfig) -> bytes:
    payload = {
        "text": text,
        "voice": config.voice,
        "format": config.audio_format,
        "sample_rate": config.sample_rate,
    }
    response = requests.post(config.endpoint, json=payload, timeout=120)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("application/json"):
        data = response.json()
        audio_b64 = data.get("audio_base64") or data.get("audio")
        if not audio_b64:
            raise ValueError("TTS response JSON missing audio_base64")
        return base64.b64decode(audio_b64)

    return response.content


def request_tts_local(text: str, config: TTSConfig) -> tuple["torch.Tensor", int]:
    import torch
    import torchaudio

    from boson_multimodal.data_types import ChatMLSample, Message
    from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine

    system_prompt = (
        "Generate audio following instruction.\n\n"
        "<|scene_desc_start|>\n"
        "Audio is recorded from a quiet room.\n"
        "<|scene_desc_end|>"
    )

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=text),
    ]

    serve_engine = HiggsAudioServeEngine(
        config.model_path,
        config.tokenizer_path,
        device=config.device,
    )

    output = serve_engine.generate(
        chat_ml_sample=ChatMLSample(messages=messages),
        max_new_tokens=1024,
        temperature=0.3,
        top_p=0.95,
        top_k=50,
        stop_strings=["<|end_of_text|>", "<|eot_id|>"],
    )

    audio_tensor = torch.from_numpy(output.audio)[None, :]
    audio_tensor = torchaudio.functional.resample(
        audio_tensor,
        output.sampling_rate,
        config.sample_rate,
    )
    return audio_tensor, config.sample_rate


def build_manifest(
    source_json: Path,
    output_dir: Path,
    audio_files: list[dict[str, Any]],
    config: TTSConfig,
) -> dict[str, Any]:
    return {
        "source_json": source_json.name,
        "output_dir": str(output_dir),
        "mode": config.mode,
        "voice": config.voice,
        "format": config.audio_format,
        "sample_rate": config.sample_rate,
        "model_path": config.model_path,
        "tokenizer_path": config.tokenizer_path,
        "device": config.device,
        "audio_files": audio_files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate TTS audio per chunk",
    )
    parser.add_argument("chunked_json", help="Path to chunked poem JSON")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("TTS_ENDPOINT", DEFAULT_ENDPOINT),
        help="TTS HTTP endpoint",
    )
    parser.add_argument(
        "--mode",
        default=os.environ.get("TTS_MODE", "http"),
        choices=["http", "local"],
        help="TTS mode: http (endpoint) or local (Higgs v2 engine)",
    )
    parser.add_argument(
        "--voice",
        default=os.environ.get("TTS_VOICE", "poetry_female_01"),
        help="Voice identifier",
    )
    parser.add_argument(
        "--format",
        default="wav",
        help="Audio format (wav, mp3)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=22050,
        help="Sample rate in Hz",
    )
    parser.add_argument(
        "--output-dir",
        default="data/audio",
        help="Directory for audio outputs",
    )
    parser.add_argument(
        "--model-path",
        default=os.environ.get("HIGGS_MODEL", "bosonai/higgs-audio-v2-generation-3B-base"),
        help="Higgs v2 model path for local mode",
    )
    parser.add_argument(
        "--tokenizer-path",
        default=os.environ.get("HIGGS_TOKENIZER", "bosonai/higgs-audio-v2-tokenizer"),
        help="Higgs v2 tokenizer path for local mode",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("HIGGS_DEVICE", "cuda"),
        help="Device for local mode (cuda or cpu)",
    )
    parser.add_argument(
        "--output",
        help="Optional manifest JSON path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.chunked_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chunked = json.loads(input_path.read_text(encoding="utf-8"))
    chunks = chunked.get("chunks", [])

    config = TTSConfig(
        mode=args.mode,
        endpoint=args.endpoint,
        voice=args.voice,
        audio_format=args.format,
        sample_rate=args.sample_rate,
        model_path=args.model_path,
        tokenizer_path=args.tokenizer_path,
        device=args.device,
    )

    audio_files: list[dict[str, Any]] = []
    stem = input_path.stem
    for chunk in chunks:
        index = chunk.get("index")
        text = chunk.get("text", "")
        if not text:
            continue
        filename = f"{stem}__chunk{int(index):03d}.{config.audio_format}"
        audio_path = output_dir / filename
        if config.mode == "local":
            import torchaudio

            audio_tensor, sample_rate = request_tts_local(text, config)
            torchaudio.save(str(audio_path), audio_tensor, sample_rate)
        else:
            audio_bytes = request_tts_http(text, config)
            audio_path.write_bytes(audio_bytes)
        audio_files.append(
            {
                "index": index,
                "text": text,
                "file": audio_path.name,
            }
        )

    manifest = build_manifest(input_path, output_dir, audio_files, config)
    output_path = Path(args.output) if args.output else output_dir / f"{stem}.tts.json"
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("TTS audio generated")
    print(f"  Input JSON:  {input_path}")
    print(f"  Output dir:  {output_dir}")
    print(f"  Manifest:    {output_path}")
    print(f"  Files:       {len(audio_files)}")


if __name__ == "__main__":
    main()
