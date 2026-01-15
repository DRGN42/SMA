# Poem Bot MVP

Modulares Bot-System (MVP) für automatisierte Gedicht-Verarbeitung mit austauschbaren Providern (LLM/TTS/T2I) und sauberer Architektur.

## Features (MVP)
- Zufälliges Gedicht von hor.de scrapen (Redirects unterstützt)
- Parsing in Autor, Titel, Text
- Chunking (standard: zeilenweise)
- LLM-Analyse: Global Visual Bible + Chunk-Prompts
- TTS je Chunk (Dummy + Higgs Audio v2)
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

### macOS / Linux (bash/zsh)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

### Windows (cmd.exe)
```bat
python -m venv .venv
.venv\\Scripts\\activate.bat
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

## Higgs Audio v2 Setup (TTS)

### Option A: CLI Integration (empfohlen)
1. Stelle sicher, dass dein Higgs CLI ausführbar ist (z. B. `higgs_tts` im PATH).
2. Setze in `config/config.yaml`:
```yaml
tts:
  provider: higgs
  higgs_mode: "cli"
  higgs_command: "higgs_tts --text-file {text_path} --voice-wav {voice_wav} --voice-text {voice_text} --output {output_path} --speed {speed}"
  voice_wav_path: "assets/voice/poemvoice.wav"
  voice_text_path: "assets/voice/poemvoice.txt"
```
3. Run wie gewohnt:
```bash
python cli.py run-once --config config/config.yaml
```

### Option B: HTTP Integration
Wenn dein Higgs Service eine HTTP-API anbietet, setze:
```yaml
tts:
  provider: higgs
  higgs_mode: "http"
  higgs_url: "http://localhost:8000"
  higgs_endpoint: "/synthesize"
```
Die Implementierung erwartet entweder `audio/wav` als Response oder JSON mit `audio_base64` oder `audio_url`.
