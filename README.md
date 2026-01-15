# Poem Bot MVP

Modulares Bot-System (MVP) für automatisierte Gedicht-Verarbeitung mit austauschbaren Providern (LLM/TTS/T2I) und sauberer Architektur.

## Features (MVP)
- Zufälliges Gedicht von hor.de scrapen (Redirects unterstützt)
- Parsing in Autor, Titel, Text
- Chunking (standard: zeilenweise)
- LLM-Analyse: Global Visual Bible + Chunk-Prompts
- TTS je Chunk (Dummy + Higgs Stub)
- T2I je Chunk (Dummy)
- Video-Komposition via ffmpeg (Ken Burns + Untertitel)
- Output-Ordnerstruktur pro Run
- Dry-Run Modus (nur scrape/parse/prompt)

## Architektur
```
core/        # Domänenlogik (Poem, Chunk, PromptPlan)
providers/   # austauschbare Adapter (llm/tts/t2i/video/storage/content)
pipelines/   # Orchestrierung (poem_to_video.py)
config/      # YAML + env Loader
cli.py       # CLI
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration
- Beispiel: `config/config.yaml`
- Env Overrides: `.env.example`

```bash
cp config/config.yaml config/local.yaml
cp .env.example .env
```

## Run
```bash
python cli.py run-once --config config/config.yaml
python cli.py run-once --config config/config.yaml --dry-run
```

## Provider wechseln
- LLM: `config.llm.provider` und `config.llm.base_url`/`model`
- TTS: `config.tts.provider` (`dummy` oder `higgs`)
- T2I: `config.t2i.provider` (aktuell `dummy`, Adapterstruktur vorhanden)

Provider-Auswahl passiert in `pipelines/poem_to_video.py`.

## Output
```
outputs/YYYY-MM-DD/run_<timestamp>/
  poem.json
  global_visual_bible.json
  chunks.json
  images/
  audio/
  subtitles.srt
  final.mp4
```

## Erweiterbarkeit
- `ContentSource` Interface: neue Quellen für Stories/Zitate/etc.
- `Publisher` Interface: später n8n/Postiz-Integration ergänzen.
