#!/usr/bin/env python3
"""Parse the LLM response into structured prompts for downstream steps."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ParsedLLMResponse:
    atmosphere: dict[str, Any]
    chunk_prompts: list[dict[str, Any]]
    raw_message: str


def extract_json(content: str) -> dict[str, Any] | None:
    content = content.strip()
    if not content:
        return None

    if content.startswith("{") and content.endswith("}"):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    fence = "```"
    if fence in content:
        parts = content.split(fence)
        for part in parts:
            stripped = part.strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    continue
    return None


def strip_message_wrappers(content: str) -> str:
    tokens = ["<|message|>", "<|channel|>", "<|constrain|>", "<|final|>", "<|assistant|>"]
    for token in tokens:
        if token in content:
            content = content.replace(token, " ")
    return content.strip()


def parse_llm_response(response_json: dict[str, Any]) -> ParsedLLMResponse:
    message = response_json.get("message", "")
    if not message and isinstance(response_json.get("response"), dict):
        choices = response_json["response"].get("choices", [])
        if choices:
            message = choices[0].get("message", {}).get("content", "")
    cleaned = strip_message_wrappers(message)
    parsed = extract_json(cleaned)

    if parsed is None:
        return ParsedLLMResponse(atmosphere={}, chunk_prompts=[], raw_message=message)

    atmosphere = parsed.get("atmosphere", {})
    chunk_prompts = parsed.get("chunk_prompts", [])

    return ParsedLLMResponse(
        atmosphere=atmosphere,
        chunk_prompts=chunk_prompts,
        raw_message=message,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse LLM response JSON into structured prompts",
    )
    parser.add_argument("llm_response", help="Path to .llm_response.json")
    parser.add_argument(
        "--output",
        help="Optional output JSON path (defaults next to input)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.llm_response)
    response = json.loads(input_path.read_text(encoding="utf-8"))

    parsed = parse_llm_response(response)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".parsed.json")
    output_payload = {
        "atmosphere": parsed.atmosphere,
        "chunk_prompts": parsed.chunk_prompts,
        "raw_message": parsed.raw_message,
    }
    output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Parsed LLM response")
    print(f"  Input JSON:  {input_path}")
    print(f"  Output JSON: {output_path}")
    print(f"  Prompts:     {len(parsed.chunk_prompts)}")


if __name__ == "__main__":
    main()
