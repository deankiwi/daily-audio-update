def generate_spanish_script(data, client):
    system_prompt = """
    You are a helpful Spanish teacher for a beginner student (Level A1/A2).
    Take the provided daily briefing data and rewrite it into a simple Spanish script.
    The student you are teaching is Dean. Please use his name in the script.
    
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
