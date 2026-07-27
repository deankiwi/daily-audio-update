# AI Context: daily-audio-update

## Purpose
Generates a daily **language-drill** MP3 for learning Spanish. Content is split into short sentences, each played `target → native → target → target` with pauses. Driven by an ordered array of configurable **blocks**; uploaded to Google Cloud Storage (dated + `latest`).

## Key Components
- **Entry point**: `main.py` (thin CLI: `--dry-run`, `--no-upload`, `--config`).
- **Engine**: `daily_briefing/core/engine.py` — orchestrates blocks with per-block isolation, retries, run summary, and the dry-run timeline.
- **Config**: `daily_briefing/core/config.py` — loads/validates `config.json` into typed `Config`/`Block`.
- **Sources**: `daily_briefing/core/sources.py` — name → fetcher registry; fetchers live in `daily_briefing/plugins/`.
- **Script**: `daily_briefing/core/script.py` — one LLM call per block, structured `{es, en}` output.
- **Render**: `daily_briefing/core/render.py` — pattern expansion, pause formula, pydub stitching.
- **TTS + catalog**: `daily_briefing/core/tts.py` + `catalog.py` — OpenAI `gpt-4o-mini-tts`, hash-keyed audio cache with a JSON manifest.
- **Storage**: `daily_briefing/core/storage.py` — GCS upload (unchanged).

## Configuration
- `.env`: secrets only — `OPENAI_API_KEY`, `GCS_BUCKET_NAME` (optional `OPENROUTER_API_KEY`).
- `config.json`: all behaviour (blocks, language, voices, patterns). Template: `config.example.json`. Both `config.json` and `cache/` are gitignored.

## Dependencies
- System: **ffmpeg** (required by pydub for stitching; checked at startup).
- Python: `pydub`, `audioop-lts` (Python ≥3.13 removed stdlib `audioop`), `openai`, `google-cloud-storage`, plugin fetchers.

## Commands
- Run: `uv run main.py`
- Dry run (no audio/API spend on TTS): `uv run main.py --dry-run`
- Tests: `uv run pytest`
- Voice samples: `uv run scripts/voice_samples.py`

## Notes
- The lyrics/Whisper/SYLT/LRC subsystem was removed.
- Full design + decisions: `docs/features/language-drill-engine.md`.

*Update this file when project structure or core logic changes significantly.*
