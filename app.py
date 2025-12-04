import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma Prop Beast", layout="wide")
st.title("PrizePicks + DraftKings Prop Crusher")
st.sidebar.success("REAL DATA LIVE — Let’s eat")

# REAL DATA SOURCES (auto-updates daily)
@st.cache_data(ttl=3600)  # Refresh every hour
def load_real_data():
    dfs = []
    
    # NBA (last 2 seasons player logs)
    try:
        nba = pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/nba-player-logs/main/nba_logs_2024_2025.csv")
        nba['DATE'] = pd.to_datetime(nba['GAME_DATE'])
        nba = nba[['DATE', 'PLAYER_NAME', 'OPPONENT', 'PTS', 'REB', 'AST', 'PRA']].rename(columns={'PLAYER_NAME': 'PLAYER'})
        dfs.append(nba)
    except: pass
    
    # CS2 (HLTV + PandaScore style — using public dataset)
    try:
        cs2 = pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/cs2-player-stats/main/cs2_series_stats.csv")
        cs2['DATE'] = pd.to_datetime(cs2['DATE'])
        cs2 = cs2[['DATE', 'PLAYER', 'OPPONENT', 'KILLS', 'DEATHS', 'ASSISTS', 'HEADSHOTS', 'HS_PCT', 'MAPS_PLAYED']]
        dfs.append(cs2)
    except: pass
    
    # LoL (Oracle's Elixir public data)
    try:
        lol = pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/lol-player-stats/main/lol_game_logs.csv")
        lol['DATE'] = pd.to_datetime(lol['DATE'])
        lol = lol[['DATE', 'PLAYER', 'ROLE', 'OPPONENT', 'KILLS', 'ASSISTS', 'CS', 'VISIONSCORE']].rename(columns={'VISIONSCORE': 'VISION_SCORE'})
        dfs.append(lol)
    except: pass
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        st.error("Data loading — using backup dummy")
        return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv")

df = load_real_data()

# Sidebar
sport = st.sidebar.selectbox("Sport", ["NBA", "NFL", "CS2", "Valorant", "LoL"])
player = st.sidebar.selectbox("Player", sorted(df["PLAYER"].unique()))
stat_options = {
    "NBA": ["PTS", "REB", "AST", "PRA"],
    "CS2": ["KILLS", "HEADSHOTS", "HS_PCT"],
    "LoL": ["KILLS", "ASSISTS", "VISION_SCORE"]
}
stat = st.sidebar.selectbox("Stat", stat_options.get(sport, ["PTS"]))

window = st.sidebar.selectbox("Window", ["Last 3", "Last 5", "Last 10", "Season"])
opponent = st.sidebar.text_input("Opponent (H2H)", "e.g. G2")

# Filter + H2H
player_df = df[df["PLAYER"] == player].copy()
if opponent:
    h2h = player_df[player_df["OPPONENT"].str.contains(opponent, case=False, na=False)]
    if not h2h.empty:
        st.sidebar.success(f"Last H2H vs {opponent}: {h2h[stat].iloc[0]:.1f}")

n = {"3":3,"5":5,"10":10}.get(window.split()[-1], len(player_df))
avg = round(player_df[stat].head(n).mean(), 2)
projection = round(avg * 1.06, 2)  # Slight model boost

line = st.number_input("Line", value=24.5, step=0.5)
edge = projection - line

col1, col2, col3 = st.columns(3)
col1.metric(f"{window} Avg", avg)
col2.metric("Projection", projection, f"{edge:+.2f}")
col3.metric("Pick", line, "MORE" if edge > 0.7 else "LESS" if edge < -0.7 else "Pass")

with st.expander("Last Games Used"):
    show = player_df[["DATE", "OPPONENT", stat]].head(n)
    show["DATE"] = show["DATE"].dt.strftime("%Y-%m-%d")
    st.dataframe(show)

st.balloons()
