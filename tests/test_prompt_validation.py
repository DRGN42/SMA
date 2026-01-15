from core.models import ChunkVisualPrompt, GlobalVisualBible


def test_global_visual_bible_validation():
    payload = {
        "overall_mood": "melancholic",
        "themes": ["love", "loss"],
        "setting": "countryside",
        "era": "19th century",
        "visual_style": "cinematic",
        "color_palette": ["sepia", "blue"],
        "camera": "slow dolly",
        "symbols": ["rose"],
        "negative_prompt": "low quality",
        "social_style": "poetic",
        "pacing": "slow",
    }
    bible = GlobalVisualBible.model_validate(payload)
    assert bible.overall_mood == "melancholic"


def test_chunk_visual_prompt_validation():
    payload = {
        "index": 0,
        "image_prompt": "A lone tree in fog",
        "negative_prompt": "blurry",
        "recommended_motion": "slow zoom in",
        "on_screen_text": "Line 1",
    }
    prompt = ChunkVisualPrompt.model_validate(payload)
    assert prompt.index == 0
