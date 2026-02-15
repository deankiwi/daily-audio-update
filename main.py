import os
from openai import OpenAI
from dotenv import load_dotenv

from daily_briefing.plugins.weather import get_weather
from daily_briefing.plugins.bbc_news import get_bbc_news
from daily_briefing.plugins.markets import get_market_data
from daily_briefing.plugins.tech_news import get_tech_news
from daily_briefing.core.llm import generate_script
from daily_briefing.core.audio import create_audio

def get_briefing_data(lat, lon):
    data = {}
    
    # Stock Market
    data["market"] = get_market_data()

    # Tech News
    data["tech"] = get_tech_news()

    # World News (BBC)
    data["world"] = get_bbc_news()

    # Weather
    data["weather"] = get_weather(lat=lat, lon=lon)
    
    return data

# MAIN EXECUTION
if __name__ == "__main__":
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Load configuration
    weather_lat = os.getenv("WEATHER_LAT", "51.21")
    weather_lon = os.getenv("WEATHER_LON", "-0.79")
    target_language = os.getenv("TARGET_LANGUAGE", "Spanish")
    user_name = os.getenv("USER_NAME", "Dean")

    print(f"Fetching data for {user_name} (Location: {weather_lat}, {weather_lon})...")
    raw_data = get_briefing_data(weather_lat, weather_lon)
    
    print(f"Writing script in {target_language}...")
    script = generate_script(raw_data, client, language=target_language, user_name=user_name)
    print(f"Script: \n{script}\n")
    
    print("Generating audio...")
    audio_file = create_audio(script, client, language=target_language)
    print(f"Done! Saved to {audio_file}")
    
    print("Uploading to Google Drive...")
    from daily_briefing.core.drive import upload_file
    file_id = upload_file(audio_file)
    if file_id:
        print(f"Successfully uploaded to Google Drive with ID: {file_id}")
    else:
        print("Failed to upload to Google Drive.")