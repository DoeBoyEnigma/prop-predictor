import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma Prop Beast", layout="wide")
st.title("PrizePicks + DraftKings Prop Crusher")
st.sidebar.success("REAL DATA LIVE — Let’s eat")

# -----------------------------
# LOAD REAL DATA
# -----------------------------
@st.cache_data(ttl=3600)
def load_real_data():
    dfs = []

    # NBA
    try:
        nba = pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/nba-player-logs/main/nba_logs_2024_2025.csv")
        nba["DATE"] = pd.to_datetime(nba["GAME_DATE"])
        nba = nba.rename(columns={"PLAYER_NAME": "PLAYER"})
        if "PRA" not in nba.columns:
            nba["PRA"] = nba["PTS"] + nba["REB"] + nba["AST"]
        nba = nba[["DATE", "PLAYER", "OPPONENT", "PTS", "REB", "AST", "PRA"]]
        dfs.append(nba)
    except Exception as e:
        st.warning(f"NBA load error: {e}")

    # CS2
    try:
        cs2 = pd.read_csv("https://raw.githubusercontent.com/doeboyenigma/cs2-playe_

