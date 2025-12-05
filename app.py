import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

BASE_URL = "https://api.balldontlie.io/v1"

# ---------------------------
# SAFE REQUEST WRAPPER
# ---------------------------

def safe_get(url):
    """Safely request JSON without crashing."""
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return r.json()
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

def get_player_season_averages(player_id, season=2025):
    url = f"{BASE_URL}/season_averages?season={season}&player_ids[]={player_id}"
    data = safe_get(url)
    stats = data.get("data", []) if data else None
    return stats[0] if stats else None


# ---------------------------
# PAGE CONFIG & STYLING
# ---------------------------

st.set_page_config(
    page_title="NBA Stats Tool",
    page_icon="🏀",
    layout="wide"
)

st.markdown("""
    <style>
        .big-title { font-size: 36px; font-weight: 700; text-align:center; margin-bottom: 5px; }
        .sub-title { text-align:center; color: #888; margin-bottom: 30px; }
        .section-header { font-size: 24px; margin-top: 30px; font-weight:600; }
        .game-box { 
            padding: 12px 18px; 
            border-radius: 12px; 
            background: #1f1f1f; 
            margin-bottom: 10px; 
            border: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)


# ---------------------------
# HEADER
# ---------------------------

st.markdown("<div class='big-title'>🏀 NBA Stats & Research Tool</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Live games • Yesterday's scores • Free public API • Season averages</div>", unsafe_allow_html=True)


# ---------------------------
# TODAY'S GAMES
# ---------------------------

st.markdown("<div class='section-header'>📅 Today's Games</div>", unsafe_allow_html=True)

today_games = get_today_games()

if today_games is None:
    st.error("API Error: Could not load today's games.")
elif today_games == []:
    st.info("No NBA games today.")
else:
    for g in today_games:
        st.markdown(f"""
            <div class='game-box'>
                <b>{g['visitor_team']['full_name']} @ {g['home_team']['full_name']}</b><br>
                <span>Status: {g['status']}</span>
            </div>
        """, unsafe_allow_html=True)


# ---------------------------
# YESTERDAY'S GAMES
# ---------------------------

st.markdown("<div class='section-header'>🕒 Yesterday's Scores</div>", unsafe_allow_html=True)

y_games = get_yesterday_games()

if y_games is None:
    st.error("API Error: Could not load yesterday's games.")
elif y_games == []:
    st.info("No games yesterday.")
else:
    for g in y_games:
        st.markdown(f"""
            <div class='game-box'>
                <b>{g['visitor_team']['full_name']} @ {g['home_team']['full_name']}</b><br>
                {g['visitor_team']['abbreviation']}: {g['visitor_team_score']} — 
                {g['home_team']['abbreviation']}: {g['home_team_score']}
            </div>
        """, unsafe_allow_html=True)


# ---------------------------
# PLAYER SEARCH
# ---------------------------

st.markdown("<div class='section-header'>🔍 Player Season Averages</div>", unsafe_allow_html=True)

player_name = st.text_input("Search for a player (ex: Luka Doncic, Curry, Tatum)")

if player_name:
    results = search_player(player_name)

    if results is None:
        st.error("API Error: Could not search for players.")
    elif results == []:
        st.error("No matching players found.")
    else:
        player = results[0]
        full_name = f"{player['first_name']} {player['last_name']}"
        team = player["team"]["full_name"]

        st.success(f"Found: **{full_name}** — {team}")

        stats = get_player_season_averages(player["id"])

        if not stats:
            st.warning("Season averages not available for this player.")
        else:

            # 3-column clean stat layout
            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric("PPG", round(stats.get("pts", 0), 1))
                st.metric("RPG", round(stats.get("reb", 0), 1))
                st.metric("APG", round(stats.get("ast", 0), 1))

            with c2:
                st.metric("FG%", f"{round(stats.get('fg_pct', 0)*100, 1)}%")
                st.metric("3P%", f"{round(stats.get('fg3_pct', 0)*100, 1)}%")
                st.metric("FT%", f"{round(stats.get('ft_pct', 0)*100, 1)}%")

            with c3:
                st.metric("STL", stats.get("stl", 0))
                st.metric("BLK", stats.get("blk", 0))
                st.metric("TOV", stats.get("turnover", 0))

