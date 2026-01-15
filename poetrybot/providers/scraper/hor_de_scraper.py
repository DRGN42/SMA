"""
Scraper for hor.de German poetry website.
"""
from typing import Optional
import requests
from bs4 import BeautifulSoup
import html
import re
import logging
from datetime import datetime

from core.entities import Poem
from core.interfaces import IScraperProvider

logger = logging.getLogger(__name__)


class HorDeScraper(IScraperProvider):
    """Scraper implementation for hor.de poem website."""
    
    BASE_URL = "https://hor.de/gedichte/gedicht.php"
    TIMEOUT = 30
    
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_random_poem(self) -> Poem:
        """Fetch a random poem following redirects."""
        response = self.session.get(
            self.BASE_URL,
            allow_redirects=True,
            timeout=self.TIMEOUT
        )
        response.raise_for_status()
        
        final_url = response.url
        logger.info(f"Fetched poem from: {final_url}")
        
        return self._parse_poem(response.text, str(final_url))
    
    def fetch_poem_by_url(self, url: str) -> Poem:
        """Fetch a specific poem by URL."""
        response = self.session.get(url, timeout=self.TIMEOUT)
        response.raise_for_status()
        return self._parse_poem(response.text, url)
    
    def _parse_poem(self, html_content: str, source_url: str) -> Poem:
        """Parse HTML content and extract poem data."""
        soup = BeautifulSoup(html_content, "lxml")
        
        title = self._extract_title(soup)
        author = self._extract_author(soup)
        text = self._extract_text(soup)
        
        return Poem(
            author=author,
            title=title,
            text=text,
            source_url=source_url,
            scraped_at=datetime.now()
        )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from <title> or <b> tag."""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            title = re.sub(r"\s*-\s*hor\.de.*$", "", title)
            if title:
                return html.unescape(title)
        
        body = soup.find("body")
        if body:
            bold = body.find("b")
            if bold:
                return html.unescape(bold.get_text(strip=True))
        
        return "Unbekannt"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author from meta tag or body."""
        meta_author = soup.find("meta", attrs={"name": re.compile(r"author", re.I)})
        if meta_author and meta_author.get("content"):
            return html.unescape(meta_author["content"].strip())
        
        author_link = soup.find("a", href=re.compile(r"/gedichte/[^/]+/$"))
        if author_link:
            return html.unescape(author_link.get_text(strip=True))
        
        return "Unbekannt"
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract poem text from <p> blocks."""
        body = soup.find("body")
        if not body:
            return ""
        
        paragraphs = body.find_all("p")
        poem_lines = []
        
        for p in paragraphs:
            if self._is_navigation(p):
                continue
            
            text = self._get_text_with_breaks(p)
            if text.strip():
                poem_lines.append(text)
        
        full_text = "\n\n".join(poem_lines)
        return html.unescape(full_text).strip()
    
    def _is_navigation(self, element) -> bool:
        """Check if element is navigation/junk."""
        text = element.get_text().lower()
        nav_patterns = ["navigation", "zurück", "home", "copyright", "©", "impressum"]
        return any(p in text for p in nav_patterns)
    
    def _get_text_with_breaks(self, element) -> str:
        """Extract text preserving <br> as newlines."""
        for br in element.find_all("br"):
            br.replace_with("\n")
        return element.get_text()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = HorDeScraper()
    poem = scraper.fetch_random_poem()
    print(f"Titel: {poem.title}")
    print(f"Autor: {poem.author}")
    print(f"URL: {poem.source_url}")
    print(f"---\n{poem.text}")
