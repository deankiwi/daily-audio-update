import json

import pytest

from daily_briefing.core.config import ConfigError, load_config, validate_config


def test_load_merges_defaults_into_blocks(config):
    weather = next(b for b in config.blocks if b.id == "weather")
    # inherited from defaults
    assert weather.pattern == ["es", "en", "es"]
    assert weather.pause_after_each is True
    assert config.pause_target_factor == 1.1
    assert config.pause_native_ms == 1000
    # voices/instructions merged from tts defaults
    assert weather.voices == {"es": "nova", "en": "alloy"}
    assert weather.instructions["es"] == "es-accent"


def test_block_override_wins_over_default(tmp_path, config_dict):
    config_dict["blocks"][1]["pattern"] = ["es", "en"]
    config_dict["blocks"][1]["voices"] = {"es": "sage"}
    p = tmp_path / "c.json"
    p.write_text(json.dumps(config_dict), encoding="utf-8")
    cfg = load_config(str(p))
    weather = next(b for b in cfg.blocks if b.id == "weather")
    assert weather.pattern == ["es", "en"]
    assert weather.voices["es"] == "sage"      # overridden
    assert weather.voices["en"] == "alloy"     # still inherited


def test_valid_config_passes(config):
    validate_config(config, check_ffmpeg=False)


def test_unknown_source_fails(tmp_path, config_dict):
    config_dict["blocks"][1]["source"] = "does_not_exist"
    p = tmp_path / "c.json"
    p.write_text(json.dumps(config_dict), encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown source"):
        validate_config(load_config(str(p)), check_ffmpeg=False)


def test_static_without_sentences_fails(tmp_path, config_dict):
    config_dict["blocks"][0]["sentences"] = []
    p = tmp_path / "c.json"
    p.write_text(json.dumps(config_dict), encoding="utf-8")
    with pytest.raises(ConfigError, match="no 'sentences'"):
        validate_config(load_config(str(p)), check_ffmpeg=False)


def test_unknown_pattern_code_fails(tmp_path, config_dict):
    config_dict["blocks"][1]["pattern"] = ["es", "fr"]
    p = tmp_path / "c.json"
    p.write_text(json.dumps(config_dict), encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown language code 'fr'"):
        validate_config(load_config(str(p)), check_ffmpeg=False)


def test_duplicate_ids_fail(tmp_path, config_dict):
    config_dict["blocks"][1]["id"] = "greeting"
    p = tmp_path / "c.json"
    p.write_text(json.dumps(config_dict), encoding="utf-8")
    with pytest.raises(ConfigError, match="Duplicate block id"):
        validate_config(load_config(str(p)), check_ffmpeg=False)


def test_missing_file():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/no/such/config.json")
