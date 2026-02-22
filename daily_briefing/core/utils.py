from datetime import datetime

def get_formatted_date_instruction() -> str:
    """
    Returns today's date formatted with ordinal suffixes.
    e.g. 'Today is Sunday the 22nd February 2026'
    """
    today = datetime.now()
    day = today.day
    if 11 <= (day % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    formatted_date = today.strftime(f"%A the {day}{suffix} %B %Y")
    return f"Today is {formatted_date}"
