#!/usr/bin/env python3
"""Send the LLM payload to an OpenAI-compatible chat completion endpoint."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_ENDPOINT = "http://localhost:8000/v1/chat/completions"


@dataclass(frozen=True)
class LLMConfig:
    endpoint: str
    model: str
    api_key: str | None
    temperature: float
    max_tokens: int


def build_headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def call_llm(payload: dict[str, Any], config: LLMConfig) -> dict[str, Any]:
    body = {
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": payload.get("system", "")},
            {"role": "user", "content": json.dumps(payload.get("user", {}), ensure_ascii=False)},
        ],
    }

    response = requests.post(
        config.endpoint,
        headers=build_headers(config.api_key),
        json=body,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def extract_message(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return message.get("content", "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LLM inference for a prompt payload",
    )
    parser.add_argument("payload_json", help="Path to .llm.json payload")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("LLM_ENDPOINT", DEFAULT_ENDPOINT),
        help="OpenAI-compatible chat completion endpoint",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LLM_MODEL", "openai/gpt-oss-20b"),
        help="Model name",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("LLM_API_KEY"),
        help="API key (optional for local servers)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.4,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Max tokens for the response",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON path (defaults next to input)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload_path = Path(args.payload_json)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    config = LLMConfig(
        endpoint=args.endpoint,
        model=args.model,
        api_key=args.api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    response_json = call_llm(payload, config)
    message = extract_message(response_json)

    output_path = Path(args.output) if args.output else payload_path.with_suffix(".llm_response.json")
    output_payload = {
        "request": {
            "endpoint": config.endpoint,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        },
        "response": response_json,
        "message": message,
    }
    output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("LLM response saved")
    print(f"  Input JSON:  {payload_path}")
    print(f"  Output JSON: {output_path}")


if __name__ == "__main__":
    main()
