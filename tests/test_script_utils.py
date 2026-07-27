from datetime import datetime

from daily_briefing.core import script
from daily_briefing.core.utils import fill_template, get_template_vars

from .helpers import FakeLLMOpenAI


def test_template_vars_spanish():
    vars_ = get_template_vars("Dean", today=datetime(2026, 7, 25))  # a Saturday
    assert vars_["name"] == "Dean"
    assert vars_["weekday_es"] == "sábado"
    assert vars_["date_es"] == "25 de julio de 2026"
    assert "25th July 2026" in vars_["date_en"]


def test_fill_template_leaves_unknown_placeholders():
    out = fill_template("Hola {name}, {missing}", {"name": "Dean"})
    assert out == "Hola Dean, {missing}"


def test_generate_sentences_parses_structured_output(config):
    weather = next(b for b in config.blocks if b.id == "weather")
    client = FakeLLMOpenAI({"sentences": [
        {"es": "Hace sol.", "en": "It is sunny."},
        {"es": "Hace calor.", "en": "It is hot."},
    ]})
    sentences = script.generate_sentences(client, config, weather, "raw weather data")
    assert len(sentences) == 2
    assert sentences[0] == {"es": "Hace sol.", "en": "It is sunny."}


def test_generate_sentences_raises_on_empty(config):
    weather = next(b for b in config.blocks if b.id == "weather")
    client = FakeLLMOpenAI({"sentences": []})
    try:
        script.generate_sentences(client, config, weather, "data")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_schema_uses_configured_codes():
    s = script._schema("es", "en")
    props = s["schema"]["properties"]["sentences"]["items"]["properties"]
    assert set(props) == {"es", "en"}
