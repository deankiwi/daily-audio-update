import requests

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
