"""Tide predictor: next high tide time & height from maths -- no external API.

The water level is modelled as a mean level plus a sum of harmonic tidal
constituents:

    h(t) = Z0 + Sum_i A_i * cos(w_i * dt - g_i)

where `dt` is the number of hours since a reference epoch, `w_i` is each
constituent's fixed astronomical speed, and `A_i` / `g_i` are its amplitude and
phase. High tides are the local maxima of h(t); we report today's and
tomorrow's in the port's local time zone.

The Warrenpoint defaults were obtained by a least-squares fit of five
constituents -- M2 (principal lunar), S2 (principal solar), N2 (larger lunar
elliptic), and the diurnal K1/O1 -- to every high and low water in the official
UKHO Warrenpoint Port tide tables for 2026 (all 1411 high/low waters). Across
the year this reproduces the book's high waters to a mean of ~17 min and
~0.10 m (worst case ~48 min).

Note: the amplitudes and phases are fitted to *2026* and are referenced to a
2026 epoch. Constituent phases drift slightly year to year (nodal cycle), so
for best accuracy in a later year, refit against that year's tables. Override
any of the values below in the block's `settings` (e.g. to model another port).
"""

import math
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

# Warrenpoint (Carlingford Lough), fitted to UKHO 2026 tide tables.
# Each constituent: (name, speed [deg/hour], amplitude [m], phase [deg]).
_DEFAULTS = {
    "name": "Warrenpoint",
    "tz": "Europe/Dublin",             # spoken time zone (IST in summer)
    "epoch": "2026-01-01T00:00:00Z",   # phase reference for the fit
    "z0": 2.8060,                      # mean level above chart datum (m)
    "constituents": [
        ("M2", 28.9841042, 1.7551, 265.224),
        ("S2", 30.0000000, 0.4585,  13.268),
        ("N2", 28.4397295, 0.2357, 249.982),
        ("K1", 15.0410686, 0.1099, 181.618),
        ("O1", 13.9430356, 0.1289, 358.367),
    ],
}


def _height(dt_hours: float, z0: float, constituents: list) -> float:
    """Water level (m above chart datum) `dt_hours` after the epoch."""
    return z0 + sum(
        amp * math.cos(math.radians(speed * dt_hours - phase))
        for _name, speed, amp, phase in constituents
    )


def _high_tides(start: datetime, end: datetime, s: dict) -> list[tuple[datetime, float]]:
    """Every high tide (local maximum of the level) between `start` and `end`.

    Returns (utc_time, height) pairs by walking a minute at a time and marking
    each point that is higher than its neighbours.
    """
    epoch = datetime.fromisoformat(str(s["epoch"]).replace("Z", "+00:00"))
    step = timedelta(minutes=1)
    peaks: list[tuple[datetime, float]] = []
    prev_time = prev_height = None
    rising = False
    t = start
    while t <= end:
        h = _height((t - epoch).total_seconds() / 3600.0, s["z0"], s["constituents"])
        if prev_height is not None:
            if h > prev_height:
                rising = True
            elif rising:  # was rising, now falling: prev point was a high tide
                peaks.append((prev_time, prev_height))
                rising = False
        prev_time, prev_height = t, h
        t += step
    return peaks


def _join(labels: list[str]) -> str:
    """'a', 'a and b', or 'a, b and c'."""
    if len(labels) == 1:
        return labels[0]
    return " and ".join([", ".join(labels[:-1]), labels[-1]])


def _day_sentence(lead: str, name: str, tides: list[tuple[datetime, float]]) -> str:
    """One sentence: times, then the heights above chart datum in brackets."""
    if not tides:
        return f"{lead} there is no high tide in {name}."
    times = _join([f"{t:%H:%M}" for t, _h in tides])
    heights = _join([f"{h:.1f}" for _t, h in tides])
    return f"{lead} high tide in {name} at {times} ({heights} metres above chart datum)."


def get_tides(settings: dict | None = None, now: datetime | None = None) -> str:
    s = {**_DEFAULTS, **(settings or {})}
    tz = ZoneInfo(s["tz"])
    if now is None:
        now = datetime.now(timezone.utc)

    today = now.astimezone(tz).date()
    tomorrow = today + timedelta(days=1)
    # Scan local midnight today through local midnight after tomorrow, so both
    # days' high tides are captured, then bucket them by local calendar day.
    start = datetime.combine(today, time.min, tz)
    end = datetime.combine(tomorrow + timedelta(days=1), time.min, tz)
    by_day: dict = {today: [], tomorrow: []}
    for utc_time, height in _high_tides(start.astimezone(timezone.utc),
                                        end.astimezone(timezone.utc), s):
        local = utc_time.astimezone(tz)
        if local.date() in by_day:
            by_day[local.date()].append((local, height))

    return (
        _day_sentence("Today,", s["name"], by_day[today]) + " "
        + _day_sentence("Tomorrow,", s["name"], by_day[tomorrow])
    )
