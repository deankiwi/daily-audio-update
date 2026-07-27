from daily_briefing.core.catalog import LocalCatalog, make_cache_key
from daily_briefing.core.tts import TTSClient

from .helpers import FakeTTSOpenAI, silence_mp3


def test_cache_key_is_stable_and_sensitive():
    a = make_cache_key("hola", "es", "nova", "gpt-4o-mini-tts", "instr")
    b = make_cache_key("hola", "es", "nova", "gpt-4o-mini-tts", "instr")
    assert a == b
    # any input change -> different key
    assert a != make_cache_key("hola", "es", "alloy", "gpt-4o-mini-tts", "instr")
    assert a != make_cache_key("hola", "en", "nova", "gpt-4o-mini-tts", "instr")
    assert a != make_cache_key("adios", "es", "nova", "gpt-4o-mini-tts", "instr")
    assert a != make_cache_key("hola", "es", "nova", "gpt-4o-mini-tts", "other")


def test_local_catalog_roundtrip(tmp_path):
    cat = LocalCatalog(str(tmp_path / "cache"))
    assert cat.get("k1") is None
    cat.put("k1", b"bytes", {"text": "hola", "duration_ms": 123})
    assert cat.get("k1") == b"bytes"
    assert cat.get_meta("k1")["duration_ms"] == 123
    # survives a reload (persisted manifest)
    cat2 = LocalCatalog(str(tmp_path / "cache"))
    assert cat2.get("k1") == b"bytes"
    assert cat2.get_meta("k1")["text"] == "hola"


def test_tts_second_identical_call_is_cache_hit(tmp_path):
    fake = FakeTTSOpenAI(silence_mp3(250))
    tts = TTSClient(fake, "gpt-4o-mini-tts", LocalCatalog(str(tmp_path / "cache")))

    r1 = tts.synth("hola", "es", "nova", "instr")
    r2 = tts.synth("hola", "es", "nova", "instr")

    assert r1.cache_hit is False
    assert r2.cache_hit is True
    assert fake.calls == 1                 # TTS only hit the API once
    assert r2.audio_bytes == r1.audio_bytes
    assert r2.duration_ms == r1.duration_ms


def test_tts_different_voice_regenerates(tmp_path):
    fake = FakeTTSOpenAI(silence_mp3(250))
    tts = TTSClient(fake, "gpt-4o-mini-tts", LocalCatalog(str(tmp_path / "cache")))
    tts.synth("hola", "es", "nova", "instr")
    tts.synth("hola", "es", "alloy", "instr")
    assert fake.calls == 2
