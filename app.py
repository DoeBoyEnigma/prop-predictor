import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma Prop Beast", layout="wide")
st.title("PrizePicks + DraftKings Prop Crusher")
st.sidebar.success("REAL DATA LIVE — Let’s eat")

# ==========================================
# LOAD REAL DATA
# ==========================================
@st.cache_data(ttl=3600)
def load_real_data():
    dfs = []

    # ---------------- NBA ----------------
    try:
        nba_url = "https://raw.githubusercontent.com/doeboyenigma/nba-player-logs/main/nba_logs_2024_2025.csv"
        nba = pd.read_csv(nba_url)
        nba["DATE"] = pd.to_datetime(nba["GAME_DATE"])
        nba = nba.rename(columns={"PLAYER_NAME": "PLAYER"})
        if "PRA" not in nba.columns:
            nba["PRA"] = nba["PTS"] + nba["REB"] + nba["AST"]
        nba = nba[["DATE", "PLAYER", "OPPONENT", "PTS", "REB", "AST", "PRA"]]
        dfs.append(nba)
    except Exception as e:
        st.warning(f"NBA load error: {e}")

    # ---------------- CS2 ----------------
    try:
        cs2_url = "https://raw.githubusercontent.com/doeboyenigma/cs2-player-stats/main/cs2_series_stats.csv"
        cs2 = pd.read_csv(cs2_url)
        cs2["DATE"] = pd.to_datetime(cs2["DATE"])
        cs2 = cs2[[
            "DATE", "PLAYER", "OPPONENT", "KILLS", "DEATHS", "ASSISTS",
            "HEADSHOTS", "HS_PCT", "MAPS_PLAYED"
        ]]
        dfs.append(cs2)
    except Exception as e:
        st.warning(f"CS2 load error: {e}")

    # ---------------- LoL ----------------
    try:
        lol_url = "https://raw.githubusercontent.com/doeboyenigma/lol-player-stats/main/lol_game_logs.csv"
        lol = pd.read_csv(lol_url)
        lol["DATE"] = pd.to_datetime(lol["DATE"])
        lol = lol.rename(columns={"VISIONSCORE": "VISION_SCORE"})
        lol = lol[[
            "DATE", "PLAYER", "ROLE", "OPPONENT",
            "KILLS", "ASSISTS", "CS", "VISION_SCORE"
        ]]
        dfs.append(lol)
    except Exception as e:
        st.warning(f"LoL load error: {e}")

    if dfs:
        return pd.concat(dfs, ignore_index=True)

    backup = "https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv"
    st.error("Failed loading real data — using backup dummy.")
    return pd.read_csv(backup)


df = load_real_data()

# ==========================================
# SIDEBAR
# ==========================================
sport = st.sidebar.selectbox("Sport", ["NBA", "NFL", "CS2", "Valorant", "LoL"])

stat_options = {
    "NBA": ["PTS", "REB", "AST", "PRA"],
    "CS2": ["KILLS", "HEADSHOTS", "HS_PCT"],
    "LoL": ["KILLS", "ASSISTS", "VISION_SCORE"],
    "NFL": ["YARDS", "RECEPTIONS", "TD"],
    "Valorant": ["KILLS", "ACS", "HS%"]
}

player = st.sidebar.selectbox("Player", sorted(df["PLAYER"].dropna().unique()))
stat = st.sidebar.selectbox("Stat", stat_options.get(sport, ["PTS"]))
window = st.sidebar.selectbox("Window", ["Last 3", "Last 5", "Last 10", "Season"])
opponent = st.sidebar.text_input("Opponent (H2H)", "")

# ==========================================
# FILTER PLAYER DATA
# ==========================================
player_df = df[df["PLAYER"] == player].copy()

if stat not in player_df.columns:
    st.error(f"Stat {stat} not found for this player.")
    st.stop()

player_df = player_df.sort_values("DATE", ascending=False)

# ==========================================
# H2H SECTION
# ==========================================
if opponent.strip():
    h2h = player_df[player_df["OPPONENT"].str.contains(opponent, case=False, na=False)]
    if not h2h.empty:
        h2h_avg = round(h2h[stat].mean(), 2)
        st.sidebar.success(f"Avg H2H vs {opponent}: {h2h_avg}")

# ==========================================
# WINDOW SAMPLE
# ==========================================
if "Season" in window:
    sample = player_df
else:
    games_num = int(window.split()[1])
    sample = player_df.head(games_num)

avg = round(sample[stat].mean(), 2)
projection = round(avg * 1.06, 2)

line = st.number_input("Line", value=float(avg), step=0.5)
edge = projection - line

# =====================================
