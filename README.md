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

## Project structure

```
.
├── data/
│   ├── audio/        # TTS audio outputs
│   └── raw/          # Raw HTML + fetch metadata
├── scripts/          # Local CLI scripts, called by n8n
└── requirements.txt
```

## Next module

The next module will generate images per chunk using the prompts from the LLM response.
