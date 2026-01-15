from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Poem(BaseModel):
    url: str
    title: str
    author: str
    text: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    index: int
    text: str
    pause_ms: int = 0
    estimated_duration: float = 0.0


class GlobalVisualBible(BaseModel):
    overall_mood: str
    themes: List[str]
    setting: str
    era: str
    visual_style: str
    color_palette: List[str]
    camera: str
    symbols: List[str]
    negative_prompt: str
    social_style: str
    pacing: str


class ChunkVisualPrompt(BaseModel):
    index: int
    image_prompt: str
    negative_prompt: str
    recommended_motion: str
    on_screen_text: str


class PromptPlan(BaseModel):
    global_visual_bible: GlobalVisualBible
    chunk_prompts: List[ChunkVisualPrompt]


class RenderPlan(BaseModel):
    poem: Poem
    chunks: List[Chunk]
    prompts: PromptPlan
    output_dir: str
    images: List[str] = Field(default_factory=list)
    audio_files: List[str] = Field(default_factory=list)
    subtitles_path: Optional[str] = None
    final_video_path: Optional[str] = None
