"""
Storage provider for file management and deduplication.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Set, Optional
import hashlib

from core.interfaces import IStorageProvider

logger = logging.getLogger(__name__)


class FileManager(IStorageProvider):
    """File storage manager with deduplication tracking."""
    
    def __init__(
        self,
        base_dir: str = "outputs",
        dedup_file: str = "processed_urls.json"
    ):
        self.base_dir = Path(base_dir)
        self.dedup_file = Path(dedup_file)
        self._current_run_dir: Optional[Path] = None
        self._processed_urls: Set[str] = set()
        
        self._load_processed_urls()
    
    @property
    def current_run_dir(self) -> Path:
        """Get current run directory, creating if needed."""
        if self._current_run_dir is None:
            self._current_run_dir = self.create_run_directory()
        return self._current_run_dir
    
    def create_run_directory(self) -> Path:
        """Create timestamped output directory."""
        now = datetime.now()
        date_dir = self.base_dir / now.strftime("%Y-%m-%d")
        run_dir = date_dir / f"run_{now.strftime('%H%M%S')}"
        
        run_dir.mkdir(parents=True, exist_ok=True)
        
        (run_dir / "images").mkdir(exist_ok=True)
        (run_dir / "audio").mkdir(exist_ok=True)
        (run_dir / "work").mkdir(exist_ok=True)
        
        self._current_run_dir = run_dir
        logger.info(f"Created run directory: {run_dir}")
        
        return run_dir
    
    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Save data as JSON file in current run directory."""
        output_path = self.current_run_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"Saved JSON: {output_path}")
        return output_path
    
    def is_duplicate(self, url: str) -> bool:
        """Check if poem URL was already processed."""
        url_hash = self._hash_url(url)
        return url_hash in self._processed_urls
    
    def mark_processed(self, url: str) -> None:
        """Mark URL as processed."""
        url_hash = self._hash_url(url)
        self._processed_urls.add(url_hash)
        self._save_processed_urls()
        logger.info(f"Marked as processed: {url}")
    
    def _hash_url(self, url: str) -> str:
        """Create hash of URL for deduplication."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _load_processed_urls(self):
        """Load set of processed URL hashes."""
        if self.dedup_file.exists():
            with open(self.dedup_file, "r") as f:
                data = json.load(f)
                self._processed_urls = set(data.get("urls", []))
            logger.info(f"Loaded {len(self._processed_urls)} processed URLs")
    
    def _save_processed_urls(self):
        """Save set of processed URL hashes."""
        with open(self.dedup_file, "w") as f:
            json.dump({"urls": list(self._processed_urls)}, f)
