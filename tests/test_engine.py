import json

import pytest

from daily_briefing.core import engine, sources
from daily_briefing.core.catalog import LocalCatalog
from daily_briefing.core.config import load_config
from daily_briefing.core.tts import TTSClient

from .helpers import FakeLLMOpenAI, FakeTTSOpenAI, silence_mp3


def _boom(_settings):
    raise RuntimeError("api down")


sources.register("t_ok", lambda s: "some weather data")
sources.register("t_boom", _boom)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(engine.time, "sleep", lambda *_a, **_k: None)


def _make_config(tmp_path, blocks):
    cfg = {
        "user": {"name": "Dean"},
        "language": {"target": "Spanish", "native": "English",
                     "target_code": "es", "native_code": "en"},
        "llm": {"model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"},
        "tts": {"model": "gpt-4o-mini-tts",
                "voices": {"es": "nova", "en": "alloy"},
                "instructions": {"es": "a", "en": "b"}},
        "defaults": {"pattern": ["es", "en"], "pause_after_each": True, "target_sentences": 1},
        "output": {"language_label": "Spanish"},
        "blocks": blocks,
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return load_config(str(p))


def _tts(tmp_path):
    return TTSClient(FakeTTSOpenAI(silence_mp3(200)), "gpt-4o-mini-tts",
                     LocalCatalog(str(tmp_path / "cache")))


def _llm():
    return FakeLLMOpenAI({"sentences": [{"es": "Hace sol.", "en": "It is sunny."}]})


def test_static_block_templates_name(tmp_path):
    cfg = _make_config(tmp_path, [
        {"id": "greeting", "source": "static",
         "sentences": [{"es": "Hola, {name}.", "en": "Hi, {name}."}]},
    ])
    result = engine.run(cfg, _llm(), _tts(tmp_path), dry_run=True)
    texts = [s.text for s in result.segments]
    assert "Hola, Dean." in texts
    assert "Hi, Dean." in texts
    assert "{name}" not in " ".join(texts)


def test_skipped_block_does_not_kill_run(tmp_path):
    cfg = _make_config(tmp_path, [
        {"id": "weather", "source": "t_boom", "prompt": "x"},
        {"id": "news", "source": "t_ok", "prompt": "x"},
    ])
    result = engine.run(cfg, _llm(), _tts(tmp_path), dry_run=True)
    statuses = {r.block_id: r.status for r in result.block_results}
    assert statuses["weather"] == "skipped"
    assert statuses["news"] == "ok"


def test_all_blocks_fail_aborts(tmp_path):
    cfg = _make_config(tmp_path, [
        {"id": "weather", "source": "t_boom", "prompt": "x"},
    ])
    with pytest.raises(engine.RunAborted):
        engine.run(cfg, _llm(), _tts(tmp_path), dry_run=True)


def test_disabled_block_is_skipped(tmp_path):
    cfg = _make_config(tmp_path, [
        {"id": "greeting", "source": "static", "enabled": False,
         "sentences": [{"es": "Hola.", "en": "Hi."}]},
        {"id": "news", "source": "t_ok", "prompt": "x"},
    ])
    result = engine.run(cfg, _llm(), _tts(tmp_path), dry_run=True)
    statuses = {r.block_id: r.status for r in result.block_results}
    assert statuses["greeting"] == "disabled"
    assert not any(s.block_id == "greeting" for s in result.segments)


def test_full_run_writes_mp3(tmp_path):
    cfg = _make_config(tmp_path, [
        {"id": "greeting", "source": "static",
         "sentences": [{"es": "Hola, {name}.", "en": "Hi, {name}."}]},
        {"id": "news", "source": "t_ok", "prompt": "x"},
    ])
    out = tmp_path / "recordings"
    result = engine.run(cfg, _llm(), _tts(tmp_path), output_dir=str(out), dry_run=False)
    assert result.mp3_path is not None
    assert (out / result.mp3_path.split("/")[-1]).exists()


def test_dry_run_timeline_has_offsets(tmp_path):
    cfg = _make_config(tmp_path, [
        {"id": "news", "source": "t_ok", "prompt": "x"},
    ])
    tts = _tts(tmp_path)
    result = engine.run(cfg, _llm(), tts, dry_run=True)
    rows = engine.dry_run_timeline(result, tts, cfg)
    assert rows
    assert rows[0]["offset_ms"] == 0
    assert all("cache" in r and "pause_ms" in r for r in rows)
