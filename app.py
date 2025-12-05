import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma CS2 + NBA Edge", layout="wide")
st.title("CS2 + NBA Prop Crusher")
st.sidebar.success("REAL HLTV + NBA DATA — LIVE")

# === REAL CS2 DATA FROM HLTV (no API key needed) ===
@st.cache_data(ttl=3600)
def get_cs2_data():
    url = "https://raw.githubusercontent.com/doeboyenigma/cs2-hltv-data/main/hltv_player_series_stats.csv"
    try:
        df = pd.read_csv(url)
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df.sort_values(['PLAYER', 'DATE'], ascending=[True, False])
    except:
        st.error("CS2 data loading — using backup")
        return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_cs2.csv")

# === REAL NBA DATA FROM NBA_API (public) ===
@st.cache_data(ttl=3600)
def get_nba_data():
    try:
        from nba_api.stats.endpoints import playergamelog
        from nba_api.stats.static import players
        all_logs = []
        top_players = ["LeBron James", "Stephen Curry", "Luka Doncic", "Nikola Jokic", "Jayson Tatum", "Devin Booker", "Anthony Davis"]
        for name in top_players:
            player = players.find_players_by_full_name(name)[0]
            log = playergamelog.PlayerGameLog(player_id=player['id'], season='2024').get_data_frames()[0]
            log['PLAYER'] = name
            log['DATE'] = pd.to_datetime(log['GAME_DATE'])
            log = log[['DATE', 'PLAYER', 'MATCHUP', 'PTS', 'REB', 'AST']]
            log['OPPONENT'] = log['MATCHUP'].apply(lambda x: x[-3:])
            all_logs.append(log)
        return pd.concat(all_logs).sort_values('DATE', ascending=False)
    except:
        st.error("NBA loading — using backup")
        return pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_nba.csv")

cs2_df = get_cs2_data()
nba_df = get_nba_data()

# Sport selector
sport = st.sidebar.selectbox("Sport", ["CS2", "NBA"])

if sport == "CS2":
    df = cs2_df
    players = sorted(df['PLAYER'].unique())
    player = st.sidebar.selectbox("Player", players)
    player_data = df[df['PLAYER'] == player].copy()
    
    st.sidebar.write(f"**Role:** {player_data['ROLE'].iloc[0]}")
    st.sidebar.write(f"**Team:** {player_data['TEAM'].iloc[0]}")
    
    stat = st.sidebar.selectbox("Stat", ["KILLS", "HEADSHOTS", "HS_PCT", "ASSISTS", "K/D"])
    window = st.sidebar.selectbox("Last X Series", ["3", "5", "8", "10", "All"])
    opponent = st.sidebar.text_input("vs Opponent (H2H)", "")
    
    n = int(window) if window != "All" else len(player_data)
    recent = player_data.head(n)
    
    if opponent:
        h2h = recent[recent['OPPONENT'].str.contains(opponent, case=False, na=False)]
        if not h2h.empty:
            st.sidebar.success(f"Last vs {opponent}: {h2h[stat].iloc[0]:.1f}")
        recent = h2h if not h2h.empty else recent
    
    avg = round(recent[stat].mean(), 2)
    projection = round(avg * 1.04, 2)  # slight boost for form
    
    line = st.number_input("PrizePicks Line", value=20.5, step=0.5)
    edge = projection - line
    
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Last {n} Series Avg", avg)
    col2.metric("Projection", projection, f"{edge:+.2f}")
    col3.metric("Edge", line, "MORE" if edge > 1 else "LESS" if edge < -1 else "Pass")
    
    with st.expander("Last Series"):
        show = recent[['DATE', 'OPPONENT', 'MAPS', 'KILLS', 'HEADSHOTS', 'HS_PCT']].head(10)
        show['DATE'] = show['DATE'].dt.strftime("%m-%d")
        st.dataframe(show)

elif sport == "NBA":
    df = nba_df
    player = st.sidebar.selectbox("Player", sorted(df['PLAYER'].unique()))
    player_data = df[df['PLAYER'] == player].copy()
    
    stat = st.sidebar.selectbox("Stat", ["PTS", "REB", "AST"])
    window = st.sidebar.selectbox("Last X Games", ["5", "10", "20", "Season"])
    opponent = st.sidebar.text_input("vs Opponent", "")
    
    n = int(window.split()[-1]) if "Season" not in window else len(player_data)
    recent = player_data.head(n)
    
    if opponent:
        h2h = recent[recent['OPPONENT'] == opponent]
        if not h2h.empty:
            st.sidebar.success(f"Last vs {opponent}: {h2h[stat].iloc[0]}")
        recent = h2h if not h2h.empty else recent
    
    avg = round(recent[stat].mean(), 2)
    projection = round(avg * 1.03, 2)
    
    line = st.number_input("Line", value=25.5, step=0.5)
    edge = projection - line
    
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Last {n} Avg", avg)
    col2.metric("Projection", projection, f"{edge:+.2f}")
    col3.metric("Pick", line, "MORE" if edge > 0.8 else "LESS")
    
    with st.expander("Last Games"):
        show = recent[['DATE', 'OPPONENT', stat]].head(10)
        show['DATE'] = pd.to_datetime(show['DATE']).dt.strftime("%m-%d")
        st.dataframe(show)

st.balloons()

