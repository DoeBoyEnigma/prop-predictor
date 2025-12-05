import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

BASE_URL = "https://api.balldontlie.io/v1"

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="NBA Stats Tool", page_icon="🏀", layout="wide")

st.title("🏀 NBA Stats & Research Tool")
st.caption("Uses the FREE Balldontlie API — with optional API key support")

st.divider()

# ---------------------------
# SIDEBAR — OPTIONAL API KEY
# ---------------------------
st.sidebar.header("API Settings")

api_key = st.sidebar.text_input("Balldontlie API Key (optional)", type="password")

headers = {"Authorization": api_key} if api_key else {}


# ---------------------------
# SAFE API REQUEST WRAPPER
# ---------------------------
def safe_get(url):
    """Safely request JSON without crashing."""
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except:
            return None
    except:
        return None


# ---------------------------
# API FUNCTIONS
# ---------------------------
def get_today_games():
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/games?dates[]={today}&per_page=100"
    data = safe_get(url)
    return data.get("data", []) if data else None

def get_yesterday_games():
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/games?dates[]={yesterday}&per_page=100"
    data = safe_get(url)
    return data.get("data", []) if data else None

def search_player(name):
    url = f"{BASE_URL}/players?search={name}&per_page=50"
    data = safe_get(url)
    return data.get("data", []) if data else None

def get_player_season_averages(pid, season=2024):
    url = f"{BASE_URL}/season_averages?season={season}&player_ids[]={pid}"
    data = safe_get(url)
    stats = data.get("data", []) if data else None
    return stats[0] if stats else None


# ---------------------------
# TODAY'S GAMES SECTION
# ---------------------------
st.subheader("📅 Today's Games")

today_games = get_today_games()

if today_games is None:
    st.error("Unable to load today's games. The API may require a key or is unavailable.")
elif today_games == []:
    st.info("No NBA games today.")
else:
    for g in today_games:
        st.write(
            f"**{g['visitor_team']['full_name']} @ {g['home_team']['full_name']}**  "
            f" — Status: {g['status']}"
        )


# ---------------------------
# YESTERDAY'S SCORES SECTION
# ---------------------------
st.subheader("🕒 Yesterday's Results")

y_games = get_yesterday_games()

if y_games is None:
    st.error("Unable to load yesterday's games. The API may require a key or is unavailable.")
elif y_games == []:
    st.info("No NBA games yesterday.")
else:
    for g in y_games:
        st.write(
            f"**{g['visitor_team']['full_name']} @ {g['home_team']['full_name']}**  \n"
            f"{g['visitor_team']['abbreviation']}: {g['visitor_team_score']}  —  "
            f"{g['home_team']['abbreviation']}: {g['home_team_score']}"
        )


st.divider()

# ---------------------------
# PLAYER SEARCH SECTION
# ---------------------------
st.subheader("🔍 Search Player — Season Averages")

player_name = st.text_input("Player name (ex: Curry, LeBron, Tatum)")

if player_name:
    players = search_player(player_name)

    if players is None:
        st.error("Unable to search players. API unreachable or key required.")
    elif players == []:
        st.warning("No matching players found.")
    else:
        player = players[0]

        fullname = f"{player['first_name']} {player['last_name']}"
        team = player["team"]["full_name"]

        st.success(f"Found: **{fullname}** — {team}")

        stats = get_player_season_averages(player["id"])

        if not stats:
            st.warning("No season averages available.")
        else:
            # Clean Metrics UI
            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric("PPG", round(stats.get("pts", 0), 1))
                st.metric("RPG", round(stats.get("reb", 0), 1))
                st.metric("APG", round(stats.get("ast", 0), 1))

            with c2:
                st.metric("FG%", f"{round(stats.get('fg_pct', 0) * 100, 1)}%")
                st.metric("3P%", f"{round(stats.get('fg3_pct', 0) * 100, 1)}%")
                st.metric("FT%", f"{round(stats.get('ft_pct', 0) * 100, 1)}%")

            with c3:
                st.metric("STL", stats.get("stl", 0))
                st.metric("BLK", stats.get("blk", 0))
                st.metric("TOV", stats.get("turnover", 0))

