"""
Weather lookup for outdoor home games (NFL/MLB/CFB/CBB).
Uses Open-Meteo — free, no API key.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import requests

TIMEOUT = 10
USER_AGENT = "bpleone-sports-hub/1.0"

# Stadium coords for Brandon's teams' home venues (and a few common road venues)
VENUE_COORDS = {
    # Home venues
    "Crypto.com Arena": (34.0430, -118.2673, False),  # Lakers — indoor, skip
    "Dodger Stadium": (34.0739, -118.2400, True),
    "SoFi Stadium": (33.9534, -118.3387, False),       # NFL — indoor (covered)
    "Los Angeles Memorial Coliseum": (34.0141, -118.2879, True),
    "Galen Center": (34.0202, -118.2858, False),       # USC basketball — indoor
    "Dedeaux Field": (34.0223, -118.2860, True),       # USC baseball

    # Common away venues
    "Oracle Park": (37.7786, -122.3893, True),
    "Petco Park": (32.7077, -117.1573, True),
    "Angel Stadium": (33.8003, -117.8827, True),
    "Yankee Stadium": (40.8296, -73.9262, True),
    "Citi Field": (40.7571, -73.8458, True),
    "Wrigley Field": (41.9484, -87.6553, True),
}

_cache: dict[str, tuple[float, Any]] = {}


def is_outdoor(venue: str | None) -> bool:
    if not venue:
        return False
    info = VENUE_COORDS.get(venue)
    if info is None:
        return False
    return info[2]


def get_forecast_for_event(venue: str | None, date_iso: str | None) -> dict | None:
    """Returns {temp_f, wind_mph, precip_pct, summary} for the hour of the event.
    None if indoor venue, unknown venue, or fetch failed."""
    if not venue or not date_iso:
        return None
    info = VENUE_COORDS.get(venue)
    if not info:
        return None
    lat, lon, outdoor = info
    if not outdoor:
        return None
    try:
        event_dt = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
    except Exception:
        return None
    # Skip if game is more than 7 days out — Open-Meteo forecast horizon
    if (event_dt - datetime.now(timezone.utc)).total_seconds() > 7 * 86400:
        return None
    key = f"{lat},{lon},{event_dt.date()}"
    now = time.time()
    if key in _cache:
        ts, val = _cache[key]
        if now - ts < 1800:  # 30 min cache
            return val
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "hourly": "temperature_2m,precipitation_probability,windspeed_10m,weathercode",
                "temperature_unit": "fahrenheit",
                "windspeed_unit": "mph",
                "forecast_days": 7,
                "timezone": "auto",
            },
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        _cache[key] = (now, None)
        return None
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    # Find nearest hour
    event_hour = event_dt.astimezone().strftime("%Y-%m-%dT%H:00")
    if event_hour not in times:
        # Fallback: nearest by string compare
        candidates = [t for t in times if t.startswith(event_dt.astimezone().strftime("%Y-%m-%d"))]
        if not candidates:
            _cache[key] = (now, None)
            return None
        target = min(candidates, key=lambda t: abs(int(t[11:13]) - event_dt.astimezone().hour))
        idx = times.index(target)
    else:
        idx = times.index(event_hour)
    out = {
        "temp_f": hourly.get("temperature_2m", [None])[idx],
        "wind_mph": hourly.get("windspeed_10m", [None])[idx],
        "precip_pct": hourly.get("precipitation_probability", [None])[idx],
        "code": hourly.get("weathercode", [None])[idx],
        "venue": venue,
    }
    out["summary"] = _weather_code_to_str(out.get("code"))
    _cache[key] = (now, out)
    return out


# WMO weather interpretation codes (Open-Meteo)
WX = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    95: "Thunderstorm", 96: "Storm w/ hail", 99: "Severe storm",
}


def _weather_code_to_str(code) -> str:
    try:
        return WX.get(int(code), "Unknown")
    except Exception:
        return "Unknown"
