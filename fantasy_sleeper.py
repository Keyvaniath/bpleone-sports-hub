"""
Sleeper fantasy API wrapper.
Docs: https://docs.sleeper.com/

Read-only, no auth. Supports NFL and NBA leagues.
Verified 2026-05-14.
"""
from __future__ import annotations

import time
from typing import Any

import requests

BASE = "https://api.sleeper.app/v1"
TIMEOUT = 10
USER_AGENT = "bpleone-sports-hub/1.0"

_cache: dict[str, tuple[float, Any]] = {}


def _get(path: str, ttl: int = 300) -> Any:
    url = f"{BASE}/{path.lstrip('/')}"
    now = time.time()
    if url in _cache:
        ts, val = _cache[url]
        if now - ts < ttl:
            return val
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        if r.status_code == 404:
            _cache[url] = (now, None)
            return None
        r.raise_for_status()
        data = r.json()
        _cache[url] = (now, data)
        return data
    except Exception as e:
        import sys
        print(f"[sleeper] {url} -> {e}", file=sys.stderr)
        return None


def get_user(username: str) -> dict | None:
    """Find Sleeper user by username (case-insensitive)."""
    if not username:
        return None
    return _get(f"user/{username}")


def get_user_leagues(user_id: str, sport: str = "nfl", season: str = "2026") -> list[dict]:
    leagues = _get(f"user/{user_id}/leagues/{sport}/{season}")
    return leagues or []


def get_league(league_id: str) -> dict | None:
    return _get(f"league/{league_id}")


def get_league_rosters(league_id: str) -> list[dict]:
    rosters = _get(f"league/{league_id}/rosters")
    return rosters or []


def get_league_users(league_id: str) -> list[dict]:
    users = _get(f"league/{league_id}/users")
    return users or []


def get_league_matchups(league_id: str, week: int) -> list[dict]:
    m = _get(f"league/{league_id}/matchups/{week}")
    return m or []


def get_nfl_state() -> dict:
    return _get("state/nfl") or {}


def get_players(sport: str = "nfl") -> dict:
    """WARNING: large payload (~5MB for NFL). Cache aggressively."""
    return _get(f"players/{sport}", ttl=86400) or {}
