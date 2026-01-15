from __future__ import annotations

import html
import re
from typing import Optional

from bs4 import BeautifulSoup

from core.models import Poem


def _clean_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_poem_html(url: str, html_content: str) -> Poem:
    soup = BeautifulSoup(html_content, "lxml")
    title = _extract_title(soup)
    author = _extract_author(soup)
    poem_text = _extract_poem_text(soup)
    return Poem(url=url, title=title, author=author, text=poem_text)


def _extract_title(soup: BeautifulSoup) -> str:
    title = ""
    if soup.title and soup.title.text:
        title = soup.title.text.strip()
    if " - " in title:
        title = title.split(" - ")[-1].strip()
    if not title:
        bold = soup.find("b")
        if bold and bold.text:
            title = bold.text.strip()
    return title or "Unbekannter Titel"


def _extract_author(soup: BeautifulSoup) -> str:
    meta_author = soup.find("meta", attrs={"name": "Author"})
    if meta_author and meta_author.get("content"):
        return meta_author["content"].strip()
    author_link = soup.find("a", href=re.compile(r"/gedichte/"))
    if author_link and author_link.text:
        return author_link.text.strip()
    heading = soup.find(["h1", "h2", "h3"])
    if heading and heading.text:
        return heading.text.strip()
    return "Unbekannter Autor"


def _extract_poem_text(soup: BeautifulSoup) -> str:
    paragraphs = [p for p in soup.find_all("p") if p.text]
    text_blocks = []
    for p in paragraphs:
        text = p.get_text("\n", strip=False)
        text = _clean_text(text)
        if not text:
            continue
        if text_blocks:
            text_blocks.append("")
        text_blocks.append(text)
    return _clean_text("\n".join(text_blocks)) or ""
