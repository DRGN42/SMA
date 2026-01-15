from __future__ import annotations

import json
from typing import Callable, List

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
                    "content": (
                        "Du bist ein Visual Art Director. Antworte NUR mit einem JSON-Objekt "
                        "ohne Markdown oder Code-Fences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analysiere das Gedicht und liefere eine GLOBAL VISUAL BIBLE als JSON mit "
                        "den Feldern overall_mood, themes, setting, era, visual_style, color_palette, "
                        "camera, symbols, negative_prompt, social_style, pacing. "
                        "Feld-Typen: overall_mood, setting, era, visual_style, camera, negative_prompt, "
                        "social_style, pacing = string; themes, color_palette, symbols = array of strings.\n\n"
                        f"Titel: {poem.title}\nAutor: {poem.author}\nText:\n{poem.text}"
                    ),
                },
            ],
            "temperature": 0.4,
        }
        response_json = self._post_chat(payload)
        return self._parse_json_response(
            response_json, _GlobalBibleResponse, normalize=_normalize_global_bible
        )

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
                        "content": (
                            "Du bist ein Prompt Engineer. Antworte NUR mit einem JSON-Objekt "
                            "ohne Markdown oder Code-Fences."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Nutze die GLOBAL VISUAL BIBLE als Leitplanke und erzeuge einen Bildprompt. "
                            "JSON Felder: index (number), image_prompt (string), negative_prompt (string), "
                            "recommended_motion (string), on_screen_text (string).\n\n"
                            f"GLOBAL VISUAL BIBLE: {json.dumps(bible_json, ensure_ascii=False)}\n\n"
                            f"Chunk {chunk.index}: {chunk.text}"
                        ),
                    },
                ],
                "temperature": 0.6,
            }
            response_json = self._post_chat(payload)
            prompt = self._parse_json_response(
                response_json,
                _ChunkPromptResponse,
                normalize=lambda data: _normalize_chunk_prompt(data, chunk.index),
            )
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
    def _parse_json_response(
        response_json: dict,
        schema: type[BaseModel],
        normalize: Callable | None = None,
    ):
        content = response_json["choices"][0]["message"]["content"]
        content = _strip_code_fences(content)
        if normalize:
            try:
                content = normalize(content)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError(f"LLM response is not valid JSON: {content}") from exc
        if isinstance(content, dict):
            payload = content
        else:
            try:
                payload = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(f"LLM response is not valid JSON: {content}") from exc
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"LLM response failed schema validation: {exc}") from exc


def _strip_code_fences(content: str) -> str:
    stripped = content.strip()
    stripped = _strip_chat_tokens(stripped)
    if stripped.startswith("```"):
        stripped = stripped.lstrip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
        if stripped.endswith("```"):
            stripped = stripped[: -3].strip()
    return stripped


def _strip_chat_tokens(content: str) -> str:
    cleaned = content.replace("<|channel|>", "").replace("<|constrain|>", "").replace("<|message|>", "")
    cleaned = cleaned.replace("<|final|>", "").replace("<|assistant|>", "")
    if "<|" in cleaned and "|>" in cleaned:
        cleaned = cleaned.replace("<|", "").replace("|>", "")
    return cleaned.strip()


def _normalize_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _normalize_color_palette(value) -> List[str]:
    if isinstance(value, dict):
        flattened: List[str] = []
        for item in value.values():
            if isinstance(item, list):
                flattened.extend(str(v) for v in item)
            else:
                flattened.append(str(item))
        return flattened
    return _normalize_list(value)


def _normalize_global_bible(data):
    if isinstance(data, str):
        data = json.loads(data)
    return {
        "overall_mood": _normalize_text(data.get("overall_mood")),
        "themes": _normalize_list(data.get("themes")),
        "setting": _normalize_text(data.get("setting")),
        "era": _normalize_text(data.get("era")),
        "visual_style": _normalize_text(data.get("visual_style")),
        "color_palette": _normalize_color_palette(data.get("color_palette")),
        "camera": _normalize_text(data.get("camera")),
        "symbols": _normalize_list(data.get("symbols")),
        "negative_prompt": _normalize_text(data.get("negative_prompt")),
        "social_style": _normalize_text(data.get("social_style")),
        "pacing": _normalize_text(data.get("pacing")),
    }


def _normalize_chunk_prompt(data, default_index: int):
    if isinstance(data, str):
        data = json.loads(data)
    index = data.get("index", default_index)
    return {
        "index": int(index) if isinstance(index, (int, str)) and str(index).isdigit() else default_index,
        "image_prompt": _normalize_text(data.get("image_prompt")),
        "negative_prompt": _normalize_text(data.get("negative_prompt")),
        "recommended_motion": _normalize_text(data.get("recommended_motion")),
        "on_screen_text": _normalize_text(data.get("on_screen_text")),
    }
