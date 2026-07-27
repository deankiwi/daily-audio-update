from datetime import datetime

SPANISH_WEEKDAYS = {
    0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves",
    4: "viernes", 5: "sábado", 6: "domingo",
}

SPANISH_MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre",
    11: "noviembre", 12: "diciembre",
}


def _ordinal_suffix(day: int) -> str:
    if 11 <= (day % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def get_formatted_date_instruction(today: datetime | None = None) -> str:
    """English date with an ordinal suffix, e.g. 'Today is Sunday the 22nd February 2026'."""
    today = today or datetime.now()
    day = today.day
    formatted = today.strftime(f"%A the {day}{_ordinal_suffix(day)} %B %Y")
    return f"Today is {formatted}"


def get_template_vars(name: str, today: datetime | None = None) -> dict[str, str]:
    """Values available for {placeholder} substitution in static block sentences."""
    today = today or datetime.now()
    day = today.day
    return {
        "name": name,
        "weekday_es": SPANISH_WEEKDAYS[today.weekday()],
        "weekday_en": today.strftime("%A"),
        "date_es": f"{day} de {SPANISH_MONTHS[today.month]} de {today.year}",
        "date_en": today.strftime(f"%A the {day}{_ordinal_suffix(day)} %B %Y"),
    }


def fill_template(text: str, variables: dict[str, str]) -> str:
    """Substitute {placeholders}; unknown placeholders are left untouched."""
    for key, value in variables.items():
        text = text.replace("{" + key + "}", str(value))
    return text
