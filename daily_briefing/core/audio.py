from datetime import date

import os

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
    return filename
