"""Config model: loads and validates config.json into typed objects.

Secrets live in .env; everything behavioural (blocks, patterns, voices,
languages) lives in config.json so a future UI can read and write it.
"""

import json
import shutil
from dataclasses import dataclass, field

from . import sources


class ConfigError(Exception):
    """Raised when config.json is missing, malformed, or inconsistent."""


@dataclass
class Block:
    id: str
    source: str
    prompt: str | None
    target_sentences: int
    enabled: bool
    pattern: list[str]
    pause_after_each: bool
    voices: dict[str, str]
    instructions: dict[str, str]
    settings: dict
    sentences: list[dict[str, str]]  # inline pairs for static blocks

    @property
    def is_static(self) -> bool:
        return self.source == sources.STATIC_SOURCE


@dataclass
class Config:
    user_name: str
    target_code: str
    native_code: str
    target_language: str
    native_language: str
    dialect: str
    level: str
    llm: dict
    tts_model: str
    output_language_label: str
    pause_target_factor: float = 1.1
    pause_native_ms: int = 1000
    blocks: list[Block] = field(default_factory=list)


def load_config(path: str = "config.json") -> Config:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise ConfigError(
            f"'{path}' not found. Copy config.example.json to config.json and edit it."
        )
    except json.JSONDecodeError as e:
        raise ConfigError(f"'{path}' is not valid JSON: {e}")

    lang = raw.get("language", {})
    target_code = lang.get("target_code", "es")
    native_code = lang.get("native_code", "en")

    defaults = raw.get("defaults", {})
    default_pattern = defaults.get("pattern", [target_code, native_code, target_code])
    default_pause = defaults.get("pause_after_each", True)
    default_sentences = defaults.get("target_sentences", 2)
    pause_cfg = defaults.get("pause", {})

    tts = raw.get("tts", {})
    default_voices = tts.get("voices", {})
    default_instructions = tts.get("instructions", {})

    blocks = []
    for b in raw.get("blocks", []):
        voices = {**default_voices, **b.get("voices", {})}
        instructions = {**default_instructions, **b.get("instructions", {})}
        blocks.append(Block(
            id=b.get("id"),
            source=b.get("source"),
            prompt=b.get("prompt"),
            target_sentences=b.get("target_sentences", default_sentences),
            enabled=b.get("enabled", True),
            pattern=b.get("pattern", default_pattern),
            pause_after_each=b.get("pause_after_each", default_pause),
            voices=voices,
            instructions=instructions,
            settings=b.get("settings", {}),
            sentences=b.get("sentences", []),
        ))

    config = Config(
        user_name=raw.get("user", {}).get("name", "there"),
        target_code=target_code,
        native_code=native_code,
        target_language=lang.get("target", "Spanish"),
        native_language=lang.get("native", "English"),
        dialect=lang.get("dialect", "Latin American"),
        level=lang.get("level", "A1/A2"),
        llm=raw.get("llm", {"base_url": None, "model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"}),
        tts_model=tts.get("model", "gpt-4o-mini-tts"),
        output_language_label=raw.get("output", {}).get("language_label", lang.get("target", "Spanish")),
        pause_target_factor=pause_cfg.get("target_factor", 1.1),
        pause_native_ms=pause_cfg.get("native_ms", 1000),
        blocks=blocks,
    )
    return config


def validate_config(config: Config, check_ffmpeg: bool = True) -> None:
    """Raise ConfigError on any problem, before we spend API calls."""
    errors: list[str] = []

    if check_ffmpeg and shutil.which("ffmpeg") is None:
        errors.append(
            "ffmpeg not found on PATH. Install it (macOS: 'brew install ffmpeg', "
            "Debian/Ubuntu: 'apt install ffmpeg')."
        )

    known_codes = {config.target_code, config.native_code}
    seen_ids: set[str] = set()

    if not config.blocks:
        errors.append("No blocks defined in config.")

    for b in config.blocks:
        where = f"block '{b.id or '<missing id>'}'"
        if not b.id:
            errors.append("A block is missing an 'id'.")
        elif b.id in seen_ids:
            errors.append(f"Duplicate block id '{b.id}'.")
        seen_ids.add(b.id)

        if not b.source:
            errors.append(f"{where} is missing a 'source'.")
        elif not sources.has_source(b.source):
            errors.append(
                f"{where} references unknown source '{b.source}'. "
                f"Known: {['static'] + sources.registered_names()}."
            )

        if b.is_static and not b.sentences:
            errors.append(f"{where} is static but has no 'sentences'.")

        for code in b.pattern:
            if code not in known_codes:
                errors.append(
                    f"{where} pattern uses unknown language code '{code}'. "
                    f"Known: {sorted(known_codes)}."
                )
            if code not in b.voices:
                errors.append(f"{where} has no voice configured for language '{code}'.")

    if errors:
        raise ConfigError("Invalid config.json:\n  - " + "\n  - ".join(errors))
