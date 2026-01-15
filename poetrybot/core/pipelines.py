"""
Main pipeline orchestrator.
Coordinates all providers to execute the full content generation workflow.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .entities import Poem, RenderPlan
from .interfaces import (
    IScraperProvider, IChunkerProvider, ILLMProvider,
    ITTSProvider, IT2IProvider, IVideoRenderer,
    IStorageProvider, IPublisherProvider
)

logger = logging.getLogger(__name__)


class PoemPipeline:
    """Orchestrates the complete poem-to-video pipeline."""
    
    def __init__(
        self,
        scraper: IScraperProvider,
        chunker: IChunkerProvider,
        llm: ILLMProvider,
        tts: ITTSProvider,
        t2i: IT2IProvider,
        video: IVideoRenderer,
        storage: IStorageProvider,
        publisher: Optional[IPublisherProvider] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.scraper = scraper
        self.chunker = chunker
        self.llm = llm
        self.tts = tts
        self.t2i = t2i
        self.video = video
        self.storage = storage
        self.publisher = publisher
        self.config = config or {}
        
    def run(self, poem_url: Optional[str] = None) -> Path:
        """Execute full pipeline and return path to final video."""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting Poetry Bot Pipeline")
        logger.info("=" * 60)
        
        # Step 1: Create output directory
        run_dir = self.storage.create_run_directory()
        logger.info(f"Output directory: {run_dir}")
        
        # Step 2: Fetch poem
        logger.info("Step 1/7: Fetching poem...")
        if poem_url:
            poem = self.scraper.fetch_poem_by_url(poem_url)
        else:
            poem = self.scraper.fetch_random_poem()
        
        if self.storage.is_duplicate(poem.source_url):
            logger.warning(f"Duplicate poem detected: {poem.source_url}")
        
        self.storage.save_json(poem.to_dict(), "poem.json")
        logger.info(f"Fetched: '{poem.title}' by {poem.author}")
        
        # Step 3: Chunk text
        logger.info("Step 2/7: Chunking poem text...")
        max_chars = self.config.get("chunker", {}).get("max_chars", 100)
        chunks = self.chunker.chunk_poem(poem, max_chars=max_chars)
        self.storage.save_json([c.to_dict() for c in chunks], "chunks.json")
        logger.info(f"Created {len(chunks)} chunks")
        
        # Step 4: LLM Analysis
        logger.info("Step 3/7: Generating visual bible with LLM...")
        visual_bible = self.llm.generate_visual_bible(poem)
        self.storage.save_json(visual_bible.to_dict(), "visual_bible.json")
        
        logger.info("Step 3b/7: Generating chunk prompts...")
        chunk_prompts = self.llm.generate_chunk_prompts(chunks, visual_bible)
        self.storage.save_json([cp.to_dict() for cp in chunk_prompts], "chunk_prompts.json")
        
        # Step 5: Generate Images
        logger.info("Step 4/7: Generating images...")
        images_dir = run_dir / "images"
        images_dir.mkdir(exist_ok=True)
        image_assets = self.t2i.generate_chunk_images(chunk_prompts, images_dir)
        logger.info(f"Generated {len(image_assets)} images")
        
        # Step 6: Generate Audio
        logger.info("Step 5/7: Generating TTS audio...")
        audio_dir = run_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        voice_sample = self.config.get("tts", {}).get("voice_sample")
        voice_path = Path(voice_sample) if voice_sample else None
        audio_segments = self.tts.synthesize_chunks(chunks, audio_dir, voice_path)
        
        # Step 7: Render Video
        logger.info("Step 6/7: Rendering video...")
        music_dir = self.config.get("video", {}).get("music_dir", "assets/ambient")
        music_files = list(Path(music_dir).glob("*.mp3"))
        bg_music = music_files[0] if music_files else None
        
        render_plan = RenderPlan(
            poem=poem,
            visual_bible=visual_bible,
            chunks=chunks,
            chunk_prompts=chunk_prompts,
            audio_segments=audio_segments,
            image_assets=image_assets,
            background_music_path=str(bg_music) if bg_music else None
        )
        
        subtitles_path = run_dir / "subtitles.srt"
        self.video.generate_subtitles(audio_segments, chunks, subtitles_path)
        
        video_path = run_dir / "final.mp4"
        final_video = self.video.render(render_plan, video_path)
        
        self.storage.mark_processed(poem.source_url)
        
        # Optional: Publish
        if self.publisher:
            logger.info("Step 7/7: Publishing video...")
            try:
                result = self.publisher.publish(
                    video_path=final_video,
                    title=f"{poem.title} - {poem.author}",
                    description=f"Gedicht: {poem.title}",
                    tags=visual_bible.themes
                )
                logger.info(f"Published: {result}")
            except Exception as e:
                logger.error(f"Publishing failed: {e}")
        
        elapsed = datetime.now() - start_time
        logger.info("=" * 60)
        logger.info(f"Pipeline complete! Duration: {elapsed}")
        logger.info(f"Output: {final_video}")
        logger.info("=" * 60)
        
        return final_video
