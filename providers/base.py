from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from core.models import Chunk, ChunkVisualPrompt, GlobalVisualBible, Poem


class ContentSource(ABC):
    @abstractmethod
    def fetch_random_poem(self) -> Poem:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    def generate_global_visual_bible(self, poem: Poem) -> GlobalVisualBible:
        raise NotImplementedError

    @abstractmethod
    def generate_chunk_prompts(
        self, poem: Poem, chunks: List[Chunk], bible: GlobalVisualBible
    ) -> List[ChunkVisualPrompt]:
        raise NotImplementedError


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, voice_id: str, speed: float, output_wav_path: str) -> str:
        raise NotImplementedError


class T2IProvider(ABC):
    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: Optional[int],
        steps: int,
        cfg: float,
        sampler: str,
        output_path: str,
    ) -> str:
        raise NotImplementedError


class AnimationProvider(ABC):
    @abstractmethod
    def animate_images(self, image_paths: List[str], motion_plan: List[str]) -> List[str]:
        raise NotImplementedError


class VideoComposer(ABC):
    @abstractmethod
    def compose(
        self,
        image_paths: List[str],
        audio_paths: List[str],
        subtitles_path: str,
        output_path: str,
        music_path: Optional[str] = None,
        fps: int = 30,
    ) -> str:
        raise NotImplementedError


class StorageProvider(ABC):
    @abstractmethod
    def is_recent_url(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def mark_url_used(self, url: str) -> None:
        raise NotImplementedError


class Publisher(ABC):
    @abstractmethod
    def publish(self, video_path: str, metadata_path: str) -> None:
        raise NotImplementedError
