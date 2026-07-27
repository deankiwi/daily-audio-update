# TODO

## Done (language-drill engine rewrite)
- [x] Block-based, per-block-configurable engine (`config.json`, ordered blocks).
- [x] Drill playback: `es → en → es → es` with pauses (`max(prev × 1.5, 1s)`), all configurable.
- [x] Structured LLM output ({es, en} pairs) — fixes the TTS "beep" on `**...**` / `1.` markdown.
- [x] Audio catalog (hash-keyed cache) so repeated lines don't re-hit TTS.
- [x] Latin American Spanish accent via `gpt-4o-mini-tts` instructions.
- [x] Removed the lyrics/Whisper/SYLT/LRC subsystem (was only for a LinkedIn post).

## Next: new sources (engine makes these easy — one fetcher + one registration)
- [ ] **Tide** block — needs a marine/tide API + a station/location (research providers).
- [ ] Quote of the day.
- [ ] "On this day in history."
- [ ] Calendar for the week.

## Later
- [ ] Pick the Spanish voice by ear (`uv run scripts/voice_samples.py`) and set `tts.voices.es`.
- [ ] Experiment with an OpenRouter model for the script stage (config flip: `llm.base_url` + `llm.api_key_env`).
- [ ] Move the audio catalog off local disk (behind the existing storage boundary).
- [ ] Block-builder UI over `config.json`.
