#!/usr/bin/env python3
"""Fetch a random poem page from hor.de and store raw HTML."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

DEFAULT_SOURCE_URL = "https://hor.de/gedichte/gedicht.php"


@dataclass(frozen=True)
class FetchResult:
    source_url: str
    final_url: str
    status_code: int
    fetched_at: str
    html_path: Path
    metadata_path: Path


def build_slug(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "gedicht"
    slug = path.replace("/", "__").replace(".htm", "").replace(".html", "")
    return slug


def fetch_poem(source_url: str, output_dir: Path, timeout_s: int) -> FetchResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(source_url, timeout=timeout_s, allow_redirects=True)
    response.raise_for_status()

    fetched_at = datetime.now(timezone.utc).isoformat()
    slug = build_slug(response.url)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    html_path = output_dir / f"{timestamp}__{slug}.html"
    metadata_path = output_dir / f"{timestamp}__{slug}.json"

    html_path.write_text(response.text, encoding=response.encoding or "utf-8")

    metadata = {
        "source_url": source_url,
        "final_url": response.url,
        "status_code": response.status_code,
        "fetched_at": fetched_at,
        "html_file": html_path.name,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    return FetchResult(
        source_url=source_url,
        final_url=response.url,
        status_code=response.status_code,
        fetched_at=fetched_at,
        html_path=html_path,
        metadata_path=metadata_path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a random poem HTML page from hor.de",
    )
    parser.add_argument(
        "--source-url",
        default=DEFAULT_SOURCE_URL,
        help="Source URL that redirects to a poem",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory to store raw HTML and metadata",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Request timeout in seconds",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = fetch_poem(args.source_url, Path(args.output_dir), args.timeout)

    print("Fetched poem HTML")
    print(f"  Source URL: {result.source_url}")
    print(f"  Final URL:  {result.final_url}")
    print(f"  Saved HTML: {result.html_path}")
    print(f"  Metadata:   {result.metadata_path}")


if __name__ == "__main__":
    main()
