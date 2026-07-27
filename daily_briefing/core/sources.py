"""Source registry: maps a config `source` key to a fetcher callable.

Each registered callable accepts a per-block `settings` dict and returns raw
data (a string or list) to be summarised by the script stage. Add a new source
by writing a fetcher and registering it here under a name.
"""

from ..plugins.weather import get_weather
from ..plugins.markets import get_market_data
from ..plugins.tech_news import get_tech_news
from ..plugins.bbc_news import get_bbc_news

STATIC_SOURCE = "static"

_REGISTRY: dict[str, callable] = {}


def register(name: str, fetcher: callable) -> None:
    _REGISTRY[name] = fetcher


def has_source(name: str) -> bool:
    return name == STATIC_SOURCE or name in _REGISTRY


def get_source(name: str) -> callable:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown source '{name}'. Registered: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def registered_names() -> list[str]:
    return sorted(_REGISTRY)


# --- Built-in sources -------------------------------------------------------
register("weather", lambda s: get_weather(
    lat=s.get("lat"), lon=s.get("lon"), location=s.get("location")))
register("markets", lambda s: get_market_data())
register("tech", lambda s: get_tech_news())
register("bbc", lambda s: get_bbc_news())
