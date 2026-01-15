from __future__ import annotations

from typing import List, Optional

from core.models import Chunk


def chunk_poem_lines(text: str, max_chars_per_chunk: Optional[int] = None) -> List[Chunk]:
    lines = [line.rstrip() for line in text.split("\n")]
    chunks: List[Chunk] = []
    current_lines: List[str] = []

    def flush() -> None:
        nonlocal chunks, current_lines
        if not current_lines:
            return
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append(
                Chunk(
                    index=len(chunks),
                    text=chunk_text,
                    estimated_duration=_estimate_duration(chunk_text),
                )
            )
        current_lines = []

    for line in lines:
        if line == "":
            flush()
            continue
        if max_chars_per_chunk:
            if sum(len(l) for l in current_lines) + len(line) + 1 > max_chars_per_chunk:
                flush()
        current_lines.append(line)
    flush()
    return chunks


def _estimate_duration(text: str) -> float:
    words = [w for w in text.split() if w]
    words_per_minute = 150
    return max(1.0, len(words) / words_per_minute * 60)
