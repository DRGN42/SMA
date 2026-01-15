#!/usr/bin/env python3
"""
Poetry Bot Pipeline - Main Entry Point
"""
import argparse
import logging
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))

from core.pipeline import PoemPipeline
from providers.scraper.hor_de_scraper import HorDeScraper
from providers.chunker.text_chunker import TextChunker
from providers.llm.lm_studio_provider import LMStudioProvider
from providers.t2i.sdxl_provider import SDXLTurboProvider
from providers.tts.higgs_provider import HiggsAudioProvider
from providers.video.ffmpeg_renderer import FFmpegRenderer
from providers.storage.file_manager import FileManager


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    
    return {}


def setup_logging(config: dict):
    """Configure logging."""
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO"))
    
    log_file = log_config.get("file", "logs/pipeline.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def create_pipeline(config: dict) -> PoemPipeline:
    """Create pipeline with all providers."""
    scraper = HorDeScraper()
    chunker = TextChunker(strategy=config.get("chunker", {}).get("strategy", "line"))
    
    llm = LMStudioProvider(
        base_url=config.get("llm", {}).get("base_url", "http://localhost:1234/v1"),
        model=config.get("llm", {}).get("model", "local-model")
    )
    
    t2i = SDXLTurboProvider(steps=config.get("t2i", {}).get("steps", 4))
    tts = HiggsAudioProvider()
    video = FFmpegRenderer(fps=config.get("video", {}).get("fps", 30))
    storage = FileManager(base_dir=config.get("output", {}).get("base_dir", "outputs"))
    
    return PoemPipeline(
        scraper=scraper,
        chunker=chunker,
        llm=llm,
        tts=tts,
        t2i=t2i,
        video=video,
        storage=storage,
        config=config
    )


def main():
    parser = argparse.ArgumentParser(description="Poetry Bot Pipeline")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--url", help="Specific poem URL to process")
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Poetry Bot Pipeline starting...")
    
    pipeline = create_pipeline(config)
    output_path = pipeline.run(poem_url=args.url)
    logger.info(f"Pipeline complete: {output_path}")


if __name__ == "__main__":
    main()
