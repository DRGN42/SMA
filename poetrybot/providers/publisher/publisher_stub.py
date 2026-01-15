"""
Publisher provider stub for social media integration.
To be implemented later with Postiz or direct API integration.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

from core.interfaces import IPublisherProvider

logger = logging.getLogger(__name__)


class PostizPublisher(IPublisherProvider):
    """Publisher using Postiz for multi-platform posting."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:3000/api",
        api_key: str = ""
    ):
        self.api_url = api_url
        self.api_key = api_key
        logger.warning("PostizPublisher is a stub - not yet implemented")
    
    def publish(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """Publish video to configured platforms via Postiz."""
        logger.info(f"[STUB] Would publish: {video_path}")
        logger.info(f"[STUB] Title: {title}")
        logger.info(f"[STUB] Tags: {tags}")
        
        return {
            "status": "stub",
            "message": "Publisher not yet implemented",
            "would_publish_to": ["tiktok", "youtube_shorts", "instagram"]
        }
