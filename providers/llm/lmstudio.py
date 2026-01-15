from __future__ import annotations

import json
from typing import List

import requests
from pydantic import BaseModel, ValidationError

from core.models import Chunk, ChunkVisualPrompt, GlobalVisualBible, Poem
from providers.base import LLMProvider


class _GlobalBibleResponse(BaseModel):
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


class _ChunkPromptResponse(BaseModel):
    index: int
    image_prompt: str
    negative_prompt: str
    recommended_motion: str
    on_screen_text: str


class LMStudioProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout_s: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def generate_global_visual_bible(self, poem: Poem) -> GlobalVisualBible:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Visual Art Director. Antworte NUR mit gültigem JSON.",
                },
                {
                    "role": "user",
                    "content": (
                        "Analysiere das Gedicht und liefere eine GLOBAL VISUAL BIBLE als JSON mit "
                        "den Feldern overall_mood, themes, setting, era, visual_style, color_palette, "
                        "camera, symbols, negative_prompt, social_style, pacing.\n\n"
                        f"Titel: {poem.title}\nAutor: {poem.author}\nText:\n{poem.text}"
                    ),
                },
            ],
            "temperature": 0.4,
        }
        response_json = self._post_chat(payload)
        return self._parse_json_response(response_json, _GlobalBibleResponse)

    def generate_chunk_prompts(
        self, poem: Poem, chunks: List[Chunk], bible: GlobalVisualBible
    ) -> List[ChunkVisualPrompt]:
        prompts: List[ChunkVisualPrompt] = []
        bible_json = bible.model_dump()
        for chunk in chunks:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Du bist ein Prompt Engineer. Antworte NUR mit gültigem JSON.",
                    },
                    {
                        "role": "user",
                        "content": (
                            "Nutze die GLOBAL VISUAL BIBLE als Leitplanke und erzeuge einen Bildprompt. "
                            "JSON Felder: index, image_prompt, negative_prompt, recommended_motion, "
                            "on_screen_text.\n\n"
                            f"GLOBAL VISUAL BIBLE: {json.dumps(bible_json, ensure_ascii=False)}\n\n"
                            f"Chunk {chunk.index}: {chunk.text}"
                        ),
                    },
                ],
                "temperature": 0.6,
            }
            response_json = self._post_chat(payload)
            prompt = self._parse_json_response(response_json, _ChunkPromptResponse)
            prompts.append(
                ChunkVisualPrompt(
                    index=prompt.index,
                    image_prompt=prompt.image_prompt,
                    negative_prompt=prompt.negative_prompt,
                    recommended_motion=prompt.recommended_motion,
                    on_screen_text=prompt.on_screen_text,
                )
            )
        return prompts

    def _post_chat(self, payload: dict) -> dict:
        url = f"{self.base_url}/chat/completions"
        response = requests.post(url, json=payload, timeout=self.timeout_s)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _parse_json_response(response_json: dict, schema: type[BaseModel]):
        content = response_json["choices"][0]["message"]["content"]
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM response is not valid JSON: {content}") from exc
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"LLM response failed schema validation: {exc}") from exc
