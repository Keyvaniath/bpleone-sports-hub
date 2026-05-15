# bpleone Sports Hub

Personal team dashboard for Brandon's teams. Lakers, Dodgers, Rams, USC FB/BB/Baseball. Live scores, schedule, injuries, news, fantasy. Pure consumption, no trading.

**Live at** [bpleone.com/sports/](https://bpleone.com/sports/) and [keyvaniath.github.io/bpleone-sports-hub/](https://keyvaniath.github.io/bpleone-sports-hub/) (fallback)

## Teams (6)

| Team | Sport | League |
|---|---|---|
| 🏀 Los Angeles Lakers | Basketball | NBA |
| ⚾ Los Angeles Dodgers | Baseball | MLB |
| 🏈 Los Angeles Rams | Football | NFL |
| 🏈 USC Trojans Football | Football | NCAAF (Big Ten) |
| 🏀 USC Trojans Basketball | Basketball | NCAAM |
| ⚾ USC Trojans Baseball | Baseball | CBB (Big Ten) |

## Static landing pages (no auth, no installs, works in any browser)

| URL | What |
|---|---|
| [/sports/](https://bpleone.com/sports/) | All-teams overview with live ESPN snapshot |
| [/sports/live/](https://bpleone.com/sports/live/) | **Live games right now** — 20s auto-refresh when in-progress |
| [/sports/lakers/](https://bpleone.com/sports/lakers/) | Lakers deep dive: record + last/next/schedule + news |
| [/sports/dodgers/](https://bpleone.com/sports/dodgers/) | Dodgers deep dive |
| [/sports/rams/](https://bpleone.com/sports/rams/) | Rams deep dive |
| [/sports/usc-football/](https://bpleone.com/sports/usc-football/) | USC Football deep dive |
| [/sports/usc-basketball/](https://bpleone.com/sports/usc-basketball/) | USC Basketball deep dive |
| [/sports/usc-baseball/](https://bpleone.com/sports/usc-baseball/) | USC Baseball deep dive |

Every page fetches live from ESPN's CORS-open JSON, no API key needed.

## Streamlit dashboard

Beyond the static landings, the Streamlit app provides 9 views per team:

| View | What |
|---|---|
| 🏠 Today | Record, last game, next game, scoreboard, news |
| 📅 Schedule | Upcoming + past with W/L outcomes, weather for outdoor home games |
| 📊 Standings | Division/conf, your team highlighted |
| 📈 Stats | Team season stats by category (offense/defense/general) |
| 🩹 Injuries | Severity-coded with return dates |
| 👥 Roster | Position filter + player gamelog deep-dive |
| 📰 News | Team + league feeds with thumbnails |
| 🎮 Fantasy | Sleeper integration (NFL + NBA leagues) |
| 🏟️ All Teams | Cross-team glance with auto-refresh on live games |

## Data sources

- **ESPN unofficial JSON** (`site.api.espn.com`, `cdn.espn.com`, `site.web.api.espn.com`) — scores, schedules, standings, news, injuries, rosters, team stats, player gamelogs, box scores. CORS open.
- **Sleeper API** (`api.sleeper.app`) — fantasy league lookup by username.
- **Open-Meteo** (`api.open-meteo.com`) — free weather forecasts for outdoor home games.

**No API keys required.** Everything runs on free tiers.

## Local dev

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy

```
python DEPLOY.py
```

Pushes to `Keyvaniath/bpleone-sports-hub`. Connect to Streamlit Cloud for the dashboard; static landings serve from GitHub Pages.

## Files

```
streamlit_app.py     ─ 9-view Streamlit dashboard per team + all-teams overview
data_sources.py      ─ ESPN API wrapper with TTL cache
fantasy_sleeper.py   ─ Sleeper API wrapper
teams_config.py      ─ team IDs + metadata (single source of truth)
weather.py           ─ Open-Meteo forecasts for outdoor home games
requirements.txt     ─ streamlit, pandas, requests, streamlit-autorefresh
DEPLOY.py / .bat     ─ one-click push to repo
docs/                ─ static GH Pages content
  index.html            main landing with live snapshot
  live/index.html       live-games-only page
  lakers/index.html     per-team deep dive
  dodgers/...
  rams/...
  usc-football/...
  usc-basketball/...
  usc-baseball/...
  team-template.html    template for per-team pages
```

## Roadmap

- [ ] Streamlit Community Cloud deploy at sports.bpleone.com (needs DNS CNAME at Squarespace)
- [ ] Push notifications when Lakers/Dodgers/Rams score
- [ ] Schedule heatmap (busy weeks / off-nights)
- [ ] Compare two teams side-by-side
- [ ] Historic head-to-head splits

## Disclaimer

Pure consumption. No trading, no betting, no edge claims. Just personal Sunday afternoon team-tracking.
