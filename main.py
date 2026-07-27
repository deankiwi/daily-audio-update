"""Entry point for the daily language-drill briefing.

Usage:
    uv run main.py            # generate + upload today's briefing
    uv run main.py --dry-run  # fetch + script only; print the segment timeline
    uv run main.py --no-upload
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from daily_briefing.core import engine
from daily_briefing.core.catalog import LocalCatalog
from daily_briefing.core.config import ConfigError, load_config, validate_config
from daily_briefing.core.storage import upload_to_gcs
from daily_briefing.core.tts import TTSClient


def _print_dry_run(rows):
    print("\nPlanned segment timeline (no audio generated):\n")
    header = f"{'#':>3}  {'block':<10} {'lang':<4} {'cache':<5} {'dur':>6} {'pause':>6}  text"
    print(header)
    print("-" * len(header))
    for i, r in enumerate(rows, 1):
        text = r["text"] if len(r["text"]) <= 50 else r["text"][:47] + "..."
        print(f"{i:>3}  {r['block']:<10} {r['lang']:<4} {r['cache']:<5} "
              f"{r['duration_ms']:>6} {r['pause_ms']:>6}  {text}")
    total = rows[-1]["offset_ms"] + rows[-1]["duration_ms"] + rows[-1]["pause_ms"] if rows else 0
    misses = sum(1 for r in rows if r["cache"] == "miss")
    print(f"\n{len(rows)} segments, {misses} would call TTS (cache miss), "
          f"~{total / 1000:.0f}s total.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the daily language-drill briefing.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch + script only; print the timeline without generating audio.")
    parser.add_argument("--no-upload", action="store_true", help="Skip the GCS upload.")
    parser.add_argument("--config", default="config.json", help="Path to config.json.")
    args = parser.parse_args()

    load_dotenv()

    try:
        config = load_config(args.config)
        validate_config(config)
    except ConfigError as e:
        print(f"Config error:\n{e}", file=sys.stderr)
        return 2

    llm_key = os.getenv(config.llm.get("api_key_env", "OPENAI_API_KEY"))
    llm_client = OpenAI(api_key=llm_key, base_url=config.llm.get("base_url") or None)

    tts_key = os.getenv("OPENAI_API_KEY")
    tts = TTSClient(OpenAI(api_key=tts_key), config.tts_model, LocalCatalog("cache"))

    print(f"Building briefing for {config.user_name} in {config.target_language} "
          f"({config.dialect})...")

    try:
        result = engine.run(config, llm_client, tts, dry_run=args.dry_run)
    except engine.RunAborted as e:
        print(f"\nRun aborted: {e}", file=sys.stderr)
        return 1

    print(f"\nBlocks: {result.summary_line()}")

    if args.dry_run:
        _print_dry_run(engine.dry_run_timeline(result, tts, config))
        return 0

    print(f"Saved: {result.mp3_path}")

    bucket = os.getenv("GCS_BUCKET_NAME")
    if args.no_upload:
        print("Skipping upload (--no-upload).")
    elif not bucket:
        print("GCS_BUCKET_NAME not set; skipping upload.")
    else:
        dated_name = os.path.basename(result.mp3_path)
        latest_name = f"briefing_{config.output_language_label}_latest.mp3"
        url_dated = upload_to_gcs(result.mp3_path, bucket, dated_name)
        url_latest = upload_to_gcs(result.mp3_path, bucket, latest_name)
        if url_dated:
            print(f"Uploaded: {url_dated}")
        if url_latest:
            print(f"Uploaded latest: {url_latest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
