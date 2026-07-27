# Language Drill Engine

## Summary
Rewrite the daily briefing from a single continuous Spanish monologue into a **configurable language-drill engine**. Content is broken into short sentences, each played as target-language → native-language → target-language (repeated). The run is driven by an ordered array of configurable **blocks**, each sourcing data from a pluggable **source registry**, generating sentences via structured LLM output, and rendering audio from a persistent **segment catalog** (cache). Delivery (GCS upload + stable `latest` URL for the iPhone alarm) is unchanged; only the audio content changes.

This is a ground-up rewrite of the engine, not an incremental change. Existing data sources are preserved and migrated into blocks.

## Goal
**Primary: language learning through repetition.** The daily info (weather, news, etc.) is the *content vehicle* for the drill, not the point. Optimize for short, clean, learnable sentences over information density. Secondary goal: keep the tool easy to configure and extend (add sources, add blocks, tune repeats) — with a **future block-builder UI** in mind, so all behavioral config must be structured, machine-readable/writable data.

## Scope
- New block-based engine: ordered playlist of blocks, each with a 3-stage pipeline `fetch → script → render`.
- Per-sentence drill pattern with configurable repeats, languages, and pauses.
- Persistent on-disk audio catalog keyed by content hash.
- Structured JSON LLM output (`{es, en}` pairs), one call per block.
- Config split: secrets in `.env`, all behavioral/block config in `config.json` (validated on startup).
- Migrate existing sources (weather, markets, tech, bbc) into blocks + add static blocks (greeting, date, sign-off).
- `--dry-run` mode; unit tests for pure logic.
- Rewrite docs (README, AI_CONTEXT, Mermaid diagram, DEPLOYMENT).

## Out of scope (deferred)
- **Tide source** — new API, deferred as the first "new source" fast-follow after the engine works. *(No provider/station chosen yet — research when we get there.)*
- **OpenRouter for the LLM stage** — wired as a config-flip (OpenAI-compatible `base_url`), but default stays OpenAI. OpenRouter cannot do TTS.
- **Non-OpenAI TTS providers** (ElevenLabs/Azure/Google) — the real fix if OpenAI accent is inadequate; held in reserve, cheap to swap later.
- **Moving the catalog off local disk** (to GCS/DB) — kept behind a storage interface so the backend can swap later; user will advise.
- **The block-builder UI itself** — only the data model is designed to support it.
- **Lyrics/synced-lyrics/Whisper subsystem — REMOVED entirely** (was only used for a LinkedIn post). No SYLT, LRC, USLT, or transcription.

## Requirements

### Drill pattern (per sentence)
- Default sequence: `["es", "en", "es", "es"]` (target → native → target → target). Confirmed.
- All segments at **standard TTS speed** — never below 1.0 (sounds unnatural). Speed is a fixed constant, not a config variable.
- A **pause after every spoken segment** (not just repeats).
- Pause duration formula: `pause = max(prev_segment_duration_ms × 1.5, 1000ms)` — proportional to the segment just spoken, minimum 1s.
- Pauses are generated silence (`AudioSegment.silent`), sized exactly using each segment's known `duration_ms`.
- Pattern, repeats, language, pauses are all **configurable** (per-block override with global default).

### Block model
- **Block definition (Layer A):**
  ```json
  {
    "id": "weather",
    "source": "weather",
    "prompt": "Summarise today's weather in 2 short sentences a beginner can follow.",
    "target_sentences": 2,
    "enabled": true,
    "pattern": ["es","en","es","es"],
    "pause_after_each": true
  }
  ```
- `id` and `source` are **fully decoupled** — `id` is a unique label; `source` is a registry key. Multiple blocks may reuse one source with different prompts.
- `enabled` is an explicit on/off toggle (keeps config but silences the block); kept as a field (not expressed only via array membership).
- Per-block settings **override a global default**; omit to inherit.
- **Ordered playlist (Layer B)** references blocks in order, plus global `language`, `defaults`, `voices`.

### Source registry
- `source` is a key mapping to a registered fetcher function (e.g. `"weather" → get_weather()`).
- Adding a source = write one function + register it under a name.
- `"source": "static"` = no fetch, no LLM; sentences supplied inline in config.

