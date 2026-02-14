import os
from openai import OpenAI
from dotenv import load_dotenv

from daily_briefing.plugins.weather import get_weather
from daily_briefing.plugins.bbc_news import get_bbc_news
from daily_briefing.plugins.markets import get_market_data
from daily_briefing.plugins.tech_news import get_tech_news
from daily_briefing.core.llm import generate_spanish_script
from daily_briefing.core.audio import create_audio

def get_briefing_data():
    data = {}
    
    # Stock Market
    data["market"] = get_market_data()

    # Tech News
    data["tech"] = get_tech_news()

    # World News (BBC)
    data["world"] = get_bbc_news()

    # Weather (Farnham)
    data["weather"] = get_weather()
    
    return data

# MAIN EXECUTION
if __name__ == "__main__":
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("Fetching data...")
    raw_data = get_briefing_data()
    
    print("Writing script...")
    spanish_script = generate_spanish_script(raw_data, client)
    print(f"Script: \n{spanish_script}\n")
    
    print("Generating audio...")
    audio_file = create_audio(spanish_script, client)
    print(f"Done! Saved to {audio_file}")
    
    print("Uploading to Google Drive...")
    from daily_briefing.core.drive import upload_file
    file_id = upload_file(audio_file)
    if file_id:
        print(f"Successfully uploaded to Google Drive with ID: {file_id}")
    else:
        print("Failed to upload to Google Drive.")