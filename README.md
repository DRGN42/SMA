# SMA Poetry Bot (Local Scripts)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Fetch a random poem page and store the raw HTML + metadata:

```bash
python scripts/scrape_poem.py --output-dir data/raw
```

Parse a single HTML file into normalized JSON:

```bash
python scripts/parse_poem.py data/raw/<file>.html
```

Chunk the parsed poem into line groups:

```bash
python scripts/chunk_poem.py data/raw/<file>.json --lines-per-chunk 2
```

Build an LLM prompt payload for atmosphere + per-chunk image prompts:

```bash
python scripts/build_llm_payload.py data/raw/<file>.chunked.json
```

Run the LLM request (OpenAI-compatible endpoint):

```bash
python scripts/run_llm.py data/raw/<file>.llm.json --endpoint http://localhost:8000/v1/chat/completions --model openai/gpt-oss-20b
```

Parse the LLM response into structured prompts:

```bash
python scripts/parse_llm_response.py data/raw/<file>.llm_response.json
```

Generate TTS audio per chunk (Higgs v2-compatible endpoint):

```bash
python scripts/run_tts.py data/raw/<file>.chunked.json --endpoint http://localhost:8002/v1/tts --voice poetry_female_01
```

Generate TTS audio per chunk (Higgs v2 local mode):

```bash
python scripts/run_tts.py data/raw/<file>.chunked.json --mode local --device cuda
```

Generate TTS with a cached reference voice (poemvoice.wav):

```bash
python scripts/run_tts.py data/raw/<file>.chunked.json --mode local --device cuda --ref-audio-path higgs-audio/examples/voice_prompts/poemvoice.wav
```

The cached reference voice is stored at `data/cache/ref_audio.wav` by default.

### Higgs v2 static cache workaround (minimal patch)

If Higgs v2 crashes with a static KV-cache shape error during local TTS, apply this minimal patch
inside `higgs-audio/boson_multimodal/serve/serve_engine.py` to disable static caches and CUDA graph
capture for now:

```diff
@@
-        # A list of KV caches for different lengths
-        self.kv_caches = {
-            length: StaticCache(
-                config=cache_config,
-                max_batch_size=1,
-                max_cache_len=length,
-                device=self.model.device,
-                dtype=self.model.dtype,
-            )
-            for length in sorted(kv_cache_lengths)
-        }
+        # Disable KV caches (workaround for static cache bugs)
+        self.kv_caches = {}
@@
-        if device == "cuda":
-            logger.info(f"Capturing CUDA graphs for each KV cache length")
-            self.model.capture_model(self.kv_caches.values())
+        if device == "cuda" and self.kv_caches:
+            logger.info(f"Capturing CUDA graphs for each KV cache length")
+            self.model.capture_model(self.kv_caches.values())
@@
-    def _prepare_kv_caches(self):
-        for kv_cache in self.kv_caches.values():
-            kv_cache.reset()
+    def _prepare_kv_caches(self):
+        if not self.kv_caches:
+            return
+        for kv_cache in self.kv_caches.values():
+            kv_cache.reset()
@@
-                use_cache=True,
+                use_cache=False,
@@
-                past_key_values_buckets=self.kv_caches,
+                past_key_values_buckets=self.kv_caches or None,
```

Generate images per chunk with ComfyUI (Flux workflow):

```bash
python scripts/run_image.py data/raw/<file>.llm_response.parsed.json --workflow workflows/flux.json --endpoint http://localhost:8188
```

Prepare video assembly assets (concat lists + subtitles):

```bash
python scripts/run_video.py data/raw/<file>.chunked.json data/images/<file>.images.json data/audio/<file>.tts.json
```

## Project structure

```
.
├── data/
│   ├── audio/        # TTS audio outputs
│   ├── images/       # Image outputs
│   ├── raw/          # Raw HTML + fetch metadata
│   └── video/        # Video assembly assets
├── scripts/          # Local CLI scripts, called by n8n
└── requirements.txt
```

## Next module

The next module will automate ffmpeg execution and add background music.
