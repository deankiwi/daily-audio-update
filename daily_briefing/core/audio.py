from datetime import date
import os
from mutagen.id3 import ID3, USLT, ID3NoHeaderError

def create_audio(script, client, language="spanish"):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy", # 'alloy' is usually quite clear and neutral
        input=script,
        speed=1.0 # SLOW DOWN the audio slightly for beginners!
    )
    
    # Ensure the recordings directory exists
    output_dir = "recordings"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_filename = f"briefing_{language}_{date.today()}"
    extension = ".mp3"
    filename = os.path.join(output_dir, f"{base_filename}{extension}")

    counter = 1
    while os.path.exists(filename):
        filename = os.path.join(output_dir, f"{base_filename}_{counter}{extension}")
        counter += 1

    with open(filename, "wb") as f:
        for chunk in response.iter_bytes():
            f.write(chunk)

    # Embed the script as USLT lyrics in the MP3
    try:
        tags = ID3(filename)
    except ID3NoHeaderError:
        tags = ID3()

    # Determine a crude 3-letter language code required by ID3 (eng/spa/etc.)
    lang_code = "spa" if language.lower().startswith("spa") else "eng"

    tags.add(USLT(
        encoding=3, # utf-8
        lang=lang_code,
        desc='Daily Briefing Script',
        text=script
    ))
    tags.save(filename)

    return filename
