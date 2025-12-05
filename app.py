import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma HLTV 2.0", layout="wide")
st.markdown("<h1 style='text-align: center; color: #00ff41;'>HLTV 2.0 — The Future Is Here</h1>", unsafe_allow_html=True)

# REAL HLTV DATA (auto-updated daily)
@st.cache_data(ttl=7200)
def get_hltv_data():
    url = "https://raw.githubusercontent.com/doeboyenigma/hltv-2.0/main/hltv_players_full.csv"
    df = pd.read_csv(url)
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df.sort_values(['PLAYER', 'DATE'], ascending=[True, False])

df = get_hltv_data()

# Dark mode + sick header
st.markdown("""
<style>
    .css-1d391kg {background: #0e1117; color: white;}
    .css-1v0mbdj {color: #00ff41;}
    .stMetric {background: #1a1f2e; padding: 15px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# Sidebar search
search = st.sidebar.text_input("Search Player", "")
role_filter = st.sidebar.multiselect("Role", options=df['ROLE'].unique(), default=[])
team_filter = st.sidebar.multiselect("Team", options=df['TEAM'].unique(), default=[])

# Filter
filtered = df.copy()
if search:
    filtered = filtered[filtered['PLAYER'].str.contains(search, case=False, na=False)]
if role_filter:
    filtered = filtered[filtered['ROLE'].isin(role_filter)]
if team_filter:
    filtered = filtered[filtered['TEAM'].isin(team_filter)]

# Top stats bar
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total Players", len(df['PLAYER'].unique()))
with col2: st.metric("Active Teams", len(df['TEAM'].unique()))
with col3: st.metric("Matches Tracked", len(df))
with col4: st.metric("Last Update", datetime.now().strftime("%b %d, %Y"))

# Player cards
for player in filtered['PLAYER'].unique()[:50]:  # Show top 50 or paginate later
    p = filtered[filtered['PLAYER'] == player].iloc[0]
    recent = filtered[filtered['PLAYER'] == player].head(10)
    
    kills_avg = round(recent['KILLS'].mean(), 1)
    hs_pct = round(recent['HS_PCT'].mean(), 1)
    kd = round(recent['K/D'].mean(), 2)
    
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1,2,1,1,2])
        with col1:
            st.image(f"https://www.hltv.org/img/static/player/player-{p['HLTV_ID']}.png", width=80)
        with col2:
            st.markdown(f"**{p['PLAYER']}**")
            st.caption(f"{p['TEAM']} • {p['ROLE']}")
        with col3:
            st.metric("KILLS/Series", kills_avg)
        with col4:
            st.metric("HS%", f"{hs_pct}%")
            st.metric("K/D", kd)
        with col5:
            if st.button("View Full", key=player):
                st.session_state.selected = player
        
        st.divider()

# Full player view
if 'selected' in st.session_state:
    player = st.session_state.selected
    data = filtered[filtered['PLAYER'] == player]
    
    st.subheader(f"{player} — Full Profile")
    col1, col2 = st.columns(2)
    with col1:
        st.image(f"https://www.hltv.org/img/static/player/player-{data['HLTV_ID'].iloc[0]}.png", width=200)
        st.write(f"**Team:** {data['TEAM'].iloc[0]}")
        st.write(f"**Role:** {data['ROLE'].iloc[0]}")
    with col2:
        st.metric("Career Rating", round(data['RATING'].mean(), 2))
        st.metric("Kills per Series (Last 10)", round(data['KILLS'].head(10).mean(), 1))
    
    st.dataframe(
        data[['DATE', 'OPPONENT', 'MAPS', 'KILLS', 'DEATHS', 'ASSISTS', 'HEADSHOTS', 'HS_PCT', 'K/D']]
        .head(20)
        .style.format({"DATE": "{:%m-%d}", "HS_PCT": "{:.1f}%"})
    )
