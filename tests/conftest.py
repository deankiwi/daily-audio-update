import json

import pytest

from daily_briefing.core.config import load_config


def _valid_config_dict():
    return {
        "user": {"name": "Dean"},
        "language": {"target": "Spanish", "native": "English",
                     "target_code": "es", "native_code": "en",
                     "dialect": "Latin American", "level": "A1/A2"},
        "llm": {"base_url": None, "model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"},
        "tts": {"model": "gpt-4o-mini-tts",
                "voices": {"es": "nova", "en": "alloy"},
                "instructions": {"es": "es-accent", "en": "en-accent"}},
        "defaults": {"pattern": ["es", "en", "es"],
                     "pause_after_each": True, "target_sentences": 2,
                     "pause": {"target_factor": 1.1, "native_ms": 1000}},
        "output": {"language_label": "Spanish"},
        "blocks": [
            {"id": "greeting", "source": "static",
             "sentences": [{"es": "Buenos días, {name}.", "en": "Good morning, {name}."}]},
            {"id": "weather", "source": "weather",
             "prompt": "Summarise the weather.", "target_sentences": 2,
             "settings": {"lat": 1.0, "lon": 2.0, "location": "Town"}},
        ],
    }


@pytest.fixture
def config_dict():
    return _valid_config_dict()


@pytest.fixture
def config_path(tmp_path, config_dict):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(config_dict), encoding="utf-8")
    return str(p)


@pytest.fixture
def config(config_path):
    return load_config(config_path)
