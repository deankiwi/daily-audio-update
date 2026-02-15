import requests
from datetime import date, timedelta

def get_weather(lat=None, lon=None, location=None):
    # Defaults for Farnham if not provided
    if lat is None:
        lat = 51.21
    if lon is None:
        lon = -0.79
        
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=auto"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        daily = data.get("daily", {})
        
        forecast_lines = []
        loc_str = f" in {location}" if location else ""
        forecast_lines.append(f"Weather Forecast{loc_str}:")
        
        # Get next 3 days
        for i in range(3):
            day_date = date.today() + timedelta(days=i)
            day_name = day_date.strftime("%A") # e.g. Monday
            
            t_max = daily["temperature_2m_max"][i]
            t_min = daily["temperature_2m_min"][i]
            precip_sum = daily["precipitation_sum"][i]
            precip_prob = daily["precipitation_probability_max"][i]
            
            rain_msg = ""
            if precip_prob > 0:
                 rain_msg = f" Rain chance: {precip_prob}% ({precip_sum}mm)."
            else:
                 rain_msg = " No rain expected."
            
            forecast_lines.append(f"- {day_name}: High {t_max}°C, Low {t_min}°C.{rain_msg}")
            
        return "\n".join(forecast_lines)
    except Exception as e:
        return f"Weather data unavailable: {e}"
