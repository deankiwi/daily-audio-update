import os
import yfinance as yf
import requests
import xml.etree.ElementTree as ET
from openai import OpenAI
from datetime import date
from dotenv import load_dotenv

# 1. GATHER DATA
def get_weather(lat=51.21, lon=-0.79):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        daily = data.get("daily", {})
        
        # Simple forecast for today
        t_max = daily["temperature_2m_max"][0]
        t_min = daily["temperature_2m_min"][0]
        
        return f"Weather in Farnham: High of {t_max}°C, Low of {t_min}°C."
    except Exception as e:
        return f"Weather data unavailable: {e}"

def get_bbc_news():
    try:
        res = requests.get("http://feeds.bbci.co.uk/news/rss.xml")
        res.raise_for_status()
        root = ET.fromstring(res.content)
        
        headlines = []
        # namespace handling can be tricky, but standard RSS usually has item under channel
        for item in root.findall(".//item")[:3]:
            title = item.find("title").text
            headlines.append(title)
            
        return headlines
    except Exception as e:
        return [f"BBC News unavailable: {e}"]

def get_briefing_data():
    data = {}
    
    # Stock Market (S&P 500 & NASDAQ)
    try:
        sp500 = yf.Ticker("^GSPC").history(period="1d")['Close'].iloc[-1]
        nasdaq = yf.Ticker("^IXIC").history(period="1d")['Close'].iloc[-1]
        data["market"] = f"S&P 500 is at {int(sp500)}, NASDAQ is at {int(nasdaq)}."
    except Exception:
        data["market"] = "Market data unavailable."

    # Tech News (Hacker News Top 3)
    try:
        hn_ids = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()[:3]
        hn_stories = []
        for hid in hn_ids:
            story = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{hid}.json').json()
            hn_stories.append(story.get('title', 'Unknown Title'))
        data["tech"] = hn_stories
    except Exception:
        data["tech"] = ["Tech news unavailable."]

    # World News (BBC)
    data["world"] = get_bbc_news()

    # Weather (Farnham)
    data["weather"] = get_weather()
    
    return data

# 2. GENERATE SCRIPT (The Pedagogical Transformation)
def generate_spanish_script(data, client):
    system_prompt = """
    You are a helpful Spanish teacher for a beginner student (Level A1/A2).
    Take the provided daily briefing data and rewrite it into a simple Spanish script.
    
    Rules:
    1. Use simple grammar (Present tense mostly, simple past).
    2. Use high-frequency vocabulary.
    3. If a technical term is hard, explain it simply.
    4. Structure the briefing as follows:
       - Greeting ("Buenos días...")
       - Weather Forecast (Farnham)
       - Market Update
       - Tech News (Top 3 stories)
       - World News (BBC Headlines)
    5. Keep it engaging but clear.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(data)}
        ]
    )
    return response.choices[0].message.content

# 3. TEXT TO SPEECH
def create_audio(script, client):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy", # 'alloy' is usually quite clear and neutral
        input=script,
        speed=0.9 # SLOW DOWN the audio slightly for beginners!
    )
    
    filename = f"briefing_{date.today()}.mp3"
    with open(filename, "wb") as f:
        for chunk in response.iter_bytes():
            f.write(chunk)
    return filename

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