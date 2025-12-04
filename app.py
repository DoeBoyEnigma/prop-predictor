import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Prop Predictor Beast", layout="wide")
st.title("🏆 PrizePicks + DraftKings Prop Predictor")
st.sidebar.success("LIVE — Edge machine activated!")

# Dummy data (replace with your CSVs later)
@st.cache_data
def load_dummy():
    dates = pd.date_range("2025-01-01", periods=50, freq='D')[::-1]
    data = {
        "DATE": np.tile(dates, 5),
        "PLAYER": np.repeat(["LeBron James", "m0NESY", "Caps", "Jahmyr Gibbs", "ZywOo"], 10),
        "OPPONENT": np.random.choice(["Lakers", "G2", "Vitality", "Bengals", "FaZe"], 50),
        "PTS": np.random.normal(28, 6, 50).clip(10, 50),
        "Kills": np.random.normal(21, 5, 50).clip(5, 40),
        "Assists": np.random.normal(9, 3, 50).clip(0, 20),
        "HEADSHOTS": np.random.normal(13, 4, 50).clip(0, 25),
        "HS_PCT": np.random.normal(55, 8, 50).clip(30, 80)
    }
    df = pd.DataFrame(data)
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df.sort_values(['PLAYER', 'DATE'], ascending=[True, False])

df = load_dummy()

# Sidebar
sport = st.sidebar.selectbox("Sport", ["NBA", "NFL", "CS2", "Valorant", "LoL"])
player = st.sidebar.selectbox("Player", sorted(df["PLAYER"].unique()))
stat = st.sidebar.selectbox("Stat", ["PTS", "Kills", "Assists", "HEADSHOTS", "HS_PCT"])

window = st.sidebar.selectbox("Rolling Window", ["Last 3", "Last 5", "Season"])
opponent = st.sidebar.text_input("Opponent (H2H Edge)", "e.g. G2")

# Calc
player_df = df[df["PLAYER"] == player].copy()
if opponent:
    h2h = player_df[player_df["OPPONENT"].str.contains(opponent, case=False, na=False)]
    if not h2h.empty:
        st.sidebar.success(f"Last H2H vs {opponent}: {h2h[stat].iloc[0]:.1f}")

n = 3 if "3" in window else 5 if "5" in window else len(player_df)
avg = player_df[stat].head(n).mean()
projection = round(avg * 1.05, 2)  # Simple boost example

line = st.number_input("Prop Line", value=25.0, step=0.5)
edge = projection - line

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric(f"{window} Avg", f"{avg:.2f}")
col2.metric("Projection", f"{projection:.2f}", f"{edge:+.2f}")
col3.metric("Rec", line, "🟢 MORE" if edge > 0.5 else "🔴 LESS")

with st.expander("Last Games"):
    st.dataframe(player_df[["DATE", "OPPONENT", stat]].head(n).style.format({"DATE": "{:%Y-%m-%d}"}))