### Script stage (LLM)
- **One LLM call per block**, using OpenAI **structured output** (`response_format` / JSON mode).
- Returns `{ "sentences": [ { "es": "...", "en": "..." }, ... ] }`.
- Only `es`/`en` string values ever reach TTS — **no markdown, numbering, or headers** (permanently fixes the prior TTS "beep on `**...**` / `1.`" bug).
- English translation comes free from the same call (no separate translation call).
- Default LLM: OpenAI `gpt-4o-mini`. Provider is config-driven (`base_url`, `model`, `api_key_env`) so OpenRouter is a one-line switch.

### Audio catalog (cache)
- Cache key: `sha256(text + language + voice + tts_model + instructions)`. (Speed removed — constant. `instructions`/accent steering included because it changes output.)
- Storage: `cache/audio/<sha256>.mp3` + `cache/manifest.json`.
- Manifest entries are **rich and readable**: `text`, `language`, `voice`, `tts_model`, `instructions`, `created`, `duration_ms`.
- Flow: compute key → hit = read file; miss = call TTS, measure `duration_ms`, save, use.
- **No expiry** (identical inputs are deterministic); optional manual "clear cache" command.
- Local disk only for now; gitignored; separate from `recordings/`. Behind a swappable storage interface.
- Within a sentence, repeated ES reps share one key → generated once, reused. Across days, recurring phrases (greeting, date fragments, common words) are cache hits → near-zero cost/latency.

### TTS
- Model: **`gpt-4o-mini-tts`** (supports `instructions` for accent steering).
- **Latin American Spanish** accent via an instruction like *"Speak with a natural native Latin American Spanish accent, clear, at a moderate learner's pace."*
- One voice for Spanish, one for English (distinct, so the ear distinguishes target vs native). Sensible defaults chosen by implementer; per-block voice override allowed.
- During build, generate short side-by-side samples of candidate voices for the user to pick from (user cannot pre-judge accent quality).

### Static blocks
- `"source": "static"`, inline `sentences` with template variables.
- Starter variables: `{name}`, `{date_es}`, `{date_en}`, `{weekday_es}`.
- Skip fetch + LLM; run the **same render pattern** as dynamic blocks (so the date/greeting are drilled too).
- Default shipped static blocks: greeting, date, sign-off.

### Config & validation
- `.env` keeps **only secrets/machine specifics** (`OPENAI_API_KEY`, `GCS_BUCKET_NAME`, …).
- New **`config.json`** holds all behavioral/block config (user name, language, dialect, defaults, voices, blocks). Weather lat/lon moves into the weather block's settings.
- `config.json` is **gitignored** (hides personal location); commit a `config.example.json`.
- **Validate `config.json` on startup**: every block references a real source; patterns use only known languages; fail with a clear message before spending API calls.

### Failure handling
- **Per-block isolation + graceful degradation**: each block's `fetch → script → render` runs independently; on failure (after retry) **log, skip, continue**.
- Transient API errors (LLM/TTS): retry ~2× with short backoff before skipping the block.
- Malformed structured output: retry once, then skip the block.
- **If every block fails: abort loudly; do NOT upload or overwrite `latest`.**
- End-of-run **summary line**, e.g. `✅ weather ✅ greeting ⚠️ tide (skipped: API timeout) ✅ news`.
- **Date-as-canary:** every run leads with the spoken date; if TTS credits run out, all speech fails → run aborts → `latest` not overwritten → next morning plays yesterday's date = unmistakable signal. The "don't overwrite latest on total failure" rule must hold for this to work.

### Audio assembly
- **`pydub` + system `ffmpeg`** for concatenation and silence generation.
- **Startup check** that fails loudly with a clear message if `ffmpeg` is not on PATH.

### Delivery (unchanged)
- Write MP3 to `recordings/`, upload to GCS under a dated name, and overwrite `briefing_<lang>_latest.mp3` (stable URL the iPhone Shortcut uses).
- Skip the `latest` overwrite only on total run failure.

## Default shipped configuration
Blocks (in order): `greeting` (static) → `date` (static) → `weather` → `markets` → `tech` → `bbc/news` → `sign-off` (static). All existing sources migrated; no source discarded.

## Edge cases
- Single source API down → that block skipped, rest proceed.
- LLM returns invalid JSON → one retry, then skip.
- TTS credits exhausted → all blocks fail → abort, `latest` preserved (canary).
- `ffmpeg` missing → loud startup failure.
- `config.json` invalid/typo → startup validation failure before API spend.
- Repeated identical segment (within sentence or across days) → served from catalog, no TTS call.

