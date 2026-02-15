# AI Context: daily-audio-update

## Purpose
Generates daily audio briefings (MP3) covering market data, tech news, world news, and weather, narrated in Spanish via OpenAI. Includes Google Drive upload.

## Key Components
- **Entry Point**: `main.py`
- **Core Logic**: `daily_briefing/core/` (LLM script generation, audio synthesis, Drive upload)
- **Data Sources**: `daily_briefing/plugins/` (Market, Tech, BBC, Weather)
- **Output**: `recordings/` (MP3 files)

## Configuration
- `.env`: API keys (OpenAI, etc.)
- `credentials.json`/`token.json`: Google Drive auth

## Commands
- Run: `uv run main.py`

*Note: Update this file when project structure or core logic changes significantly.*
