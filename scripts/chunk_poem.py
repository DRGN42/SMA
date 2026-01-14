#!/usr/bin/env python3
"""Chunk parsed poem JSON into line groups for downstream TTS + image prompts."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChunkConfig:
    lines_per_chunk: int


def chunk_lines(lines: list[str], lines_per_chunk: int) -> list[dict]:
    if lines_per_chunk < 1:
        raise ValueError("lines_per_chunk must be >= 1")

    chunks: list[dict] = []
    index = 1
    for start in range(0, len(lines), lines_per_chunk):
        segment = lines[start : start + lines_per_chunk]
        if not segment:
            continue
        chunks.append(
            {
                "index": index,
                "start_line": start + 1,
                "end_line": start + len(segment),
                "lines": segment,
                "text": "\n".join(segment),
            }
        )
        index += 1
    return chunks


def build_output(parsed: dict, config: ChunkConfig) -> dict:
    lines = parsed.get("lines") or []
    chunks = chunk_lines(lines, config.lines_per_chunk)

    return {
        "source_html": parsed.get("source_html", ""),
        "author": parsed.get("author", ""),
        "title": parsed.get("title", ""),
        "text": parsed.get("text", ""),
        "lines": lines,
        "chunk_config": {
            "lines_per_chunk": config.lines_per_chunk,
        },
        "chunks": chunks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk parsed poem JSON into line groups",
    )
    parser.add_argument("parsed_json", help="Path to parsed poem JSON")
    parser.add_argument(
        "--lines-per-chunk",
        type=int,
        default=2,
        help="Number of lines per chunk",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON path (defaults next to input)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.parsed_json)
    parsed = json.loads(input_path.read_text(encoding="utf-8"))
    config = ChunkConfig(lines_per_chunk=args.lines_per_chunk)

    output = build_output(parsed, config)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".chunked.json")
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Chunked poem JSON")
    print(f"  Input JSON:  {input_path}")
    print(f"  Output JSON: {output_path}")
    print(f"  Chunks:      {len(output['chunks'])}")


if __name__ == "__main__":
    main()
