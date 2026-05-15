# bpleone Sports Hub

Personal sports dashboard for Brandon's teams. Live at **sports.bpleone.com**.

Tracks:
- 🏀 Los Angeles Lakers (NBA)
- ⚾ Los Angeles Dodgers (MLB)
- 🏈 Los Angeles Rams (NFL)
- 🏈 USC Trojans Football (NCAAF)
- 🏀 USC Trojans Basketball (NCAAM)
- ⚾ USC Trojans Baseball (CBB)

## Views
- **Overview** — every team at a glance: last game, next game, today's status
- **Today** — your team's game today + around the league + latest news + weather for outdoor home games
- **Schedule** — full season, upcoming, past with W/L outcomes, in-game box-score expander
- **Standings** — division and conference standings, your team highlighted
- **Stats** — team season stats by category (offense/defense/general) with league ranks
- **Injuries** — current injury report, severity-coded with return dates
- **Roster** — full roster with position filter + player gamelog deep-dive
- **News** — team + league feeds with thumbnails
- **Fantasy** — Sleeper integration (enter username, browse leagues, standings)

## Data sources
- **ESPN unofficial JSON** (`site.api.espn.com`, `cdn.espn.com`, `site.web.api.espn.com`) — scores, schedules, standings, news, injuries, rosters, team stats, player gamelogs, box scores
- **Sleeper API** (`api.sleeper.app`) — fantasy leagues
- **Open-Meteo** (`api.open-meteo.com`) — weather forecasts for outdoor home games (no auth required)

No API keys required.

## Local dev
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy
```
python DEPLOY.py    # pushes to Keyvaniath/bpleone-sports-hub
```

Streamlit Community Cloud auto-rebuilds within ~60 seconds. Custom domain `sports.bpleone.com` is configured via CNAME.

## Files
- `streamlit_app.py` — main dashboard, page routing, all UI
- `data_sources.py` — ESPN API wrapper with TTL cache; covers team summary, schedule, scoreboard, roster, injuries, news, standings, team stats, player gamelog, box score
- `fantasy_sleeper.py` — Sleeper API wrapper (user lookup, leagues, rosters, matchups)
- `weather.py` — Open-Meteo wrapper for stadium-coord weather forecasts
- `teams_config.py` — team IDs and metadata (single source of truth)
- `requirements.txt` — `streamlit`, `pandas`, `requests`, `streamlit-autorefresh`
- `DEPLOY.py` / `DEPLOY.bat` — one-click push to `Keyvaniath/bpleone-sports-hub`

## Architecture notes
- Live games auto-refresh every 30 seconds via `streamlit-autorefresh`
- All ESPN calls have a TTL cache (30s for scoreboards, 5-15m for static data)
- Streamlit's `@st.cache_data` adds a second layer for cross-session sharing
- Force-refresh button in the sidebar clears all caches

## Roadmap
- [x] Player gamelog deep-dive in Roster view
- [x] Weather forecast for outdoor home games (Dodgers, Rams, USC FB/BB)
- [x] USC baseball — ESPN id 68, full season schedule
- [ ] Push notification webhook on close-game scoring (Discord)
- [ ] Historic head-to-head splits
- [ ] Schedule heat-map (busy weeks / off-nights)
- [ ] Compare two teams side-by-side
