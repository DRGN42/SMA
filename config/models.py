from __future__ import annotations

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "lmstudio"
    base_url: str = "http://192.168.178.54:1234/v1"
    model: str = "openai/gpt-oss-20b"


class TTSConfig(BaseModel):
    provider: str = "dummy"
    voice_id: str = "poemvoice"
    speed: float = 1.0
    higgs_url: str = "http://localhost:8000"


class T2IConfig(BaseModel):
    provider: str = "dummy"
    width: int = 1080
    height: int = 1920
    steps: int = 6
    cfg: float = 2.0
    sampler: str = "euler"


class VideoConfig(BaseModel):
    fps: int = 30
    music_glob: str = "assets/ambient/ambient*.mp3"


class ContentConfig(BaseModel):
    source: str = "hor_de"
    base_url: str = "https://hor.de/gedichte/gedicht.php"


class ChunkingConfig(BaseModel):
    max_chars_per_chunk: int | None = None


class OutputConfig(BaseModel):
    root_dir: str = "outputs"
    dedupe_store: str = "outputs/dedupe.json"


class AppConfig(BaseModel):
    content: ContentConfig = Field(default_factory=ContentConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    t2i: T2IConfig = Field(default_factory=T2IConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    dry_run: bool = False
