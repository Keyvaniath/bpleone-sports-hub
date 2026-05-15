"""
Teams Brandon follows. Single source of truth for the Sports Hub.

ESPN ids verified against site.api.espn.com on 2026-05-14:
  Lakers   NBA   id=13   abbr=LAL
  Dodgers  MLB   id=19   abbr=LAD
  Rams     NFL   id=14   abbr=LAR
  USC      NCAAF id=30   abbr=USC
  USC MBB  NCAAM id=30   abbr=USC
"""

TEAMS = [
    {
        "key": "lakers",
        "name": "Los Angeles Lakers",
        "short": "Lakers",
        "league": "nba",
        "sport": "basketball",
        "espn_id": "13",
        "espn_abbr": "lal",
        "color": "#552583",
        "accent": "#FDB927",
        "emoji": "🏀",
        "in_season_months": [10, 11, 12, 1, 2, 3, 4, 5, 6],
    },
    {
        "key": "dodgers",
        "name": "Los Angeles Dodgers",
        "short": "Dodgers",
        "league": "mlb",
        "sport": "baseball",
        "espn_id": "19",
        "espn_abbr": "lad",
        "color": "#005A9C",
        "accent": "#EF3E42",
        "emoji": "⚾",
        "in_season_months": [3, 4, 5, 6, 7, 8, 9, 10, 11],
    },
    {
        "key": "rams",
        "name": "Los Angeles Rams",
        "short": "Rams",
        "league": "nfl",
        "sport": "football",
        "espn_id": "14",
        "espn_abbr": "lar",
        "color": "#003594",
        "accent": "#FFA300",
        "emoji": "🏈",
        "in_season_months": [9, 10, 11, 12, 1, 2],
    },
    {
        "key": "usc_fb",
        "name": "USC Trojans Football",
        "short": "USC Football",
        "league": "college-football",
        "sport": "football",
        "espn_id": "30",
        "espn_abbr": "usc",
        "color": "#990000",
        "accent": "#FFC72C",
        "emoji": "🏈",
        "in_season_months": [8, 9, 10, 11, 12, 1],
    },
    {
        "key": "usc_mbb",
        "name": "USC Trojans Basketball",
        "short": "USC Basketball",
        "league": "mens-college-basketball",
        "sport": "basketball",
        "espn_id": "30",
        "espn_abbr": "usc",
        "color": "#990000",
        "accent": "#FFC72C",
        "emoji": "🏀",
        "in_season_months": [11, 12, 1, 2, 3, 4],
    },
    {
        "key": "usc_bb",
        "name": "USC Trojans Baseball",
        "short": "USC Baseball",
        "league": "college-baseball",
        "sport": "baseball",
        "espn_id": "68",
        "espn_abbr": "usc",
        "color": "#990000",
        "accent": "#FFC72C",
        "emoji": "⚾",
        "in_season_months": [2, 3, 4, 5, 6, 7],
    },
]

TEAM_BY_KEY = {t["key"]: t for t in TEAMS}


def get_team(key: str) -> dict:
    return TEAM_BY_KEY[key]


def league_path(team: dict) -> str:
    """ESPN URL path fragment, e.g. 'basketball/nba'."""
    return f"{team['sport']}/{team['league']}"