## Acceptance criteria
- `uv run main.py` produces an MP3 where each block's sentences play `ES → EN → ES → ES` with correct pauses.
- Repeated segments are served from the catalog (visible in logs).
- File uploads to GCS + overwrites `latest`.
- A skipped block does not kill the run; run summary reports per-block status.
- Total failure aborts without overwriting `latest`.
- Lyrics/Whisper subsystem is gone.

## Dependencies / setup notes
- New runtime dep: `pydub`; new system dep: **`ffmpeg`** (add to `DEPLOYMENT.md`; `brew install ffmpeg` / `apt install ffmpeg`).
- TTS model change to `gpt-4o-mini-tts`.
- New `config.json` (+ committed `config.example.json`); `config.json` gitignored.
- `cache/` directory (gitignored).
- Env: `OPENAI_API_KEY`, `GCS_BUCKET_NAME` retained; optional `OPENROUTER_API_KEY` for future flip.

## Verification notes
1. **Unit tests (mocked, no API):** config validation, cache-key stability, pause formula `max(prev×1.5, 1s)`, pattern expansion → ordered segment list, catalog hit/miss (2nd identical segment doesn't re-call TTS).
2. **`--dry-run` mode:** runs fetch + LLM, prints planned segment timeline (segment, language, cache hit/miss, pause length, total duration) with **no audio generated** — cheap structural check before spending TTS credits.
3. **One live end-to-end run:** user listens to the MP3 and confirms the drill cadence and Spanish accent. This is the true acceptance test.

## Documentation impacts
- Rewrite `README.md` and `AI_CONTEXT.md` for the drill engine, block/catalog model, `config.json` + `ffmpeg` setup.
- Update the Mermaid diagram to: config → per-block fetch/LLM → catalog-aware TTS → stitch → GCS.
- Add `ffmpeg` to `DEPLOYMENT.md`.

## Implementation status (built)
Engine rewrite complete and tested offline.

- `daily_briefing/core/config.py` — typed `Config`/`Block`, `load_config`, `validate_config` (ffmpeg + schema).
- `daily_briefing/core/sources.py` — name→fetcher registry; weather/markets/tech/bbc registered; `static` handled by the engine.
- `daily_briefing/core/script.py` — one structured LLM call per block, dynamic `{target, native}` schema.
- `daily_briefing/core/catalog.py` — `make_cache_key`, `measure_duration_ms`, `LocalCatalog` (audio dir + JSON manifest).
- `daily_briefing/core/tts.py` — `TTSClient` (catalog-backed, `synth`/`peek`), `gpt-4o-mini-tts` + instructions.
- `daily_briefing/core/render.py` — `pause_ms`, `expand_block`, `render_timeline` (pydub stitch).
- `daily_briefing/core/engine.py` — per-block isolation, retries, `RunAborted`, run summary, `dry_run_timeline`.
- `main.py` — CLI (`--dry-run`, `--no-upload`, `--config`); GCS upload unchanged.
- `config.example.json`, `.env.example`, `.gitignore` (config.json + cache/), `pyproject.toml` (pydub + audioop-lts; mutagen removed), cron PATH (+`/opt/homebrew/bin`), `scripts/voice_samples.py`.
- Removed: `daily_briefing/core/audio.py`, `daily_briefing/core/llm.py`.
- Tests: `tests/` — 27 passing (config, catalog/cache-hit, render/pauses/stitch, engine isolation+abort, script/utils).

**Verified offline:** unit suite green; `config.example.json` loads + validates with real ffmpeg check; CLI dry-run renders the full `es→en→es→es` timeline with template substitution and pause/offset math.
**Not yet done (needs API keys / your ear):** one live end-to-end run + listen; Spanish voice selection from samples.

## Open questions / unresolved
- [ ] Default Spanish/English **voice names** — implementer to propose; user picks from generated samples.
- [ ] Exact **accent instruction** wording for `gpt-4o-mini-tts` — tune during the sample step.
- [ ] **Tide** source: provider/API + location/station — deferred, research later.
- [ ] Future **catalog backend** (GCS/DB) — user will advise when ready.
- [ ] Whether to eventually default the script LLM to an **OpenRouter** model for better Spanish phrasing — experiment after pipeline runs.
