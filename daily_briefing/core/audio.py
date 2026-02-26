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

    # 1. Embed the script as USLT lyrics in the MP3
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

    # 2. Use Whisper to get timestamps for SYLT (Synced Lyrics)
    print(f"Fetching timestamps for SYLT via Whisper...")
    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    # Build the SYLT text array
    # mutagen.id3.SYLT requires a list of (text, timestamp_in_ms) tuples
    sylt_data = []
    
    # Optional: include an initial timestamp
    sylt_data.append(("", 0))
    
    if hasattr(transcript, 'segments') and transcript.segments:
        for segment in transcript.segments:
            # Whisper segment timestamps are in seconds; segment is an object
            start_ms = int(getattr(segment, 'start', 0) * 1000)
            text = getattr(segment, 'text', '').strip()
            sylt_data.append((text, start_ms))
    elif isinstance(transcript, dict) and 'segments' in transcript:
        for segment in transcript['segments']:
            start_ms = int(segment['start'] * 1000)
            text = segment['text'].strip()
            sylt_data.append((text, start_ms))

    # 3. Create a traditional .lrc file alongside the MP3
    lrc_filename = os.path.splitext(filename)[0] + ".lrc"
    with open(lrc_filename, "w", encoding="utf-8") as lrc_file:
        # Optional LRC headers
        lrc_file.write(f"[ti:Daily Briefing]\n")
        lrc_file.write(f"[ar:AI]\n")
        lrc_file.write(f"[al:{date.today()}]\n")
        lrc_file.write(f"[la:{lang_code}]\n")
        
        for text, start_ms in sylt_data:
            if not text:
                continue
            
            # Format: [mm:ss.xx]
            total_seconds = start_ms / 1000.0
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            hundredths = int((total_seconds * 100) % 100)
            
            lrc_file.write(f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]{text}\n")

    from mutagen.id3 import SYLT
    
    tags.add(SYLT(
        encoding=3, # utf-8
        lang=lang_code,
        format=2,   # 2 = milliseconds
        type=1,     # 1 = lyrics/text
        desc='Daily Briefing Synced Script',
        text=sylt_data
    ))

    tags.save(filename)

    return filename
