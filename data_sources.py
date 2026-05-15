"""
ESPN data layer for the Sports Hub.

All endpoints are ESPN's public/unofficial JSON. No auth required.
Verified working 2026-05-14.

Base URLs:
  site.api.espn.com/apis/site/v2/sports/{sport}/{league}/...
  cdn.espn.com/core/{league}/standings?xhr=1

We keep a tiny in-memory TTL cache so repeated Streamlit reruns
don't hammer ESPN within a single user session. Streamlit's own
@st.cache_data wraps this from streamlit_app.py for cross-session caching.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from typing import Any

import requests

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_CDN = "https://cdn.espn.com/core"
ESPN_CORE = "https://sports.core.api.espn.com/v2/sports"

USER_AGENT = "bpleone-sports-hub/1.0 (+https://sports.bpleone.com)"
TIMEOUT = 15

_cache: dict[str, tuple[float, Any]] = {}


def _get(url: str, ttl: int = 60, params: dict | None = None) -> dict:
    """GET JSON with a small TTL cache. Returns {} on failure (logs to stderr)."""
    key = url + ("?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items())) if params else "")
    now = time.time()
    if key in _cache:
        ts, val = _cache[key]
        if now - ts < ttl:
            return val
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        data = r.json()
        _cache[key] = (now, data)
        return data
    except Exception as e:
        import sys
        print(f"[data_sources] {url} -> {e}", file=sys.stderr)
        _cache[key] = (now, {})
        return {}


# ---------- Team summary ----------
def get_team_summary(team: dict) -> dict:
    """Display name, record, logo, conference, etc."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/teams/{team['espn_id']}"
    data = _get(url, ttl=300)
    t = data.get("team", {}) if data else {}
    record_items = t.get("record", {}).get("items", [])
    summary = record_items[0].get("summary") if record_items else None
    standing_summary = t.get("standingSummary")
    logos = t.get("logos", [])
    logo = logos[0].get("href") if logos else None
    return {
        "name": t.get("displayName", team["name"]),
        "short": t.get("shortDisplayName", team["short"]),
        "abbr": t.get("abbreviation", team["espn_abbr"].upper()),
        "record": summary,
        "standing": standing_summary,
        "logo": logo,
        "color": "#" + t.get("color", team["color"].lstrip("#")),
        "alternate_color": "#" + t.get("alternateColor", team["accent"].lstrip("#")),
        "links": t.get("links", []),
    }


# ---------- Schedule ----------
def get_schedule(team: dict) -> list[dict]:
    """Returns full season schedule, normalized to a flat list."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/teams/{team['espn_id']}/schedule"
    data = _get(url, ttl=300)
    events = data.get("events", []) if data else []
    return [_normalize_event(e, team) for e in events]


def _normalize_event(e: dict, team: dict) -> dict:
    comp = (e.get("competitions") or [{}])[0]
    competitors = comp.get("competitors", [])
    home, away = None, None
    for c in competitors:
        side = c.get("homeAway")
        info = {
            "name": c.get("team", {}).get("displayName"),
            "abbr": c.get("team", {}).get("abbreviation"),
            "logo": c.get("team", {}).get("logo") or c.get("team", {}).get("logos", [{}])[0].get("href"),
            "score": c.get("score", {}).get("displayValue") if isinstance(c.get("score"), dict) else c.get("score"),
            "winner": c.get("winner"),
            "record": (c.get("records") or [{}])[0].get("summary"),
        }
        if side == "home":
            home = info
        else:
            away = info
    status = comp.get("status", {})
    status_type = status.get("type", {})
    venue = comp.get("venue", {})
    broadcasts = comp.get("broadcasts") or []
    broadcast_names = []
    for b in broadcasts:
        names = b.get("names") or []
        broadcast_names.extend(names)
    return {
        "id": e.get("id"),
        "date": e.get("date"),
        "name": e.get("name"),
        "short_name": e.get("shortName"),
        "status_state": status_type.get("state"),  # pre, in, post
        "status_desc": status_type.get("description"),
        "status_detail": status.get("displayClock") or status_type.get("detail"),
        "period": status.get("period"),
        "completed": status_type.get("completed", False),
        "home": home,
        "away": away,
        "venue": venue.get("fullName"),
        "city": venue.get("address", {}).get("city"),
        "broadcasts": broadcast_names,
        "is_home_game": (home and home.get("abbr", "").lower() == team["espn_abbr"].lower()),
        "team_abbr": team["espn_abbr"].upper(),
    }


def split_schedule(events: list[dict]) -> dict[str, list[dict]]:
    """Bucket into past / live / upcoming relative to now."""
    now = datetime.now(timezone.utc)
    past, live, upcoming = [], [], []
    for e in events:
        try:
            dt = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        except Exception:
            continue
        e["_dt"] = dt
        state = e.get("status_state")
        if state == "in":
            live.append(e)
        elif e.get("completed") or dt < now - timedelta(hours=6):
            past.append(e)
        else:
            upcoming.append(e)
    past.sort(key=lambda x: x["_dt"], reverse=True)
    upcoming.sort(key=lambda x: x["_dt"])
    return {"past": past, "live": live, "upcoming": upcoming}


# ---------- League scoreboard (today's games) ----------
def get_scoreboard(team: dict) -> list[dict]:
    """All games today in this team's league, normalized."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/scoreboard"
    data = _get(url, ttl=30)
    events = data.get("events", []) if data else []
    return [_normalize_event(e, team) for e in events]


