import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma Prop Beast", layout="wide")
st.title("PrizePicks + DraftKings Prop Crusher")

# -------------------------------
# SETTINGS
# -------------------------------
THRESH = 0.7  # edge threshold for pick

# -------------------------------
# LOAD DATA / API FUNCTIONS
# -------------------------------

# --- NBA via balldontlie ---
@st.cache_data(ttl=3600)
def load_nba_player_stats(player_name):
    try:
        # find player
        resp = requests.get("https://www.balldontlie.io/api/v1/players", params={"search": player_name})
        data = resp.json().get("data", [])
        if not data:
            return None
        player_id = data[0]["id"]

        # get last 100 games
        games = []
        page = 0
        while True:
            page += 1
            resp = requests.get(
                "https://www.balldontlie.io/api/v1/stats",
                params={"player_ids[]": player_id, "per_page": 100, "page": page}
            )
            js = resp.json()
            if not js.get("data"): break
            games.extend(js["data"])
            if len(js["data"]) < 100: break

        if not games:
            return None

        df = pd.DataFrame(games)
        df["DATE"] = pd.to_datetime([g["game"]["date"] for g in games])
        df["PLAYER"] = player_name
        df["PTS"] = [g["pts"] for g in games]
        df["REB"] = [g["reb"] for g in games]
        df["AST"] = [g["ast"] for g in games]
        df["PRA"] = df["PTS"] + df["REB"] + df["AST"]
        df["OPPONENT"] = [g["game"]["home_team"]["abbreviation"] if g["game"]["home_team"]["id"] != g["team"]["id"] else g["game"]["visitor_team"]["abbreviation"] for g in games]
        return df[["DATE", "PLAYER", "OPPONENT", "PTS", "REB", "AST", "PRA"]]
    except:
        return None

# --- Placeholder functions for other sports ---
def load_lol_stats(player_name):
    # TODO: replace with Riot API
    # fallback dummy
    return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv")

def load_valorant_stats(player_name):
    # TODO: replace with Riot API
    # fallback dummy
    return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv")

def load_dota2_stats(player_name):
    # TODO: replace with STRATZ API
    # fallback dummy
    return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv")

def load_cs2_stats(player_name):
    # TODO: replace with FACEIT API or HLTV Kaggle CSV
    # fallback dummy
    return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv")

# -------------------------------
# APP SIDEBAR
# -------------------------------
sport = st.sidebar.selectbox("Sport", ["NBA", "LoL", "Valorant", "Dota 2", "CS2"])
player = st.sidebar.text_input("Player name (exact or partial)")

stat_options = {
    "NBA": ["PTS", "REB", "AST", "PRA"],
    "LoL": ["KILLS", "ASSISTS", "VISION_SCORE"],
    "Valorant": ["KILLS", "ACS", "HS_PCT"],
    "Dota 2": ["KILLS", "ASSISTS", "DEATHS", "GPM", "XPM"],
    "CS2": ["KILLS", "HEADSHOTS", "HS_PCT"]
}
stat = st.sidebar.selectbox("Stat", stat_options.get(sport, ["PTS"]))
window = st.sidebar.selectbox("Window", ["Last 3", "Last 5", "Last 10", "Season"])
opponent = st.sidebar.text_input("Opponent (H2H)", "")

# -------------------------------
# LOAD DATA BASED ON SPORT
# -------------------------------
df = None
if sport == "NBA" and player:
    df = load_nba_player_stats(player)
elif sport == "LoL" and player:
    df = load_lol_stats(player)
elif sport == "Valorant" and player:
    df = load_valorant_stats(player)
elif sport == "Dota 2" and player:
    df = load_dota2_stats(player)
elif sport == "CS2" and player:
    df = load_cs2_stats(player)

if df is None or df.empty:
    st.warning("No data found for this player — using backup dummy")
    df = pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv")

# -------------------------------
# FILTER PLAYER DATA
# -------------------------------
player_df = df[df["PLAYER"].str.contains(player, case=False, na=False)].copy()
player_df["DATE"] = pd.to_datetime(player_df["DATE"], errors="coerce")
player_df = player_df.sort_values("DATE", ascending=False)

# H2H filtering
if opponent.strip():
    h2h = player_df[player_df["OPPONENT"].str.contains(opponent, case=False, na=False)]
    if not h2h.empty:
        st.sidebar.success(f"Avg last H2H vs {opponent}: {round(h2h[stat].mean(),2)}")

# WINDOW
if window == "Season":
    sample = player_df
else:
    num = int(window.split()[1])
    sample = player_df.head(num)

avg = round(sample[stat].mean(), 2)
projection = round(avg * 1.06, 2)

line = st.number_input("Line", value=float(avg), step=0.5)
edge = projection - line

# -------------------------------
# METRICS
# -------------------------------
col1, col2, col3 = st.columns(3)
col1.metric(f"{window} Avg", avg)
col2.metric("Projection", projection, f"{edge:+.2f}")

if edge > THRESH:
    pick = "MORE"
elif edge < -THRESH:
    pick = "LESS"
else:
    pick = "Pass"
col3.metric("Pick", line, pick)

# -------------------------------
# LAST GAMES TABLE
# -------------------------------
with st.expander("Last Games Used"):
    show = sample[["DATE", "OPPONENT", stat]].copy()
    show["DATE"] = show["DATE"].dt.strftime("%Y-%m-%d")
    st.dataframe(show)

st.balloons()

