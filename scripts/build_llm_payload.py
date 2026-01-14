#!/usr/bin/env python3
"""Build an LLM prompt payload from chunked poem JSON."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptConfig:
    tone_hint: str
    image_style: str
    max_prompt_words: int


def build_payload(chunked: dict, config: PromptConfig) -> dict:
    base_info = {
        "author": chunked.get("author", ""),
        "title": chunked.get("title", ""),
        "text": chunked.get("text", ""),
        "lines": chunked.get("lines", []),
    }

    system_prompt = (
        "Du bist ein kreativer Assistent für Gedicht-Visualisierungen. "
        "Analysiere zuerst die Gesamtatmosphäre des Gedichts. "
        "Erstelle danach pro Chunk einen präzisen Bildprompt für eine Text-zu-Bild-KI."
    )

    user_prompt = {
        "task": "poem_to_visuals",
        "tone_hint": config.tone_hint,
        "image_style": config.image_style,
        "max_prompt_words": config.max_prompt_words,
        "poem": base_info,
        "chunks": chunked.get("chunks", []),
        "output_schema": {
            "atmosphere": {
                "mood": "string",
                "themes": ["string"],
                "color_palette": ["string"],
                "style": "string",
            },
            "chunk_prompts": [
                {
                    "index": "int",
                    "prompt": "string",
                    "negative_prompt": "string",
                }
            ],
        },
    }

    return {
        "system": system_prompt,
        "user": user_prompt,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an LLM prompt payload from chunked poem JSON",
    )
    parser.add_argument("chunked_json", help="Path to chunked poem JSON")
    parser.add_argument(
        "--tone-hint",
        default="poetisch, bildhaft, emotional",
        help="High-level tone guidance for the LLM",
    )
    parser.add_argument(
        "--image-style",
        default="cinematic, soft lighting, high detail",
        help="Style hint for image prompts",
    )
    parser.add_argument(
        "--max-prompt-words",
        type=int,
        default=40,
        help="Target max words per image prompt",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON path (defaults next to input)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.chunked_json)
    chunked = json.loads(input_path.read_text(encoding="utf-8"))
    config = PromptConfig(
        tone_hint=args.tone_hint,
        image_style=args.image_style,
        max_prompt_words=args.max_prompt_words,
    )

    payload = build_payload(chunked, config)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".llm.json")
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Built LLM payload")
    print(f"  Input JSON:  {input_path}")
    print(f"  Output JSON: {output_path}")


if __name__ == "__main__":
    main()
