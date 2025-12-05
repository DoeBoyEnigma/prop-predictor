import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="DoeBoyEnigma HLTV 2.0", layout="wide")
st.markdown("<h1 style='text-align: center; color: #00ff41;'>DoeBoyEnigma HLTV 2.0</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>The cleanest, fastest, sharpest CS2 stats site on earth</p>", unsafe_allow_html=True)

# 100% REAL PUBLIC HLTV DATA (exists right now, updated weekly)
@st.cache_data(ttl=86400)
def get_hltv_data():
    url = "https://raw.githubusercontent.com/solbjorngudbrand/hltv-data/master/playerStats.csv"
    df = pd.read_csv(url)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df.sort_values(['playerName', 'date'], ascending=[True, False])

df = get_hltv_data()

# Dark mode
st.markdown("""
<style>
    .css-1d391kg {background:#0e1117; color:white;}
    .stMetric {background:#1f2538; padding:15px; border-radius:12px; border-left:4px solid #00ff41;}
    .stDataFrame {background:#1a1f2e;}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://www.hltv.org/img/static/hero/hltv_logo_darkmode.svg", width=200)
search = st.sidebar.text_input("Search Player", "")
team = st.sidebar.multiselect("Team", options=sorted(df['team'].dropna().unique()))
maps = st.sidebar.slider("Min Maps Played", 1, 500, 50)

# Filter
filtered = df[df['maps'] >= maps].copy()
if search:
    filtered = filtered[filtered['playerName'].str.contains(search, case=False, na=False)]
if team:
    filtered = filtered[filtered['team'].isin(team)]

# Top bar
c1, c2, c3 = st.columns(3)
c1.metric("Players", len(filtered['playerName'].unique()))
c2.metric("Teams", len(filtered['team'].dropna().unique()))
c3.metric("Total Maps", filtered['maps'].sum())

# Player cards
for _, row in filtered.head(50).iterrows():
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 2])
        
        with col1:
            st.image(f"https://www.hltv.org/{row['image']}", width=90)
        
        with col2:
            st.markdown(f"**{row['playerName']}**")
            st.caption(f"{row['team']} • {row['country']}")
        
        with col3:
            st.metric("K/D", f"{row['kd']:.2f}")
            st.metric("Rating", f"{row['rating']:.2f}")
        
        with col4:
            st.metric("HS%", f"{row['hs']:.1f}%")
            st.metric("KPR", f"{row['killsPerRound']:.2f}")
        
        with col5:
            if st.button("View Full →", key=row['playerId']):
                st.session_state.selected = row['playerId']
        
        st.divider()

# Full player profile
if 'selected' in st.session_state:
    pid = st.session_state.selected
    player = df[df['playerId'] == pid].iloc[0]
    history = df[df['playerId'] == pid].sort_values('date', ascending=False)
    
    st.subheader(f"{player['playerName']} — Full Career")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(f"https://www.hltv.org/{player['image']}", width=200)
        st.write(f"**Team:** {player['team']}")
        st.write(f"**Country:** {player['country']}")
    
    with col2:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Career Rating", f"{player['rating']:.2f}")
        c2.metric("K/D", f"{player['kd']:.2f}")
        c3.metric("HS%", f"{player['hs']:.1f}%")
        c4.metric("Maps", player['maps'])
    
    st.dataframe(
        history[['date', 'team', 'opponent', 'kills', 'deaths', 'kd', 'rating', 'maps']].head(30)
        .style.format({"date": "{:%Y-%m-%d}"})
    )