# ---------- Roster ----------
def get_roster(team: dict) -> list[dict]:
    """Returns flat list of athletes. Some leagues group by position
    (athletes is list of {position, items}); others give flat list."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/teams/{team['espn_id']}/roster"
    data = _get(url, ttl=600)
    athletes = data.get("athletes", []) if data else []
    flat = []
    for entry in athletes:
        if isinstance(entry, dict) and "items" in entry:
            group = entry.get("position", "")
            for a in entry.get("items", []):
                flat.append(_norm_athlete(a, group))
        elif isinstance(entry, dict):
            flat.append(_norm_athlete(entry))
    return flat


def _norm_athlete(a: dict, group: str = "") -> dict:
    pos = a.get("position", {}) or {}
    inj = a.get("injuries", []) or []
    inj0 = inj[0] if inj else {}
    return {
        "id": a.get("id"),
        "name": a.get("fullName") or a.get("displayName"),
        "jersey": a.get("jersey"),
        "position": pos.get("abbreviation") if isinstance(pos, dict) else None,
        "position_group": group,
        "age": a.get("age"),
        "height": a.get("displayHeight"),
        "weight": a.get("displayWeight"),
        "experience": (a.get("experience") or {}).get("years"),
        "headshot": (a.get("headshot") or {}).get("href") if isinstance(a.get("headshot"), dict) else None,
        "status": (a.get("status") or {}).get("name") if isinstance(a.get("status"), dict) else None,
        "injury_status": inj0.get("status"),
        "injury_type": (inj0.get("details") or {}).get("type") if isinstance(inj0.get("details"), dict) else None,
    }


# ---------- Injuries ----------
def get_injuries(team: dict) -> list[dict]:
    """Team-level injury feed. ESPN's site.api injuries endpoint
    is often sparse; we also pull from roster as a fallback."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/teams/{team['espn_id']}/injuries"
    data = _get(url, ttl=300)
    out = []
    for inj in data.get("injuries", []) if data else []:
        ath = inj.get("athlete", {})
        out.append({
            "name": ath.get("displayName"),
            "position": (ath.get("position") or {}).get("abbreviation"),
            "headshot": (ath.get("headshot") or {}).get("href") if isinstance(ath.get("headshot"), dict) else None,
            "status": inj.get("status"),
            "type": (inj.get("details") or {}).get("type") if isinstance(inj.get("details"), dict) else None,
            "side": (inj.get("details") or {}).get("side") if isinstance(inj.get("details"), dict) else None,
            "detail": (inj.get("details") or {}).get("detail") if isinstance(inj.get("details"), dict) else None,
            "return_date": (inj.get("details") or {}).get("returnDate") if isinstance(inj.get("details"), dict) else None,
            "short_comment": inj.get("shortComment"),
            "long_comment": inj.get("longComment"),
            "date": inj.get("date"),
        })
    if not out:
        # Fallback: scan roster for any athlete with an injury attached
        for a in get_roster(team):
            if a.get("injury_status"):
                out.append({
                    "name": a.get("name"),
                    "position": a.get("position"),
                    "headshot": a.get("headshot"),
                    "status": a.get("injury_status"),
                    "type": a.get("injury_type"),
                    "side": None,
                    "detail": None,
                    "return_date": None,
                    "short_comment": None,
                    "long_comment": None,
                    "date": None,
                })
    return out


