#!/usr/bin/env python3
"""Parse a single hor.de poem HTML file into normalized JSON."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

SKIP_TITLE_CANDIDATES = {
    "Gedichtsammlung",
}


@dataclass(frozen=True)
class ParsedPoem:
    source_html: str
    author: str
    title: str
    text: str
    lines: list[str]


def normalize_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]


def parse_poem_html(html_path: Path) -> ParsedPoem:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    author_meta = soup.find("meta", attrs={"name": "Author"})
    author = author_meta.get("content", "").strip() if author_meta else ""

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title = title_text.split(" - ")[-1].strip() if " - " in title_text else title_text

    title_bold = soup.find("p")
    for p in soup.find_all("p"):
        bold = p.find("b")
        if not bold:
            continue
        candidate = bold.get_text(strip=True)
        if not candidate or candidate in SKIP_TITLE_CANDIDATES:
            continue
        title = candidate or title
        title_bold = p
        break

    poem_lines: list[str] = []
    if title_bold:
        for sibling in title_bold.find_all_next("p"):
            if sibling.find("a") and sibling.get_text(strip=True).endswith("index.html"):
                continue
            text = sibling.get_text("\n", strip=True)
            if text:
                poem_lines.extend(text.splitlines())

    text = "\n".join(normalize_lines("\n".join(poem_lines)))
    lines = normalize_lines(text)

    return ParsedPoem(
        source_html=html_path.name,
        author=author,
        title=title,
        text=text,
        lines=lines,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a single poem HTML file into JSON",
    )
    parser.add_argument("html_path", help="Path to the raw HTML file")
    parser.add_argument(
        "--output",
        help="Optional output JSON path (defaults next to HTML)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    html_path = Path(args.html_path)
    parsed = parse_poem_html(html_path)

    output_path = Path(args.output) if args.output else html_path.with_suffix(".json")
    output_path.write_text(
        json.dumps(parsed.__dict__, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Parsed poem HTML")
    print(f"  Source HTML: {parsed.source_html}")
    print(f"  Author:      {parsed.author}")
    print(f"  Title:       {parsed.title}")
    print(f"  Output JSON: {output_path}")


if __name__ == "__main__":
    main()
