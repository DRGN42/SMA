from __future__ import annotations

from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from providers.base import T2IProvider


class DummyT2I(T2IProvider):
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
        image = Image.new("RGB", (width, height), color=(20, 20, 20))
        draw = ImageDraw.Draw(image)
        text = prompt[:200]
        draw.text((40, 40), text, fill=(255, 255, 255))
        image.save(output_path)
        return output_path
