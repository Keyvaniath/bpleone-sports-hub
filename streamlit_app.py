"""
bpleone.com Sports Hub
Personal dashboard for Brandon's teams: Lakers / Dodgers / Rams / USC.

Run:    streamlit run streamlit_app.py
Deploy: Streamlit Community Cloud -> sports.bpleone.com
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import data_sources as ds
import weather as wx
from teams_config import TEAMS, get_team

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Sports Hub — bpleone.com",
    page_icon="🏟️",
    layout="wide",
    initial_sidebar_state="expanded",
)

GOLD = "#f5c842"
BG_CARD = "#131826"
BORDER = "#232a3e"
TEXT_DIM = "#8b94a8"

st.markdown(
    f"""
    <style>
    .stApp {{ background: #0a0e1a; }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 3rem; }}
    h1, h2, h3, h4 {{ color: #e8ecf4; }}

    .team-pill {{
        display: inline-flex; align-items: center; gap: 8px;
        background: {BG_CARD}; border: 1px solid {BORDER};
        border-radius: 10px; padding: 6px 12px; margin: 2px 4px 2px 0;
        font-size: 13px; color: #cfd5e3;
    }}
    .stat-card {{
        background: {BG_CARD}; border: 1px solid {BORDER};
        border-radius: 12px; padding: 18px; height: 100%;
    }}
    .stat-card .label {{ color: {TEXT_DIM}; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat-card .value {{ color: #e8ecf4; font-size: 28px; font-weight: 700; margin-top: 6px; }}
    .stat-card .sub {{ color: {TEXT_DIM}; font-size: 12px; margin-top: 4px; }}

    .game-card {{
        background: {BG_CARD}; border: 1px solid {BORDER};
        border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
    }}
    .game-card.live {{ border-color: #f87171; box-shadow: 0 0 0 1px rgba(248,113,113,0.3); }}
    .game-card.win {{ border-left: 4px solid #4ade80; }}
    .game-card.loss {{ border-left: 4px solid #f87171; }}
    .game-card .matchup {{ font-weight: 600; font-size: 15px; color: #e8ecf4; }}
    .game-card .meta {{ color: {TEXT_DIM}; font-size: 12px; margin-top: 4px; }}
    .game-card .score {{ font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: {GOLD}; }}

    .news-item {{
        padding: 10px 0; border-bottom: 1px solid {BORDER};
    }}
    .news-item a {{ color: #e8ecf4; text-decoration: none; font-weight: 500; }}
    .news-item a:hover {{ color: {GOLD}; }}
    .news-item .byline {{ color: {TEXT_DIM}; font-size: 11px; }}

    .injury-row {{
        background: {BG_CARD}; border: 1px solid {BORDER};
        border-left: 4px solid #fb923c; border-radius: 8px;
        padding: 10px 14px; margin-bottom: 8px;
    }}

    .status-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px;
                     font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }}
    .status-live {{ background: #f87171; color: #fff; }}
    .status-final {{ background: #232a3e; color: {TEXT_DIM}; }}
    .status-soon {{ background: {GOLD}; color: #0a0e1a; }}

    [data-testid="stSidebar"] {{ background: #0d1220; border-right: 1px solid {BORDER}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# Cached data wrappers
# ----------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def cached_scoreboard(team_key: str):
    return ds.get_scoreboard(get_team(team_key))


@st.cache_data(ttl=120, show_spinner=False)
def cached_summary(team_key: str):
    return ds.get_team_summary(get_team(team_key))


@st.cache_data(ttl=120, show_spinner=False)
def cached_schedule(team_key: str):
    return ds.get_schedule(get_team(team_key))


@st.cache_data(ttl=300, show_spinner=False)
def cached_news_team(team_key: str, limit: int = 12):
    return ds.get_team_news(get_team(team_key), limit=limit)


@st.cache_data(ttl=300, show_spinner=False)
def cached_news_league(team_key: str, limit: int = 12):
    return ds.get_league_news(get_team(team_key), limit=limit)


@st.cache_data(ttl=600, show_spinner=False)
def cached_standings(team_key: str):
    return ds.get_standings(get_team(team_key))


@st.cache_data(ttl=600, show_spinner=False)
def cached_roster(team_key: str):
    return ds.get_roster(get_team(team_key))


@st.cache_data(ttl=300, show_spinner=False)
def cached_injuries(team_key: str):
    return ds.get_injuries(get_team(team_key))


@st.cache_data(ttl=600, show_spinner=False)
def cached_team_stats(team_key: str):
    return ds.get_team_stats(get_team(team_key))


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏟️ Sports Hub")
    st.caption("Brandon's personal team dashboard")

    team_labels = {t["key"]: f"{t['emoji']} {t['short']}" for t in TEAMS}
    team_options = ["__all__"] + [t["key"] for t in TEAMS]
    selected_key = st.radio(
        "Team",
        options=team_options,
        format_func=lambda k: "🏟️ All Teams" if k == "__all__" else team_labels[k],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    if selected_key == "__all__":
        view = "🏟️ Overview"
    else:
        view = st.radio(
            "View",
            ["🏠 Today", "📅 Schedule", "📊 Standings", "📈 Stats", "🩹 Injuries", "👥 Roster", "📰 News", "🎮 Fantasy"],
            index=0,
            label_visibility="collapsed",
        )

    st.markdown("---")
    st.caption("Data: ESPN • Sleeper")
    if st.button("🔄 Force refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Last loaded: {datetime.now().strftime('%I:%M:%S %p')}")


team = None if selected_key == "__all__" else get_team(selected_key)
summary = None if selected_key == "__all__" else cached_summary(selected_key)


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
if team is not None:
    header_cols = st.columns([1, 6, 3])
    with header_cols[0]:
        if summary.get("logo"):
            st.image(summary["logo"], width=80)
        else:
            st.markdown(f"<div style='font-size:64px'>{team['emoji']}</div>", unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown(f"### {summary.get('name', team['name'])}")
        record_line = summary.get("record") or "—"
        if summary.get("standing"):
            record_line = f"{record_line} • {summary['standing']}"
        st.caption(record_line)
    with header_cols[2]:
        sb = cached_scoreboard(selected_key)
        my_game = next(
            (g for g in sb if g.get("home", {}).get("abbr", "").lower() == team["espn_abbr"].lower()
             or g.get("away", {}).get("abbr", "").lower() == team["espn_abbr"].lower()),
            None,
        )
        if my_game:
            state = my_game.get("status_state")
            badge = "LIVE" if state == "in" else ("FINAL" if my_game.get("completed") else "TODAY")
            cls = "status-live" if state == "in" else ("status-final" if my_game.get("completed") else "status-soon")
            st.markdown(f"<span class='status-badge {cls}'>{badge}</span> "
                        f"<span style='color:#e8ecf4'>{ds.event_outcome_for_team(my_game, team['espn_abbr'].upper())}</span>",
                        unsafe_allow_html=True)
            st.caption(my_game.get("short_name") or my_game.get("name"))
    st.markdown("---")
else:
    st.markdown("## 🏟️ All Teams")
    st.caption("Cross-team overview — picks up live games, latest results, and next-up matchups.")
    st.markdown("---")


# ----------------------------------------------------------------------
# Page renderers
# ----------------------------------------------------------------------
def fmt_dt(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%a %b %d • %I:%M %p")
    except Exception:
        return iso or ""


def render_game_card(g: dict, team_abbr: str, *, is_completed_view: bool = False, expander_key: str | None = None):
    home = g.get("home") or {}
    away = g.get("away") or {}
    state = g.get("status_state")
    is_live = state == "in"
    outcome_label = ds.event_outcome_for_team(g, team_abbr)
    extra_class = "live" if is_live else ("win" if outcome_label.startswith("W ") else ("loss" if outcome_label.startswith("L ") else ""))
    score_str = ""
    if state in ("in", "post") or g.get("completed"):
        score_str = f"{away.get('abbr','?')} {away.get('score','?')} @ {home.get('abbr','?')} {home.get('score','?')}"
    meta_parts = [fmt_dt(g.get("date", ""))]
    if g.get("venue"): meta_parts.append(g["venue"])
    if g.get("broadcasts"): meta_parts.append("📺 " + ", ".join(g["broadcasts"]))
    if is_live and g.get("status_detail"): meta_parts.append(f"⏱ {g['status_detail']}")
    if not score_str and state == "pre":
        outcome_label = f"{away.get('abbr','?')} @ {home.get('abbr','?')}"
    # Weather for outdoor games starting within 7 days
    if state == "pre" and g.get("is_home_game") and wx.is_outdoor(g.get("venue")):
        forecast = wx.get_forecast_for_event(g.get("venue"), g.get("date"))
        if forecast and forecast.get("temp_f") is not None:
            wx_str = f"☁ {round(forecast['temp_f'])}°F · {forecast.get('summary','')}"
            if forecast.get("wind_mph") is not None:
                wx_str += f" · 💨{round(forecast['wind_mph'])}mph"
            if forecast.get("precip_pct") is not None and forecast["precip_pct"] > 10:
                wx_str += f" · 🌧 {forecast['precip_pct']}%"
            meta_parts.append(wx_str)

    st.markdown(
        f"""
        <div class='game-card {extra_class}'>
          <div style='display:flex; justify-content:space-between; align-items:center; gap:12px;'>
            <div>
              <div class='matchup'>{g.get('name','')}</div>
              <div class='meta'>{' • '.join(meta_parts)}</div>
            </div>
            <div class='score'>{score_str or outcome_label}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Optional detail expander
    if expander_key and g.get("id") and (is_live or g.get("completed")):
        with st.expander("Box score & details", expanded=False):
            try:
                summary_data = ds.get_game_summary(team, g["id"])
                _render_game_detail(summary_data, team_abbr)
            except Exception as e:
                st.caption(f"Couldn't load details: {e}")


def _render_game_detail(summary_data: dict, team_abbr: str):
    if not summary_data:
        st.caption("No detail available.")
        return
    header = summary_data.get("header") or {}
    competitions = header.get("competitions") or [{}]
    comp = competitions[0]
    season = (header.get("season") or {}).get("year")
    week = comp.get("week")
    if season or week:
        st.caption(f"Season {season or '?'}{' • Week ' + str(week) if week else ''}")

    boxscore = summary_data.get("boxscore") or {}
    teams = boxscore.get("teams") or []
    if teams:
        cols = st.columns(len(teams))
        for c, tm in zip(cols, teams):
            tinfo = tm.get("team", {})
            with c:
                st.markdown(f"**{tinfo.get('displayName','?')}** ({tm.get('homeAway','?')})")
                stats = tm.get("statistics") or []
                rows = [(s.get("label") or s.get("name"), s.get("displayValue")) for s in stats if s.get("label") or s.get("name")]
                if rows:
                    df = pd.DataFrame(rows, columns=["Stat", "Value"])
                    st.dataframe(df, use_container_width=True, hide_index=True)

    # Leaders (most leagues)
    leaders = summary_data.get("leaders") or header.get("competitions", [{}])[0].get("leaders") or []
    if leaders:
        st.markdown("##### Leaders")
        for ld in leaders:
            team_name = (ld.get("team") or {}).get("displayName")
            for cat in ld.get("leaders") or []:
                cat_name = cat.get("displayName")
                top = (cat.get("leaders") or [{}])[0]
                ath = (top.get("athlete") or {}).get("displayName")
                val = top.get("displayValue")
                if ath and val:
                    st.markdown(f"- **{cat_name}** ({team_name}) — {ath}: {val}")

    # Scoring plays (where available — football/basketball)
    plays = summary_data.get("scoringPlays") or []
    if plays:
        st.markdown("##### Scoring Plays")
        for p in plays[-12:]:
            qtr = (p.get("period") or {}).get("displayValue") or ""
            clock = p.get("clock", {}).get("displayValue", "")
            text = p.get("text") or ""
            score_text = ""
            ascore = p.get("awayScore")
            hscore = p.get("homeScore")
            if ascore is not None and hscore is not None:
                score_text = f" ({ascore}-{hscore})"
            st.caption(f"{qtr} {clock} — {text}{score_text}")


def page_today():
    st.subheader("Today")
    sb = cached_scoreboard(selected_key)
    team_abbr_u = team["espn_abbr"].upper()
    my_games = [g for g in sb if g.get("home", {}).get("abbr", "").upper() == team_abbr_u
                or g.get("away", {}).get("abbr", "").upper() == team_abbr_u]

    cols = st.columns(4)
    sched = cached_schedule(selected_key)
    buckets = ds.split_schedule(sched)
    last_game = buckets["past"][0] if buckets["past"] else None
    next_game = buckets["upcoming"][0] if buckets["upcoming"] else None

    with cols[0]:
        st.markdown(
            f"<div class='stat-card'><div class='label'>Record</div>"
            f"<div class='value'>{summary.get('record','—')}</div>"
            f"<div class='sub'>{summary.get('standing') or ''}</div></div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        last_str = "—"
        last_meta = ""
        if last_game:
            last_str = ds.event_outcome_for_team(last_game, team_abbr_u)
            last_meta = fmt_dt(last_game.get("date", ""))
        st.markdown(
            f"<div class='stat-card'><div class='label'>Last Game</div>"
            f"<div class='value'>{last_str}</div>"
            f"<div class='sub'>{last_meta}</div></div>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        next_str = "—"
        next_meta = ""
        if next_game:
            opp = (next_game.get("away") if next_game.get("is_home_game") else next_game.get("home")) or {}
            next_str = ("vs " if next_game.get("is_home_game") else "@ ") + (opp.get("abbr") or "?")
            next_meta = fmt_dt(next_game.get("date", ""))
        st.markdown(
            f"<div class='stat-card'><div class='label'>Next Game</div>"
            f"<div class='value'>{next_str}</div>"
            f"<div class='sub'>{next_meta}</div></div>",
            unsafe_allow_html=True,
        )
    with cols[3]:
        season_games = len(buckets["past"]) + len(buckets["live"]) + len(buckets["upcoming"])
        played = len(buckets["past"]) + len(buckets["live"])
        st.markdown(
            f"<div class='stat-card'><div class='label'>Games Played</div>"
            f"<div class='value'>{played}<span style='color:{TEXT_DIM}; font-size:18px'> / {season_games}</span></div>"
            f"<div class='sub'>{season_games - played} remaining</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### My Game Today")
    if my_games:
        for idx, g in enumerate(my_games):
            render_game_card(g, team_abbr_u, expander_key=f"today_my_{idx}")
            # Auto-refresh while live
            if g.get("status_state") == "in":
                try:
                    import streamlit_autorefresh as sar
                    sar.st_autorefresh(interval=30 * 1000, key=f"live_my_{idx}")
                except Exception:
                    pass
    else:
        st.info(f"No {team['short']} game today.")

    st.markdown("#### Around the League")
    league_today = [g for g in sb if g not in my_games]
    if league_today:
        for idx, g in enumerate(league_today[:8]):
            render_game_card(g, team_abbr_u)
    else:
        st.caption("No other league games today.")

    st.markdown("#### Latest News")
    news = cached_news_team(selected_key, limit=6)
    if not news:
        news = cached_news_league(selected_key, limit=6)
    for n in news[:6]:
        url = n.get("url") or "#"
        pub = n.get("published", "")[:10]
        st.markdown(
            f"<div class='news-item'><a href='{url}' target='_blank'>{n['headline']}</a>"
            f"<div class='byline'>{n.get('byline') or n.get('type','')} • {pub}</div></div>",
            unsafe_allow_html=True,
        )


def page_schedule():
    st.subheader("Schedule")
    sched = cached_schedule(selected_key)
    if not sched:
        st.warning("No schedule available (offseason?).")
        return
    buckets = ds.split_schedule(sched)
    team_abbr_u = team["espn_abbr"].upper()

    tab_up, tab_past, tab_all = st.tabs([
        f"Upcoming ({len(buckets['upcoming'])})",
        f"Past ({len(buckets['past'])})",
        f"Full Season ({len(sched)})",
    ])

    with tab_up:
        if buckets["live"]:
            st.markdown("##### 🔴 Live now")
            for idx, g in enumerate(buckets["live"]):
                render_game_card(g, team_abbr_u, expander_key=f"sched_live_{idx}")
            try:
                import streamlit_autorefresh as sar
                sar.st_autorefresh(interval=30 * 1000, key="sched_live_refresh")
            except Exception:
                pass
        if buckets["upcoming"]:
            for idx, g in enumerate(buckets["upcoming"][:20]):
                render_game_card(g, team_abbr_u)
        else:
            st.caption("No upcoming games.")

    with tab_past:
        wins = sum(1 for g in buckets["past"] if ds.event_outcome_for_team(g, team_abbr_u).startswith("W "))
        losses = sum(1 for g in buckets["past"] if ds.event_outcome_for_team(g, team_abbr_u).startswith("L "))
        st.caption(f"{wins} W · {losses} L from {len(buckets['past'])} games shown")
        for idx, g in enumerate(buckets["past"][:30]):
            render_game_card(g, team_abbr_u, expander_key=f"sched_past_{idx}")

    with tab_all:
        # Pandas table for full-season scan
        rows = []
        for g in sched:
            home = g.get("home") or {}
            away = g.get("away") or {}
            opp = home if not g.get("is_home_game") else away
            rows.append({
                "Date": fmt_dt(g.get("date", "")),
                "Home/Away": "Home" if g.get("is_home_game") else "Away",
                "Opponent": opp.get("name", "?"),
                "Status": g.get("status_desc") or "",
                "Result": ds.event_outcome_for_team(g, team_abbr_u),
                "TV": ", ".join(g.get("broadcasts") or []),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_standings():
    st.subheader("Standings")
    st_data = cached_standings(selected_key)
    if not st_data:
        st.warning("Standings unavailable for this league right now.")
        return
    for grp_name, entries in st_data.items():
        st.markdown(f"##### {grp_name}")
        rows = []
        for e in entries:
            rows.append({
                "★": "★" if e.get("is_user_team") else "",
                "Team": e.get("team"),
                "W": e.get("wins"),
                "L": e.get("losses"),
                **({"T": e.get("ties")} if e.get("ties") not in (None, "0", 0) else {}),
                "PCT": e.get("win_pct"),
                "GB": e.get("games_behind"),
                "Streak": e.get("streak"),
                "Home": e.get("home"),
                "Road": e.get("road"),
                "Div": e.get("div"),
                "Conf": e.get("conf"),
                "Diff": e.get("diff"),
            })
        df = pd.DataFrame(rows)
        df = df.dropna(axis=1, how="all")
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_injuries():
    st.subheader("Injury Report")
    injuries = cached_injuries(selected_key)
    if not injuries:
        st.success("No injuries reported. 🟢")
        return
    sev_order = {"Out": 0, "Doubtful": 1, "Questionable": 2, "Probable": 3, "Day-To-Day": 4}
    injuries.sort(key=lambda x: sev_order.get(x.get("status") or "", 99))
    for inj in injuries:
        status = inj.get("status") or "Unknown"
        color = {"Out": "#f87171", "Doubtful": "#fb923c", "Questionable": "#fbbf24",
                 "Probable": "#4ade80", "Day-To-Day": "#fbbf24"}.get(status, "#8b94a8")
        type_str = inj.get("type") or ""
        detail = inj.get("short_comment") or inj.get("detail") or ""
        retdate = inj.get("return_date") or ""
        if retdate:
            try:
                retdate = "Return: " + datetime.fromisoformat(retdate.replace("Z", "+00:00")).strftime("%b %d, %Y")
            except Exception:
                pass
        st.markdown(
            f"""
            <div class='injury-row' style='border-left-color:{color}'>
              <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                  <strong style='color:#e8ecf4'>{inj.get('name','?')}</strong>
                  <span style='color:{TEXT_DIM}; margin-left:8px;'>{inj.get('position') or ''}</span>
                </div>
                <span style='color:{color}; font-weight:700; font-size:12px;'>{status.upper()}</span>
              </div>
              <div style='color:{TEXT_DIM}; font-size:13px; margin-top:6px;'>{type_str} {('• ' + detail) if detail else ''}</div>
              {('<div style=\"color:' + TEXT_DIM + '; font-size:11px; margin-top:4px;\">' + retdate + '</div>') if retdate else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_roster():
    st.subheader("Roster")
    roster = cached_roster(selected_key)
    if not roster:
        st.warning("Roster unavailable.")
        return

    # Group filter
    groups = sorted({a.get("position_group") for a in roster if a.get("position_group")})
    if groups:
        chosen = st.multiselect("Position group", groups, default=groups)
        roster = [a for a in roster if a.get("position_group") in chosen] if chosen else roster

    rows = []
    for a in roster:
        rows.append({
            "#": a.get("jersey"),
            "Name": a.get("name"),
            "Pos": a.get("position"),
            "Age": a.get("age"),
            "Ht": a.get("height"),
            "Wt": a.get("weight"),
            "Exp": a.get("experience"),
            "Status": a.get("status"),
            "Injury": a.get("injury_status"),
        })
    df = pd.DataFrame(rows)
    df = df.dropna(axis=1, how="all")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Player deep-dive
    st.markdown("##### Player deep-dive")
    player_options = {f"{a.get('name','?')} ({a.get('position') or '?'})": a.get("id")
                      for a in roster if a.get("id")}
    if not player_options:
        return
    pick = st.selectbox("Pick a player", options=["—"] + list(player_options.keys()))
    if pick and pick != "—":
        athlete_id = player_options[pick]
        try:
            logs = ds.get_player_gamelog(team, str(athlete_id))
        except Exception as e:
            st.caption(f"Couldn't load gamelog: {e}")
            return
        if not logs:
            st.caption("No game log available for this player.")
            return
        st.caption(f"Last {len(logs)} games — {pick}")
        log_df = pd.DataFrame(logs)
        log_df = log_df.dropna(axis=1, how="all")
        st.dataframe(log_df, use_container_width=True, hide_index=True)


def page_stats():
    st.subheader("Team Stats")
    stats = cached_team_stats(selected_key)
    if not stats:
        st.warning("Stats not available for this team / league right now.")
        return
    for cat_name, items in stats.items():
        st.markdown(f"##### {cat_name}")
        # Display in a clean grid
        cols = st.columns(3)
        for i, s in enumerate(items):
            with cols[i % 3]:
                rank = s.get("rank_display") or (f"#{s['rank']}" if s.get("rank") else "")
                rank_html = f"<span style='color:{TEXT_DIM}; font-size:11px; margin-left:6px'>{rank}</span>" if rank else ""
                st.markdown(
                    f"<div class='stat-card' style='margin-bottom:8px; padding:12px 16px'>"
                    f"<div class='label'>{s.get('name','?')}</div>"
                    f"<div class='value' style='font-size:22px'>{s.get('value','—')}{rank_html}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


def page_news():
    st.subheader("News")
    tab_team, tab_league = st.tabs([f"{team['short']} News", "League News"])
    with tab_team:
        news = cached_news_team(selected_key, limit=20)
        if not news:
            st.caption("No team-specific articles right now.")
        for n in news:
            url = n.get("url") or "#"
            pub = (n.get("published") or "")[:10]
            cols = st.columns([1, 5])
            with cols[0]:
                if n.get("image"):
                    st.image(n["image"], use_container_width=True)
            with cols[1]:
                st.markdown(f"**[{n['headline']}]({url})**")
                if n.get("description"):
                    st.caption(n["description"][:200])
                st.caption(f"{n.get('byline') or n.get('type','')} • {pub}")
            st.markdown("---")
    with tab_league:
        news = cached_news_league(selected_key, limit=20)
        for n in news:
            url = n.get("url") or "#"
            pub = (n.get("published") or "")[:10]
            cols = st.columns([1, 5])
            with cols[0]:
                if n.get("image"):
                    st.image(n["image"], use_container_width=True)
            with cols[1]:
                st.markdown(f"**[{n['headline']}]({url})**")
                if n.get("description"):
                    st.caption(n["description"][:200])
                st.caption(f"{n.get('byline') or n.get('type','')} • {pub}")
            st.markdown("---")


def page_fantasy():
    st.subheader("Fantasy")
    st.caption("Sleeper integration — add your username below to pull all your leagues.")
    import fantasy_sleeper as fs

    username = st.text_input(
        "Sleeper username",
        value=st.session_state.get("sleeper_username", ""),
        placeholder="brandonpleone",
    )
    if username:
        st.session_state["sleeper_username"] = username
        user = fs.get_user(username)
        if not user:
            st.error(f"Couldn't find Sleeper user '{username}'. Check spelling.")
            return
        st.success(f"Connected as {user.get('display_name') or username}")
        season = st.selectbox("Season", ["2026", "2025", "2024"], index=0)
        sport_pick = st.selectbox("Sport", ["nfl", "nba"], index=0)
        leagues = fs.get_user_leagues(user["user_id"], sport_pick, season)
        if not leagues:
            st.info(f"No {sport_pick.upper()} leagues found for {season}.")
            return
        league_pick = st.selectbox(
            "League",
            options=[lg["league_id"] for lg in leagues],
            format_func=lambda lid: next((lg["name"] for lg in leagues if lg["league_id"] == lid), lid),
        )
        # Render league
        rosters = fs.get_league_rosters(league_pick)
        users = {u["user_id"]: u for u in fs.get_league_users(league_pick)}
        rows = []
        my_user_id = user["user_id"]
        for r in rosters:
            settings = r.get("settings", {})
            owner = users.get(r.get("owner_id"), {})
            display = owner.get("display_name") or owner.get("username") or "—"
            wins = settings.get("wins", 0)
            losses = settings.get("losses", 0)
            ties = settings.get("ties", 0)
            pts_for = (settings.get("fpts", 0) or 0) + (settings.get("fpts_decimal", 0) or 0) / 100.0
            pts_against = (settings.get("fpts_against", 0) or 0) + (settings.get("fpts_against_decimal", 0) or 0) / 100.0
            rows.append({
                "★": "★" if r.get("owner_id") == my_user_id else "",
                "Team": display,
                "W": wins, "L": losses, "T": ties,
                "PF": round(pts_for, 2),
                "PA": round(pts_against, 2),
            })
        rows.sort(key=lambda x: (-x["W"], x["L"], -x["PF"]))
        df = pd.DataFrame(rows)
        st.markdown("##### Standings")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Enter your Sleeper username to link your leagues. "
                "Don't have one? Sleeper is free — [sleeper.com](https://sleeper.com).")


def page_overview():
    """All-teams glance: 1 row per team."""
    any_live = False
    for t in TEAMS:
        s = cached_summary(t["key"])
        sched = cached_schedule(t["key"])
        buckets = ds.split_schedule(sched)
        sb = cached_scoreboard(t["key"])
        team_abbr_u = t["espn_abbr"].upper()
        my_today = next(
            (g for g in sb if g.get("home", {}).get("abbr", "").upper() == team_abbr_u
             or g.get("away", {}).get("abbr", "").upper() == team_abbr_u),
            None,
        )

        with st.container():
            cols = st.columns([1, 3, 3, 3, 3])
            with cols[0]:
                if s.get("logo"):
                    st.image(s["logo"], width=72)
                else:
                    st.markdown(f"<div style='font-size:48px'>{t['emoji']}</div>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"**{s.get('name', t['name'])}**")
                st.caption(s.get("record") or s.get("standing") or "Offseason")
            with cols[2]:
                last = buckets["past"][0] if buckets["past"] else None
                if last:
                    st.markdown(f"<div class='label' style='color:{TEXT_DIM};font-size:11px;text-transform:uppercase;'>Last</div>"
                                f"<div style='color:#e8ecf4;font-weight:600'>{ds.event_outcome_for_team(last, team_abbr_u)}</div>"
                                f"<div style='color:{TEXT_DIM};font-size:11px'>{fmt_dt(last.get('date',''))}</div>",
                                unsafe_allow_html=True)
                else:
                    st.caption("No recent games")
            with cols[3]:
                nxt = buckets["upcoming"][0] if buckets["upcoming"] else None
                if nxt:
                    opp = (nxt.get("away") if nxt.get("is_home_game") else nxt.get("home")) or {}
                    label = ("vs " if nxt.get("is_home_game") else "@ ") + (opp.get("abbr") or "?")
                    st.markdown(f"<div class='label' style='color:{TEXT_DIM};font-size:11px;text-transform:uppercase;'>Next</div>"
                                f"<div style='color:#e8ecf4;font-weight:600'>{label}</div>"
                                f"<div style='color:{TEXT_DIM};font-size:11px'>{fmt_dt(nxt.get('date',''))}</div>"
                                f"<div style='color:{TEXT_DIM};font-size:11px'>{(', '.join(nxt.get('broadcasts') or []) or '')}</div>",
                                unsafe_allow_html=True)
                else:
                    st.caption("No games scheduled")
            with cols[4]:
                if my_today:
                    state = my_today.get("status_state")
                    if state == "in":
                        any_live = True
                        st.markdown(
                            f"<span class='status-badge status-live'>LIVE</span> "
                            f"<span style='color:#e8ecf4;font-weight:600'>{ds.event_outcome_for_team(my_today, team_abbr_u)}</span>",
                            unsafe_allow_html=True,
                        )
                    elif my_today.get("completed"):
                        st.markdown(
                            f"<span class='status-badge status-final'>FINAL</span> "
                            f"<span style='color:#e8ecf4'>{ds.event_outcome_for_team(my_today, team_abbr_u)}</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<span class='status-badge status-soon'>TODAY</span> "
                            f"<span style='color:#e8ecf4'>{ds.event_outcome_for_team(my_today, team_abbr_u)}</span>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No game today")
        st.markdown("---")

    if any_live:
        st.info("🔴 Live games — page auto-refreshes every 30 seconds.")
        try:
            import streamlit_autorefresh as sar
            sar.st_autorefresh(interval=30 * 1000, key="overview_live")
        except Exception:
            pass

    # League-wide breaking news strip
    st.markdown("#### Today's Sports News")
    all_news = []
    for t in TEAMS:
        try:
            all_news.extend(cached_news_team(t["key"], limit=3))
        except Exception:
            pass
    seen = set()
    deduped = []
    for n in all_news:
        h = n.get("headline")
        if h and h not in seen:
            seen.add(h)
            deduped.append(n)
    deduped.sort(key=lambda n: n.get("published") or "", reverse=True)
    for n in deduped[:8]:
        url = n.get("url") or "#"
        pub = (n.get("published") or "")[:10]
        st.markdown(
            f"<div class='news-item'><a href='{url}' target='_blank'>{n['headline']}</a>"
            f"<div class='byline'>{n.get('byline') or n.get('type','')} • {pub}</div></div>",
            unsafe_allow_html=True,
        )


# Router
if selected_key == "__all__":
    page_overview()
elif view.startswith("🏠"):
    page_today()
elif view.startswith("📅"):
    page_schedule()
elif view.startswith("📊"):
    page_standings()
elif view.startswith("📈"):
    page_stats()
elif view.startswith("🩹"):
    page_injuries()
elif view.startswith("👥"):
    page_roster()
elif view.startswith("📰"):
    page_news()
elif view.startswith("🎮"):
    page_fantasy()


# Footer
st.markdown("---")
st.caption(
    f"Data: ESPN unofficial JSON + Sleeper public API • "
    f"bpleone.com/sports • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
)
