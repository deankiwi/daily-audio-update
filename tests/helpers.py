"""Shared test helpers: fake OpenAI clients and real (silent) mp3 bytes."""

import io
import json

from pydub import AudioSegment


def silence_mp3(ms: int = 300) -> bytes:
    buf = io.BytesIO()
    AudioSegment.silent(duration=ms).export(buf, format="mp3")
    return buf.getvalue()


class _FakeBinary:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeSpeech:
    def __init__(self, data: bytes):
        self._data = data
        self.calls = 0
        self.seen_voices = []

    def create(self, **kwargs):
        self.calls += 1
        self.seen_voices.append(kwargs.get("voice"))
        return _FakeBinary(self._data)


class FakeTTSOpenAI:
    """Stands in for an OpenAI client's .audio.speech.create."""

    def __init__(self, data: bytes):
        self.speech = _FakeSpeech(data)
        self.audio = type("A", (), {"speech": self.speech})()

    @property
    def calls(self) -> int:
        return self.speech.calls


class _FakeMessage:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _FakeChatCompletions:
    def __init__(self, payload: dict):
        self._payload = payload
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        content = json.dumps(self._payload)
        return type("R", (), {"choices": [_FakeMessage(content)]})()


class FakeLLMOpenAI:
    """Stands in for an OpenAI client's .chat.completions.create."""

    def __init__(self, payload: dict):
        self.completions = _FakeChatCompletions(payload)
        self.chat = type("C", (), {"completions": self.completions})()
