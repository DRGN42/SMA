from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import List

from config.models import AppConfig
from core.chunking import chunk_poem_lines
from core.models import Chunk, PromptPlan, RenderPlan
from providers.base import AnimationProvider, ContentSource, LLMProvider, T2IProvider, TTSProvider, VideoComposer
from providers.content.hor_de import HorDePoemSource
from providers.llm.lmstudio import LMStudioProvider
from providers.storage.json_store import JsonURLStore
from providers.tts.dummy import DummyTTS
from providers.tts.higgs import HiggsTTS
from providers.t2i.dummy import DummyT2I
from providers.animation.simple import PassthroughAnimation
from providers.video.ffmpeg_composer import FFMPEGComposer


def build_pipeline(config: AppConfig):
    source = HorDePoemSource(config.content.base_url)
    llm = LMStudioProvider(config.llm.base_url, config.llm.model)
    if config.tts.provider == "dummy":
        tts = DummyTTS()
    elif config.tts.provider == "higgs":
        tts = HiggsTTS(
            service_url=config.tts.higgs_url,
            voice_id=config.tts.voice_id,
            mode=config.tts.higgs_mode,
            command_template=config.tts.higgs_command,
            voice_wav_path=config.tts.voice_wav_path,
            voice_text_path=config.tts.voice_text_path,
            endpoint=config.tts.higgs_endpoint,
        )
    else:
        raise ValueError(f"Unsupported TTS provider: {config.tts.provider}")
    if config.t2i.provider == "dummy":
        t2i = DummyT2I()
    else:
        raise ValueError(f"Unsupported T2I provider: {config.t2i.provider}")
    animation = PassthroughAnimation()
    composer = FFMPEGComposer()
    dedupe = JsonURLStore(config.output.dedupe_store)
    return source, llm, tts, t2i, animation, composer, dedupe


def run_poem_pipeline(config: AppConfig, dry_run: bool = False) -> RenderPlan:
    source, llm, tts, t2i, animation, composer, dedupe = build_pipeline(config)

    poem = source.fetch_random_poem()
    if dedupe.is_recent_url(poem.url):
        poem = source.fetch_random_poem()
    dedupe.mark_url_used(poem.url)

    chunks = chunk_poem_lines(poem.text, config.chunking.max_chars_per_chunk)
    bible = llm.generate_global_visual_bible(poem)
    chunk_prompts = llm.generate_chunk_prompts(poem, chunks, bible)
    prompt_plan = PromptPlan(global_visual_bible=bible, chunk_prompts=chunk_prompts)

    output_dir = _prepare_output_dir(config.output.root_dir)
    _write_json(output_dir / "poem.json", poem.model_dump())
    _write_json(output_dir / "global_visual_bible.json", bible.model_dump())
    _write_json(output_dir / "chunks.json", [chunk.model_dump() for chunk in chunks])

    if dry_run or config.dry_run:
        return RenderPlan(poem=poem, chunks=chunks, prompts=prompt_plan, output_dir=str(output_dir))

    images_dir = output_dir / "images"
    audio_dir = output_dir / "audio"
    images_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    image_paths: List[str] = []
    audio_paths: List[str] = []

    for chunk, prompt in zip(chunks, chunk_prompts):
        image_path = images_dir / f"{chunk.index:04d}.png"
        audio_path = audio_dir / f"{chunk.index:04d}.wav"
        t2i.generate_image(
            prompt=prompt.image_prompt,
            negative_prompt=prompt.negative_prompt,
            width=config.t2i.width,
            height=config.t2i.height,
            seed=None,
            steps=config.t2i.steps,
            cfg=config.t2i.cfg,
            sampler=config.t2i.sampler,
            output_path=str(image_path),
        )
        tts.synthesize(chunk.text, config.tts.voice_id, config.tts.speed, str(audio_path))
        image_paths.append(str(image_path))
        audio_paths.append(str(audio_path))

    animated_images = animation.animate_images(image_paths, [p.recommended_motion for p in chunk_prompts])
    subtitles_path = output_dir / "subtitles.srt"
    _write_srt(subtitles_path, chunks)
    music_path = _pick_music(config.video.music_glob)
    final_video_path = output_dir / "final.mp4"
    composer.compose(
        animated_images,
        audio_paths,
        str(subtitles_path),
        str(final_video_path),
        music_path=music_path,
        fps=config.video.fps,
    )

    return RenderPlan(
        poem=poem,
        chunks=chunks,
        prompts=prompt_plan,
        output_dir=str(output_dir),
        images=image_paths,
        audio_files=audio_paths,
        subtitles_path=str(subtitles_path),
        final_video_path=str(final_video_path),
    )


def _prepare_output_dir(root_dir: str) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    date_dir = Path(root_dir) / datetime.utcnow().strftime("%Y-%m-%d")
    output_dir = date_dir / f"run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_srt(path: Path, chunks: List[Chunk]) -> None:
    current = 0.0
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        start = current
        duration = chunk.estimated_duration
        end = start + duration
        lines.append(str(index))
        lines.append(f"{_format_timestamp(start)} --> {_format_timestamp(end)}")
        lines.append(chunk.text)
        lines.append("")
        current = end
    path.write_text("\n".join(lines), encoding="utf-8")


def _format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def _pick_music(glob_pattern: str) -> str | None:
    paths = list(Path(".").glob(glob_pattern))
    if not paths:
        return None
    return str(random.choice(paths))
