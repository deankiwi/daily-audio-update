"""Text-to-speech, backed by the audio catalog.

Always calls OpenAI (gpt-4o-mini-tts) at standard speed. A cache hit returns
stored bytes with no API call; a miss synthesises, measures duration, and stores
the result with rich metadata for later inspection / a future UI.
"""

from dataclasses import dataclass

from . import catalog


@dataclass
class SynthResult:
    audio_bytes: bytes
    duration_ms: int
    cache_hit: bool
    key: str


class TTSClient:
    def __init__(self, openai_client, tts_model: str, cache: catalog.LocalCatalog):
        self.client = openai_client
        self.model = tts_model
        self.cache = cache

    def key_for(self, text: str, language: str, voice: str, instructions: str = "") -> str:
        return catalog.make_cache_key(text, language, voice, self.model, instructions)

    def peek(self, text: str, language: str, voice: str, instructions: str = "") -> dict | None:
        """Return cached metadata (incl. duration_ms) without generating -- for dry runs."""
        return self.cache.get_meta(self.key_for(text, language, voice, instructions))

    def synth(self, text: str, language: str, voice: str, instructions: str = "") -> SynthResult:
        key = self.key_for(text, language, voice, instructions)

        cached = self.cache.get(key)
        if cached is not None:
            meta = self.cache.get_meta(key) or {}
            duration = meta.get("duration_ms") or catalog.measure_duration_ms(cached)
            return SynthResult(cached, duration, cache_hit=True, key=key)

        response = self.client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text,
            instructions=instructions or None,
            response_format="mp3",
        )
        audio_bytes = response.read()
        duration = catalog.measure_duration_ms(audio_bytes)
        self.cache.put(key, audio_bytes, {
            "text": text,
            "language": language,
            "voice": voice,
            "tts_model": self.model,
            "instructions": instructions or "",
            "duration_ms": duration,
        })
        return SynthResult(audio_bytes, duration, cache_hit=False, key=key)
