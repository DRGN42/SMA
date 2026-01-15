"""
Abstract interfaces for all pipeline providers.
Following Clean Architecture - core depends on nothing external.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from .entities import (
    Poem, Chunk, VisualBible, ChunkPrompt,
    AudioSegment, ImageAsset, RenderPlan
)


class IScraperProvider(ABC):
    """Interface for poem scraping."""
    
    @abstractmethod
    def fetch_random_poem(self) -> Poem:
        """Fetch a random poem from the source."""
        pass
    
    @abstractmethod
    def fetch_poem_by_url(self, url: str) -> Poem:
        """Fetch a specific poem by URL."""
        pass


class IChunkerProvider(ABC):
    """Interface for text chunking."""
    
    @abstractmethod
    def chunk_poem(self, poem: Poem, max_chars: int = 100) -> List[Chunk]:
        """Split poem text into chunks for TTS."""
        pass


class ILLMProvider(ABC):
    """Interface for LLM-based analysis."""
    
    @abstractmethod
    def generate_visual_bible(self, poem: Poem) -> VisualBible:
        """Analyze poem and generate global visual style guide."""
        pass
    
    @abstractmethod
    def generate_chunk_prompts(
        self, 
        chunks: List[Chunk], 
        visual_bible: VisualBible
    ) -> List[ChunkPrompt]:
        """Generate image prompts for each chunk."""
        pass


class ITTSProvider(ABC):
    """Interface for Text-to-Speech."""
    
    @abstractmethod
    def synthesize(
        self, 
        text: str, 
        output_path: Path,
        voice_sample: Optional[Path] = None
    ) -> AudioSegment:
        """Generate speech audio from text."""
        pass
    
    @abstractmethod
    def synthesize_chunks(
        self,
        chunks: List[Chunk],
        output_dir: Path,
        voice_sample: Optional[Path] = None
    ) -> List[AudioSegment]:
        """Generate audio for all chunks."""
        pass


class IT2IProvider(ABC):
    """Interface for Text-to-Image generation."""
    
    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        output_path: Path,
        width: int = 1080,
        height: int = 1920
    ) -> ImageAsset:
        """Generate a single image from prompt."""
        pass
    
    @abstractmethod
    def generate_chunk_images(
        self,
        chunk_prompts: List[ChunkPrompt],
        output_dir: Path
    ) -> List[ImageAsset]:
        """Generate images for all chunks."""
        pass


class IVideoRenderer(ABC):
    """Interface for video rendering."""
    
    @abstractmethod
    def render(self, plan: RenderPlan, output_path: Path) -> Path:
        """Render final video from all assets."""
        pass
    
    @abstractmethod
    def generate_subtitles(
        self,
        audio_segments: List[AudioSegment],
        chunks: List[Chunk],
        output_path: Path
    ) -> Path:
        """Generate SRT subtitle file."""
        pass


class IStorageProvider(ABC):
    """Interface for file storage and management."""
    
    @abstractmethod
    def create_run_directory(self) -> Path:
        """Create timestamped output directory."""
        pass
    
    @abstractmethod
    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Save data as JSON file."""
        pass
    
    @abstractmethod
    def is_duplicate(self, url: str) -> bool:
        """Check if poem URL was already processed."""
        pass
    
    @abstractmethod
    def mark_processed(self, url: str) -> None:
        """Mark URL as processed."""
        pass


class IPublisherProvider(ABC):
    """Interface for social media publishing (stub for later)."""
    
    @abstractmethod
    def publish(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """Publish video to platform. Returns platform response."""
        pass
