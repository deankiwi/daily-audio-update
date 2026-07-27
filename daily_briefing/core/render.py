"""Render stage: expand sentences into an ordered segment timeline and stitch
the audio with silent pauses.

Each sentence is expanded via the block's pattern (e.g. es -> en -> es -> es).
A pause follows every spoken segment (when enabled), sized from the duration of
the segment just spoken.
"""

import io
from dataclasses import dataclass

from pydub import AudioSegment

DEFAULT_TARGET_FACTOR = 1.1   # pause after a target-language line = duration x this
DEFAULT_NATIVE_PAUSE_MS = 1000  # fixed pause after a native-language line


def pause_ms(duration_ms: int, is_native: bool,
             target_factor: float = DEFAULT_TARGET_FACTOR,
             native_ms: int = DEFAULT_NATIVE_PAUSE_MS) -> int:
    """Pause after a segment.

    Native-language lines (the translation) get a short fixed pause; target-language
    lines get a pause proportional to how long they took, so you have time to repeat.
    """
    if is_native:
        return native_ms
    return int(duration_ms * target_factor)


@dataclass
class Segment:
    block_id: str
    language: str
    text: str
    voice: str
    instructions: str
    pause_after: bool


def expand_block(block, sentences: list[dict[str, str]]) -> list[Segment]:
    """One sentence -> N spoken segments following the block's pattern."""
    segments: list[Segment] = []
    for sentence in sentences:
        for code in block.pattern:
            text = sentence.get(code)
            if not text:
                continue
            segments.append(Segment(
                block_id=block.id,
                language=code,
                text=text,
                voice=block.voices.get(code),
                instructions=block.instructions.get(code, ""),
                pause_after=block.pause_after_each,
            ))
    return segments


def render_timeline(segments: list[Segment], tts, native_code: str,
                    target_factor: float = DEFAULT_TARGET_FACTOR,
                    native_ms: int = DEFAULT_NATIVE_PAUSE_MS) -> AudioSegment:
    """Synthesise each segment (via catalog) and concatenate with pauses."""
    combined = AudioSegment.empty()
    for seg in segments:
        result = tts.synth(seg.text, seg.language, seg.voice, seg.instructions)
        combined += AudioSegment.from_file(io.BytesIO(result.audio_bytes), format="mp3")
        if seg.pause_after:
            pause = pause_ms(result.duration_ms, seg.language == native_code,
                             target_factor, native_ms)
            combined += AudioSegment.silent(duration=pause)
    return combined