# ---------- News ----------
def get_team_news(team: dict, limit: int = 10) -> list[dict]:
    """League news filtered to this team. ESPN's team news endpoint takes ?team= id."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/news"
    data = _get(url, ttl=300, params={"team": team["espn_id"], "limit": limit})
    return _normalize_news(data.get("articles", []) if data else [])


def get_league_news(team: dict, limit: int = 10) -> list[dict]:
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/news"
    data = _get(url, ttl=300, params={"limit": limit})
    return _normalize_news(data.get("articles", []) if data else [])


def _normalize_news(articles: list[dict]) -> list[dict]:
    out = []
    for a in articles:
        images = a.get("images", []) or []
        thumb = images[0].get("url") if images else None
        links = a.get("links", {}) or {}
        web = (links.get("web") or {}).get("href") if isinstance(links.get("web"), dict) else None
        out.append({
            "headline": a.get("headline"),
            "description": a.get("description"),
            "published": a.get("published"),
            "type": a.get("type"),
            "byline": a.get("byline"),
            "image": thumb,
            "url": web,
        })
    return out


# ---------- Standings ----------
def get_standings(team: dict) -> dict:
    """Returns {conference_name: [entries]} where each entry has team + stats."""
    league = team["league"]
    url = f"{ESPN_CDN}/{league}/standings?xhr=1"
    data = _get(url, ttl=900)
    if not data:
        return {}
    standings = data.get("content", {}).get("standings", {})
    groups = standings.get("groups", []) or [standings]
    out = {}
    for g in groups:
        name = g.get("name") or g.get("abbreviation") or "League"
        entries = []
        std = g.get("standings", {})
        # Some payloads nest entries; others have direct children
        raw_entries = std.get("entries") or []
        if not raw_entries and isinstance(std, list):
            raw_entries = std
        for e in raw_entries:
            t = e.get("team", {})
            stats = {s.get("name"): s.get("displayValue") for s in e.get("stats", [])}
            entries.append({
                "team": t.get("displayName"),
                "abbr": t.get("abbreviation"),
                "logo": t.get("logos", [{}])[0].get("href") if t.get("logos") else None,
                "id": t.get("id"),
                "wins": stats.get("wins"),
                "losses": stats.get("losses"),
                "ties": stats.get("ties"),
                "win_pct": stats.get("winPercent"),
                "games_behind": stats.get("gamesBehind"),
                "streak": stats.get("streak"),
                "home": stats.get("Home"),
                "road": stats.get("Road"),
                "div": stats.get("vs. Div.") or stats.get("Division"),
                "conf": stats.get("vs. Conf.") or stats.get("Conference"),
                "diff": stats.get("differential") or stats.get("pointDifferential"),
                "is_user_team": str(t.get("id")) == str(team["espn_id"]),
            })
        # Some leagues have sub-divisions inside groups
        sub_groups = g.get("groups") or []
        for sg in sub_groups:
            sname = sg.get("name") or sg.get("abbreviation") or "Division"
            sentries = []
            std2 = sg.get("standings", {})
            for e in std2.get("entries", []):
                t = e.get("team", {})
                stats = {s.get("name"): s.get("displayValue") for s in e.get("stats", [])}
                sentries.append({
                    "team": t.get("displayName"),
                    "abbr": t.get("abbreviation"),
                    "id": t.get("id"),
                    "logo": t.get("logos", [{}])[0].get("href") if t.get("logos") else None,
                    "wins": stats.get("wins"),
                    "losses": stats.get("losses"),
                    "ties": stats.get("ties"),
                    "win_pct": stats.get("winPercent"),
                    "games_behind": stats.get("gamesBehind"),
                    "streak": stats.get("streak"),
                    "is_user_team": str(t.get("id")) == str(team["espn_id"]),
                })
            if sentries:
                out[f"{name} — {sname}"] = sentries
        if entries:
            out[name] = entries
    return out


# ---------- Player gamelog ----------
def get_player_gamelog(team: dict, athlete_id: str) -> list[dict]:
    """Recent game logs for a player. Returns up to ~20 most recent games normalized."""
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/{team['sport']}/{team['league']}/athletes/{athlete_id}/gamelog"
    data = _get(url, ttl=600)
    if not data:
        return []
    events = data.get("events", {}) or {}
    if not isinstance(events, dict):
        return []
    season_types = data.get("seasonTypes", []) or []
    names = data.get("names", []) or []
    labels = data.get("labels", []) or []
    out = []
    for st in season_types:
        for cat in st.get("categories", []) or []:
            for evt in cat.get("events", []) or []:
                event_id = evt.get("eventId")
                stats_arr = evt.get("stats") or []
                event_meta = events.get(event_id, {})
                row = {
                    "date": event_meta.get("gameDate") or event_meta.get("date"),
                    "opponent": event_meta.get("opponent", {}).get("displayName") or event_meta.get("opponent", {}).get("abbreviation"),
                    "home_away": event_meta.get("homeAwaySymbol") or ("vs" if not event_meta.get("atVs") else "@"),
                    "result": event_meta.get("gameResult"),
                    "score": event_meta.get("score"),
                }
                # Map labels to values
                for i, lbl in enumerate(names):
                    if i < len(stats_arr):
                        row[lbl] = stats_arr[i]
                out.append(row)
    out.sort(key=lambda r: r.get("date") or "", reverse=True)
    return out[:20]


# ---------- Team statistics ----------
def get_team_stats(team: dict) -> dict:
    """Per-team season stats, grouped by category (General / Offense / Defense / etc.)."""
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/{team['sport']}/{team['league']}/teams/{team['espn_id']}/statistics"
    data = _get(url, ttl=600)
    if not data:
        return {}
    results = data.get("results", {}) or {}
    stats = results.get("stats", {}) or {}
    categories = stats.get("categories", []) or []
    out = {}
    for cat in categories:
        cname = cat.get("displayName") or cat.get("name") or "Stats"
        out[cname] = [
            {
                "name": s.get("displayName") or s.get("name"),
                "value": s.get("displayValue"),
                "rank": s.get("rank"),
                "rank_display": s.get("rankDisplayValue"),
            }
            for s in (cat.get("stats") or [])
            if s.get("displayName") or s.get("name")
        ]
    return out


# ---------- Game details / box score ----------
def get_game_summary(team: dict, event_id: str) -> dict:
    """Per-game box score, scoring plays, etc."""
    url = f"{ESPN_BASE}/{team['sport']}/{team['league']}/summary"
    data = _get(url, ttl=30, params={"event": event_id})
    return data or {}


# ---------- Helpers for UI ----------
def humanize_event_time(event: dict) -> str:
    try:
        dt = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).astimezone()
        return dt.strftime("%a %b %-d, %-I:%M %p %Z") if hasattr(dt, "strftime") else dt.isoformat()
    except Exception:
        return event.get("date", "")


def event_outcome_for_team(event: dict, team_abbr: str) -> str:
    """Returns 'W 110-102', 'L 5-3', 'in progress', 'preview', etc."""
    home, away = event.get("home"), event.get("away")
    if not home or not away:
        return event.get("status_desc", "")
    state = event.get("status_state")
    if state == "pre":
        return "vs " + (away["abbr"] if home["abbr"] == team_abbr else home["abbr"])
    is_home = home["abbr"].lower() == team_abbr.lower()
    my, opp = (home, away) if is_home else (away, home)
    try:
        my_s = int(float(my.get("score") or 0))
        opp_s = int(float(opp.get("score") or 0))
    except (TypeError, ValueError):
        my_s, opp_s = 0, 0
    if state == "in":
        return f"{my_s}-{opp_s} ({event.get('status_detail') or 'live'})"
    if event.get("completed"):
        result = "W" if my_s > opp_s else ("L" if my_s < opp_s else "T")
        return f"{result} {my_s}-{opp_s}"
    return event.get("status_desc", "")
