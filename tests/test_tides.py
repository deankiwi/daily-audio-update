import math
import re
from datetime import datetime, timedelta, timezone

from daily_briefing.core import sources
from daily_briefing.plugins.tides import get_tides, _high_tides, _height, _DEFAULTS


def test_tides_source_is_registered():
    assert sources.has_source("tides")
    assert "tides" in sources.registered_names()


def test_output_is_two_sentences_today_and_tomorrow():
    out = get_tides({"name": "Warrenpoint"},
                    now=datetime(2026, 7, 27, 8, 0, tzinfo=timezone.utc))
    assert out.startswith("Today, high tide in Warrenpoint at ")
    today_part, tomorrow_part = out.split("Tomorrow,")
    # Exactly two sentences (one ". " break; decimals use "." with no space).
    assert out.count(". ") == 1
    assert out.endswith(".")
    assert "metres above chart datum" in today_part
    assert "metres above chart datum" in tomorrow_part
    assert len(re.findall(r"\d\d:\d\d", today_part)) == 2
    assert len(re.findall(r"\d\d:\d\d", tomorrow_part)) == 2


def test_height_is_mean_level_plus_constituents():
    # At the epoch, every constituent contributes A*cos(-phase).
    z0 = _DEFAULTS["z0"]
    expected = z0 + sum(a * math.cos(math.radians(-g))
                        for _n, _s, a, g in _DEFAULTS["constituents"])
    assert abs(_height(0.0, z0, _DEFAULTS["constituents"]) - expected) < 1e-9


# A sample of official UKHO high waters (times in GMT/UTC, heights in m).
BOOK_HIGH_WATERS = [
    (datetime(2026, 7, 27, 22, 17, tzinfo=timezone.utc), 4.6),   # near a neap
    (datetime(2026, 8, 13, 23, 44, tzinfo=timezone.utc), 5.4),   # a big spring
    (datetime(2026, 8, 31, 0, 35, tzinfo=timezone.utc), 5.1),    # a spring
    (datetime(2026, 1, 1, 9, 6, tzinfo=timezone.utc), 4.7),      # winter (GMT)
]


def test_matches_official_tide_table_within_tolerance():
    for book_time, book_height in BOOK_HIGH_WATERS:
        peaks = _high_tides(book_time - timedelta(hours=6),
                            book_time + timedelta(hours=6), _DEFAULTS)
        best = min(peaks, key=lambda p: abs((p[0] - book_time).total_seconds()))
        assert abs((best[0] - book_time).total_seconds()) <= 60 * 60, (
            f"time off for {book_time}: predicted {best[0]}")
        assert abs(best[1] - book_height) <= 0.4, (
            f"height off for {book_time}: predicted {best[1]:.2f}")


def test_local_times_follow_dst():
    # In summer, Europe/Dublin is one hour ahead of UTC, so the same high tide
    # should be printed an hour later than when rendered in UTC.
    now = datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc)
    utc_h, utc_m = re.search(r"at (\d\d):(\d\d)",
                             get_tides({"tz": "UTC"}, now=now)).groups()
    dub_h, dub_m = re.search(r"at (\d\d):(\d\d)",
                             get_tides({"tz": "Europe/Dublin"}, now=now)).groups()
    assert dub_m == utc_m
    assert int(dub_h) == (int(utc_h) + 1) % 24


def test_name_setting_is_used():
    out = get_tides({"name": "Testport"},
                    now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert "Testport" in out
