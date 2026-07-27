"""Generate short Spanish samples across candidate OpenAI voices so you can pick
the one whose accent you like, then set it in config.json (tts.voices.es).

    uv run scripts/voice_samples.py

Writes MP3s to samples/ using gpt-4o-mini-tts with the Latin American accent
instruction. Costs a few small TTS calls.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

CANDIDATE_VOICES = ["nova", "shimmer", "coral", "sage", "alloy", "verse"]
SAMPLE_TEXT = "Buenos días. Hoy hace sol y la temperatura es de veinte grados."
INSTRUCTIONS = (
    "Speak with a natural, native Latin American Spanish accent. "
    "Clear and warm, at a moderate pace suitable for a language learner."
)


def main() -> None:
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    os.makedirs("samples", exist_ok=True)
    for voice in CANDIDATE_VOICES:
        print(f"Generating sample for '{voice}'...")
        try:
            resp = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=SAMPLE_TEXT,
                instructions=INSTRUCTIONS,
                response_format="mp3",
            )
            path = os.path.join("samples", f"voice_{voice}.mp3")
            with open(path, "wb") as f:
                f.write(resp.read())
            print(f"  -> {path}")
        except Exception as e:  # noqa: BLE001
            print(f"  ! failed for '{voice}': {e}")
    print("\nListen to samples/voice_*.mp3 and set tts.voices.es in config.json.")


if __name__ == "__main__":
    main()
