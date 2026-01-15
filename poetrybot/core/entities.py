"""
Core domain entities for the Poetry Bot Pipeline.
These are pure data classes with no external dependencies.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MotionType(Enum):
    """Types of Ken-Burns motion effects."""
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    STATIC = "static"


@dataclass
class Poem:
    """Domain entity representing a scraped poem."""
    author: str
    title: str
    text: str
    source_url: str
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "author": self.author,
            "title": self.title,
            "text": self.text,
            "source_url": self.source_url,
            "scraped_at": self.scraped_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Poem":
        return cls(
            author=data["author"],
            title=data["title"],
            text=data["text"],
            source_url=data["source_url"],
            scraped_at=datetime.fromisoformat(data.get("scraped_at", datetime.now().isoformat()))
        )


@dataclass
class Chunk:
    """A segment of poem text for TTS and image generation."""
    index: int
    text: str
    pause_after_ms: int = 500
    estimated_duration_sec: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "text": self.text,
            "pause_after_ms": self.pause_after_ms,
            "estimated_duration_sec": self.estimated_duration_sec
        }


@dataclass
class VisualBible:
    """Global visual style guide for consistent image generation."""
    overall_mood: str
    themes: List[str]
    setting: str
    era: str
    visual_style: str
    color_palette: List[str]
    camera_style: str
    symbols: List[str]
    negative_prompt: str
    social_hook: str
    pacing: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_mood": self.overall_mood,
            "themes": self.themes,
            "setting": self.setting,
            "era": self.era,
            "visual_style": self.visual_style,
            "color_palette": self.color_palette,
            "camera_style": self.camera_style,
            "symbols": self.symbols,
            "negative_prompt": self.negative_prompt,
            "social_hook": self.social_hook,
            "pacing": self.pacing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualBible":
        return cls(**data)


@dataclass
class ChunkPrompt:
    """Per-chunk data for image generation and video assembly."""
    chunk_index: int
    image_prompt: str
    negative_prompt: str
    recommended_motion: MotionType
    subtitle_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "image_prompt": self.image_prompt,
            "negative_prompt": self.negative_prompt,
            "recommended_motion": self.recommended_motion.value,
            "subtitle_text": self.subtitle_text
        }


@dataclass
class AudioSegment:
    """Represents a generated TTS audio file with timing info."""
    chunk_index: int
    file_path: str
    duration_sec: float
    start_time_sec: float = 0.0


@dataclass
class ImageAsset:
    """Represents a generated image for a chunk."""
    chunk_index: int
    file_path: str
    width: int
    height: int
    prompt_used: str


@dataclass
class SubtitleEntry:
    """A single subtitle entry for SRT generation."""
    index: int
    start_time_sec: float
    end_time_sec: float
    text: str
    
    def to_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def to_srt(self) -> str:
        return f"{self.index}\n{self.to_srt_time(self.start_time_sec)} --> {self.to_srt_time(self.end_time_sec)}\n{self.text}\n"


@dataclass
class RenderPlan:
    """Complete plan for video rendering."""
    poem: Poem
    visual_bible: VisualBible
    chunks: List[Chunk]
    chunk_prompts: List[ChunkPrompt]
    audio_segments: List[AudioSegment] = field(default_factory=list)
    image_assets: List[ImageAsset] = field(default_factory=list)
    subtitles: List[SubtitleEntry] = field(default_factory=list)
    background_music_path: Optional[str] = None
    output_path: Optional[str] = None
