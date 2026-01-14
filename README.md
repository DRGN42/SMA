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

## Project structure

```
.
├── data/
│   └── raw/          # Raw HTML + fetch metadata
├── scripts/          # Local CLI scripts, called by n8n
└── requirements.txt
```

## Next module

The next module will chunk poem lines for TTS + image prompt generation.
