import os
from openai import OpenAI
from dotenv import load_dotenv

from daily_briefing.plugins.weather import get_weather
from daily_briefing.plugins.bbc_news import get_bbc_news
from daily_briefing.plugins.markets import get_market_data
from daily_briefing.plugins.tech_news import get_tech_news
from daily_briefing.core.llm import generate_script
from daily_briefing.core.audio import create_audio

def get_briefing_data(lat, lon, location_name):
    data = {}
    
    # Stock Market
    data["market"] = get_market_data()

    # Tech News
    data["tech"] = get_tech_news()

    # World News (BBC)
    data["world"] = get_bbc_news()

    # Weather
    data["weather"] = get_weather(lat=lat, lon=lon, location=location_name)
    
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
    user_location = os.getenv("WEATHER_LOCATION_NAME", "Local Area")

    print(f"Fetching data for {user_name} (Location: {weather_lat}, {weather_lon} - {user_location})...")
    raw_data = get_briefing_data(weather_lat, weather_lon, user_location)
    
    print(f"Writing script in {target_language}...")
    script = generate_script(raw_data, client, language=target_language, user_name=user_name)
    print(f"Script: \n{script}\n")
    
    print("Generating audio...")
    audio_file = create_audio(script, client, language=target_language)
    print(f"Done! Saved to {audio_file}")
    
    print("Uploading to Google Cloud Storage...")
    from daily_briefing.core.storage import upload_to_gcs
    
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        print("Error: GCS_BUCKET_NAME not found in .env")
    else:
        # Upload 1: Specific filename
        file_name = os.path.basename(audio_file)
        public_url_1 = upload_to_gcs(audio_file, bucket_name, file_name)
        
        # Upload 2: Latest version
        latest_file_name = f"briefing_{target_language}_latest.mp3"
        public_url_2 = upload_to_gcs(audio_file, bucket_name, latest_file_name)

        if public_url_1:
            print(f"Successfully uploaded: {public_url_1}")
        if public_url_2:
            print(f"Successfully uploaded latest version: {public_url_2}")