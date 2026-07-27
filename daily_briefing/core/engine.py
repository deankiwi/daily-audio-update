"""Engine: orchestrate blocks into a stitched briefing.

Per-block isolation: each block runs fetch -> script -> render independently.
A failing block (after retries) is logged and skipped; the run continues. If
*every* block fails the run aborts, so the stable 'latest' file is never
overwritten with an empty briefing (the spoken date then acts as a freshness
canary).
"""

import os
import time
from dataclasses import dataclass, field
from datetime import date

from . import render, script, sources
from .utils import get_template_vars, fill_template

CHARS_PER_SECOND = 14  # rough TTS pace, used only to estimate durations in dry runs


class RunAborted(Exception):
    """Raised when no block produced any audio."""


@dataclass
class BlockResult:
    block_id: str
    status: str  # "ok" | "skipped" | "disabled"
    note: str = ""


@dataclass
class RunResult:
    segments: list = field(default_factory=list)
    block_results: list = field(default_factory=list)
    mp3_path: str | None = None

    def summary_line(self) -> str:
        icons = {"ok": "✅", "skipped": "⚠️", "disabled": "⏸️"}
        parts = []
        for r in self.block_results:
            icon = icons.get(r.status, "•")
            note = f" ({r.note})" if r.note and r.status != "ok" else ""
            parts.append(f"{icon} {r.block_id}{note}")
        return "  ".join(parts)


def _retry(fn, tries: int = 3, delay: float = 1.5):
    last = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - deliberately broad, we retry then skip
            last = e
            if attempt < tries - 1:
                time.sleep(delay)
    raise last


def _sentences_for_block(config, block, llm_client, template_vars) -> list[dict]:
    if block.is_static:
        return [
            {code: fill_template(text, template_vars) for code, text in sentence.items()}
            for sentence in block.sentences
        ]
    raw = _retry(lambda: sources.get_source(block.source)(block.settings))
    return _retry(lambda: script.generate_sentences(llm_client, config, block, raw))


def run(config, llm_client, tts, output_dir: str = "recordings", dry_run: bool = False) -> RunResult:
    template_vars = get_template_vars(config.user_name)
    result = RunResult()

    for block in config.blocks:
        if not block.enabled:
            result.block_results.append(BlockResult(block.id, "disabled"))
            continue
        try:
            sentences = _sentences_for_block(config, block, llm_client, template_vars)
            segments = render.expand_block(block, sentences)
            if not segments:
                raise ValueError("no renderable sentences")
            result.segments.extend(segments)
            result.block_results.append(
                BlockResult(block.id, "ok", f"{len(sentences)} sentence(s)"))
        except Exception as e:  # noqa: BLE001
            result.block_results.append(BlockResult(block.id, "skipped", str(e)))

    if not any(r.status == "ok" for r in result.block_results):
        raise RunAborted("All blocks failed; nothing to speak. Not writing output.")

    if dry_run:
        return result

    audio = render.render_timeline(
        result.segments, tts, config.native_code,
        config.pause_target_factor, config.pause_native_ms)
    os.makedirs(output_dir, exist_ok=True)
    base = f"briefing_{config.output_language_label}_{date.today()}"
    path = os.path.join(output_dir, f"{base}.mp3")
    counter = 1
    while os.path.exists(path):
        path = os.path.join(output_dir, f"{base}_{counter}.mp3")
        counter += 1
    audio.export(path, format="mp3")
    result.mp3_path = path
    return result


def dry_run_timeline(result: RunResult, tts, config) -> list[dict]:
    """Per-segment preview: language, text, cache hit/miss, pause length, offset.

    Uses cached duration when available; otherwise estimates from text length so
    the structure can be reviewed without spending TTS credits.
    """
    rows = []
    offset_ms = 0
    for seg in result.segments:
        meta = tts.peek(seg.text, seg.language, seg.voice, seg.instructions)
        if meta and meta.get("duration_ms"):
            duration = meta["duration_ms"]
            hit = True
        else:
            duration = int(len(seg.text) / CHARS_PER_SECOND * 1000)
            hit = False
        pause = render.pause_ms(
            duration, seg.language == config.native_code,
            config.pause_target_factor, config.pause_native_ms) if seg.pause_after else 0
        rows.append({
            "block": seg.block_id,
            "lang": seg.language,
            "text": seg.text,
            "cache": "hit" if hit else "miss",
            "duration_ms": duration,
            "pause_ms": pause,
            "offset_ms": offset_ms,
        })
        offset_ms += duration + pause
    return rows
