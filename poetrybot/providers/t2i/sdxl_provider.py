"""
Text-to-Image provider using SDXL Turbo via Diffusers.
"""
import logging
from pathlib import Path
from typing import List
import torch
from diffusers import AutoPipelineForText2Image

from core.entities import ChunkPrompt, ImageAsset
from core.interfaces import IT2IProvider

logger = logging.getLogger(__name__)


class SDXLTurboProvider(IT2IProvider):
    """Text-to-Image using SDXL Turbo for fast inference."""
    
    MODEL_ID = "stabilityai/sdxl-turbo"
    
    def __init__(
        self,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        steps: int = 4,
        guidance_scale: float = 0.0
    ):
        self.device = device
        self.dtype = dtype
        self.steps = steps
        self.guidance_scale = guidance_scale
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Lazy-load the pipeline."""
        if self._pipeline is None:
            logger.info("Loading SDXL Turbo model...")
            self._pipeline = AutoPipelineForText2Image.from_pretrained(
                self.MODEL_ID,
                torch_dtype=self.dtype,
                variant="fp16"
            )
            self._pipeline.to(self.device)
            
            if hasattr(self._pipeline, "enable_attention_slicing"):
                self._pipeline.enable_attention_slicing()
            
            logger.info("SDXL Turbo loaded successfully")
        
        return self._pipeline
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        output_path: Path,
        width: int = 1080,
        height: int = 1920
    ) -> ImageAsset:
        """Generate a single image from prompt."""
        logger.info(f"Generating image: {prompt[:50]}...")
        
        image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=self.steps,
            guidance_scale=self.guidance_scale
        ).images[0]
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")
        
        logger.info(f"Saved image to: {output_path}")
        
        return ImageAsset(
            chunk_index=-1,
            file_path=str(output_path),
            width=width,
            height=height,
            prompt_used=prompt
        )
    
    def generate_chunk_images(
        self,
        chunk_prompts: List[ChunkPrompt],
        output_dir: Path
    ) -> List[ImageAsset]:
        """Generate images for all chunks."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        assets = []
        
        for cp in chunk_prompts:
            filename = f"{cp.chunk_index:04d}.png"
            output_path = output_dir / filename
            
            asset = self.generate_image(
                prompt=cp.image_prompt,
                negative_prompt=cp.negative_prompt,
                output_path=output_path
            )
            asset.chunk_index = cp.chunk_index
            
            assets.append(asset)
            logger.info(f"Generated image {cp.chunk_index + 1}/{len(chunk_prompts)}")
        
        return assets
    
    def unload(self):
        """Unload model to free GPU memory."""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            torch.cuda.empty_cache()
            logger.info("SDXL Turbo unloaded")
