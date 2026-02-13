from datetime import date

def create_audio(script, client):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy", # 'alloy' is usually quite clear and neutral
        input=script,
        speed=1.0 # SLOW DOWN the audio slightly for beginners!
    )
    
    filename = f"briefing_{date.today()}.mp3"
    with open(filename, "wb") as f:
        for chunk in response.iter_bytes():
            f.write(chunk)
    return filename
