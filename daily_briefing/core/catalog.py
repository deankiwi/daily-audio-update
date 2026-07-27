"""Persistent audio catalog (cache).

Every TTS segment is a pure function of (text, language, voice, tts_model,
instructions), so we hash those into a key and store the resulting audio. Same
inputs -> same file, forever (no expiry). Repeated segments -- within a sentence
or across days -- become free cache hits.

Storage sits behind a small interface so the backend can later move off local
disk (e.g. to GCS) without touching the engine.
"""

import hashlib
import io
import json
import os
from datetime import datetime, timezone

from pydub import AudioSegment


def make_cache_key(text: str, language: str, voice: str, tts_model: str,
                   instructions: str = "") -> str:
    payload = "\x1f".join([text, language, voice, tts_model, instructions or ""])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def measure_duration_ms(audio_bytes: bytes) -> int:
    seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    return len(seg)


class LocalCatalog:
    """On-disk catalog: audio files + a readable JSON manifest."""

    def __init__(self, root: str = "cache"):
        self.root = root
        self.audio_dir = os.path.join(root, "audio")
        self.manifest_path = os.path.join(root, "manifest.json")
        os.makedirs(self.audio_dir, exist_ok=True)
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_manifest(self) -> None:
        tmp = self.manifest_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._manifest, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.manifest_path)

    def _audio_path(self, key: str) -> str:
        return os.path.join(self.audio_dir, f"{key}.mp3")

    def get_meta(self, key: str) -> dict | None:
        return self._manifest.get(key)

    def get(self, key: str) -> bytes | None:
        path = self._audio_path(key)
        if key in self._manifest and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    def put(self, key: str, audio_bytes: bytes, meta: dict) -> None:
        with open(self._audio_path(key), "wb") as f:
            f.write(audio_bytes)
        entry = dict(meta)
        entry.setdefault("created", datetime.now(timezone.utc).isoformat())
        self._manifest[key] = entry
        self._save_manifest()
