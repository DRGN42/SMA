"""
LLM Provider using LM Studio's OpenAI-compatible API.
"""
import json
import logging
from typing import List, Dict, Any
import requests

from core.entities import Poem, Chunk, VisualBible, ChunkPrompt, MotionType
from core.interfaces import ILLMProvider

logger = logging.getLogger(__name__)


class LMStudioProvider(ILLMProvider):
    """LLM implementation using LM Studio's local OpenAI-compatible API."""
    
    def __init__(
        self,
        base_url: str = "http://192.168.178.54:1234/v1",
        model: str = "local-model",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.session = requests.Session()
    
    def _chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Send chat completion request to LM Studio."""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def generate_visual_bible(self, poem: Poem) -> VisualBible:
        """Analyze poem and generate comprehensive visual style guide."""
        
        system_prompt = """Du bist ein erfahrener Kreativdirektor für visuelle Poesie-Videos.
Analysiere das Gedicht und erstelle einen detaillierten visuellen Styleguide (Visual Bible).
Antworte NUR mit validem JSON, ohne zusätzlichen Text."""
        
        user_prompt = f"""Analysiere dieses Gedicht und erstelle eine Visual Bible:

TITEL: {poem.title}
AUTOR: {poem.author}

TEXT:
{poem.text}

---

Erstelle ein JSON-Objekt mit folgender Struktur:
{{
    "overall_mood": "Die emotionale Grundstimmung",
    "themes": ["Thema 1", "Thema 2", "Thema 3"],
    "setting": "Beschreibung der visuellen Umgebung",
    "era": "Zeitliche Einordnung",
    "visual_style": "Kunststil",
    "color_palette": ["#hexcode1", "#hexcode2", "#hexcode3"],
    "camera_style": "Kameraführung",
    "symbols": ["Symbol 1", "Symbol 2"],
    "negative_prompt": "Was nicht im Bild sein soll",
    "social_hook": "Kurzer Hook-Text für Social Media",
    "pacing": "Tempo des Videos"
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._chat_completion(messages)
        
        try:
            json_match = response
            if "```json" in response:
                json_match = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_match = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_match.strip())
            
            return VisualBible(
                overall_mood=data.get("overall_mood", "neutral"),
                themes=data.get("themes", []),
                setting=data.get("setting", ""),
                era=data.get("era", ""),
                visual_style=data.get("visual_style", ""),
                color_palette=data.get("color_palette", []),
                camera_style=data.get("camera_style", ""),
                symbols=data.get("symbols", []),
                negative_prompt=data.get("negative_prompt", ""),
                social_hook=data.get("social_hook", ""),
                pacing=data.get("pacing", "mittel")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._default_visual_bible()
    
    def generate_chunk_prompts(
        self,
        chunks: List[Chunk],
        visual_bible: VisualBible
    ) -> List[ChunkPrompt]:
        """Generate image prompts for each chunk based on visual bible."""
        chunk_prompts = []
        
        for chunk in chunks:
            prompt = self._generate_single_chunk_prompt(chunk, visual_bible)
            chunk_prompts.append(prompt)
        
        return chunk_prompts
    
    def _generate_single_chunk_prompt(
        self,
        chunk: Chunk,
        visual_bible: VisualBible
    ) -> ChunkPrompt:
        """Generate prompt for a single chunk."""
        
        motion_map = {
            "zoom_in": MotionType.ZOOM_IN,
            "zoom_out": MotionType.ZOOM_OUT,
            "pan_left": MotionType.PAN_LEFT,
            "pan_right": MotionType.PAN_RIGHT,
            "static": MotionType.STATIC
        }
        
        # Default prompt based on visual bible
        return ChunkPrompt(
            chunk_index=chunk.index,
            image_prompt=f"{visual_bible.setting}, {visual_bible.visual_style}, cinematic lighting, 8k",
            negative_prompt=visual_bible.negative_prompt or "text, watermark, blurry",
            recommended_motion=MotionType.ZOOM_IN,
            subtitle_text=chunk.text
        )
    
    def _default_visual_bible(self) -> VisualBible:
        """Return default visual bible when LLM fails."""
        return VisualBible(
            overall_mood="contemplative",
            themes=["poetry", "emotion"],
            setting="atmospheric natural landscape",
            era="timeless",
            visual_style="cinematic, romantic",
            color_palette=["#2C3E50", "#8B7355", "#D4A574"],
            camera_style="slow pans",
            symbols=["nature", "light"],
            negative_prompt="text, watermark, modern objects",
            social_hook="Ein Gedicht, das berührt...",
            pacing="langsam"
        )
