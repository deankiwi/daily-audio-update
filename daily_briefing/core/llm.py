from .utils import get_formatted_date_instruction

def generate_script(data, client, language="Spanish", user_name="Dean"):
    # Language mapping for level
    if language.lower() == "spanish":
        level = "A1/A2"
    elif language.lower() == "french":
        level = "A1/A2"
    elif language.lower() == "german":
        level = "A1/A2"
    else:
        level = "beginner"

    formatted_date_instruction = get_formatted_date_instruction()

    system_prompt = f"""
    You are a helpful {language} teacher for a beginner student (Level {level}).
    Take the provided daily briefing data and rewrite it into a simple {language} script.
    The student you are teaching is {user_name}. Please use their name in the script.
    
    Rules:
    1. Use simple grammar (Present tense mostly, simple past).
    2. Use high-frequency vocabulary.
    3. If a technical term is hard, explain it simply.
    4. Structure the briefing as follows:
    - Greeting ("Good morning..." in {language})
    - State today's date (Translate "{formatted_date_instruction}" to {language})
    - Weather Forecast
    - Market Update
    - Tech News (Top 3 stories)
    - World News (Headlines)
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
