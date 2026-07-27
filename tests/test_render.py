import io

import pytest
from pydub import AudioSegment

from daily_briefing.core.config import load_config
from daily_briefing.core.render import expand_block, pause_ms, render_timeline
from daily_briefing.core.tts import TTSClient
from daily_briefing.core.catalog import LocalCatalog

from .helpers import FakeTTSOpenAI, silence_mp3


def test_pause_formula():
    # target-language line: proportional to its duration
    assert pause_ms(2000, is_native=False) == 2200   # 2000 * 1.1
    assert pause_ms(500, is_native=False) == 550
    # native-language line: fixed short pause
    assert pause_ms(2000, is_native=True) == 1000
    assert pause_ms(200, is_native=True) == 1000
    # custom factors honoured
    assert pause_ms(1000, is_native=False, target_factor=2.0) == 2000
    assert pause_ms(1000, is_native=True, native_ms=500) == 500


def test_expand_block_follows_pattern(config):
    weather = next(b for b in config.blocks if b.id == "weather")
    sentences = [{"es": "Hace sol.", "en": "It is sunny."}]
    segs = expand_block(weather, sentences)
    # pattern es,en,es -> 3 segments
    assert [s.language for s in segs] == ["es", "en", "es"]
    assert [s.text for s in segs] == ["Hace sol.", "It is sunny.", "Hace sol."]
    assert [s.voice for s in segs] == ["nova", "alloy", "nova"]
    assert all(s.pause_after for s in segs)


def test_expand_block_skips_missing_language(config):
    weather = next(b for b in config.blocks if b.id == "weather")
    segs = expand_block(weather, [{"es": "Hola."}])  # no 'en'
    assert [s.language for s in segs] == ["es", "es"]


def test_render_timeline_stitches_with_pauses(tmp_path, config):
    weather = next(b for b in config.blocks if b.id == "weather")
    segs = expand_block(weather, [{"es": "uno", "en": "one"}])
    fake = FakeTTSOpenAI(silence_mp3(300))
    tts = TTSClient(fake, "gpt-4o-mini-tts", LocalCatalog(str(tmp_path / "cache")))

    audio = render_timeline(segs, tts, native_code="en")

    # pattern es,en,es: 3 * 300ms speech + pauses [es:330, en:1000, es:330]
    speech = 3 * 300
    pauses = pause_ms(300, False) + pause_ms(300, True) + pause_ms(300, False)
    assert abs(len(audio) - (speech + pauses)) < 150   # mp3 frame rounding tolerance
    # identical 'es' text synthesised once, reused from catalog for the repeat
    assert fake.calls == 2                     # one 'es', one 'en'
