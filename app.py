# app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import subprocess
import sys
import time

st.set_page_config(page_title="DoeBoyEnigma Prop Beast", layout="wide")
st.title("PrizePicks + DraftKings Prop Crusher")

# -------------------------------
# SETTINGS
# -------------------------------
THRESH = 0.7  # edge threshold for pick
BACKUP_CSV = "https://raw.githubusercontent.com/doeboyenigma/prop-predictor/main/backup_dummy.csv"

# -------------------------------
# Ensure nba_api available (best-effort; many Streamlit hosts permit pip at runtime)
# -------------------------------
def ensure_nba_api():
    try:
        import nba_api  # noqa: F401
        return True
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "nba_api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # small pause to let install settle
            time.sleep(1)
            import nba_api  # noqa: F401
            return True
        except Exception:
            return False

NBA_API_AVAILABLE = ensure_nba_api()

# -------------------------------
# LOAD DATA / API FUNCTIONS
# -------------------------------

# --- NBA via nba_api (preferred) with fallback to balldontlie
@st.cache_data(ttl=3600)
def load_nba_player_stats(player_name, max_games=100):
    """
    Returns a DataFrame with columns: DATE, PLAYER, OPPONENT, PTS, REB, AST, PRA
    Uses nba_api if available, else falls back to balldontlie (less precise).
    """
    player_name = player_name.strip()
    if not player_name:
        return None

    # Try using nba_api for best precision
    if NBA_API_AVAILABLE:
        try:
            from nba_api.stats.static import players as nba_players
            from nba_api.stats.endpoints import playergamelog
            # find candidate players by full name match or substring match
            found = nba_players.find_players_by_full_name(player_name)
            if not found:
                # try simple search through all players
                all_players = nba_players.get_active_players()
                matches = [p for p in all_players if player_name.lower() in p['full_name'].lower()]
                if matches:
                    found = matches
            if not found:
                return None
            # pick top match
            player = found[0]
            pid = player['id']
            # request last season regular season gamelog (nba_api handles headers)
            gl = playergamelog.PlayerGameLog(player_id=pid, season='2024-25', season_type_all_star='Regular Season')
            df = gl.get_data_frames()[0]
            if df.empty:
                # fallback to multiple seasons (recent)
                gl = playergamelog.PlayerGameLog(player_id=pid)
                df = gl.get_data_frames()[0]
            # normalize columns
            df = df.rename(columns={c: c.upper() for c in df.columns})
            # ensure required columns exist
            # DATE is GAME_DATE
            if 'GAME_DATE' in df.columns:
                df['DATE'] = pd.to_datetime(df['GAME_DATE'])
            elif 'GAME_DATE_EST' in df.columns:
                df['DATE'] = pd.to_datetime(df['GAME_DATE_EST'])
            else:
                df['DATE'] = pd.NaT
            # Points/Reb/Ast
            pts = df.get('PTS', pd.Series(np.nan,index=df.index))
            reb = df.get('REB', pd.Series(np.nan,index=df.index))
            ast = df.get('AST', pd.Series(np.nan,index=df.index))
            # Opponent column: match-up column has form "LAL vs. BOS" or "LAL @ BOS"
            matchup = df.get('MATCHUP', pd.Series('', index=df.index))
            def parse_opp(m):
                try:
                    parts = m.split()
                    # last token is opponent abbreviation (either 'BOS' or 'vs.' followed by 'BOS')
                    if len(parts) >= 1:
                        # matchup like 'LAL vs BOS' or 'LAL @ BOS' -> last token is opponent
                        return parts[-1]
                except:
                    return ""
                return ""
            opp = matchup.apply(parse_opp)
            out = pd.DataFrame({
                'DATE': df['DATE'],
                'PLAYER': player['full_name'],
                'OPPONENT': opp,
                'PTS': pts,
                'REB': reb,
                'AST': ast
            }).sort_values('DATE', ascending=False).head(max_games)
            out['PRA'] = out['PTS'].fillna(0) + out['REB'].fillna(0) + out['AST'].fillna(0)
            return out[['DATE','PLAYER','OPPONENT','PTS','REB','AST','PRA']]
        except Exception as e:
            # if anything goes wrong, fall through to balldontlie fallback
            st.sidebar.error(f"nba_api fetch error, falling back: {str(e)[:200]}")
    # Fallback: balldontlie (less complete but public, no key)
    try:
        resp = requests.get("https://www.balldontlie.io/api/v1/players", params={"search": player_name}, timeout=10)
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
                params={"player_ids[]": player_id, "per_page": 100, "page": page},
                timeout=10
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
        df["OPPONENT"] = [
            g["game"]["home_team"]["abbreviation"] if g["game"]["home_team"]["id"] != g["team"]["id"] else g["game"]["visitor_team"]["abbreviation"]
            for g in games
        ]
        return df[["DATE", "PLAYER", "OPPONENT", "PTS", "REB", "AST", "PRA"]]
    except Exception:
        return None

# --- CS2 via unofficial HLTV API (hltv-api.vercel.app)
@st.cache_data(ttl=1800)
def load_cs2_stats(player_name):
    """
    Attempts to find player via HLTV unofficial API and returns a DataFrame
    with DATE, PLAYER, OPPONENT (team), KILLS, HEADSHOTS, HS_PCT columns if available.
    """
    try:
        base = "https://hltv-api.vercel.app/api"
        # fetch players list (this endpoint returns many players; we'll filter)
        players_resp = requests.get(f"{base}/players", timeout=10)
        if players_resp.status_code != 200:
            return None
        players = players_resp.json()
        # players is likely a list of dicts with 'name' and 'id'
        candidates = [p for p in players if player_name.lower() in p.get('name','').lower()]
        if not candidates:
            # try exact match
            candidates = [p for p in players if p.get('name','').lower() == player_name.lower()]
        if not candidates:
            return None
        player = candidates[0]
        pid = player.get('id')
        if not pid:
            return None
        # fetch player details (may include stats)
        p_resp = requests.get(f"{base}/player/{pid}", timeout=10)
        if p_resp.status_code != 200:
            return None
        pdata = p_resp.json()
        # Format depends on the API, so be defensive:
        rows = []
        # possible keys: recentMatches or matches or stats
        recent_matches = pdata.get('recentMatches') or pdata.get('matches') or pdata.get('recent') or []
        for m in recent_matches:
            # m likely contains date, team vs, maps, stats
            date = m.get('date') or m.get('dateString') or None
            try:
                date = pd.to_datetime(date)
            except:
                date = None
            kills = m.get('kills') or (m.get('stats') or {}).get('kills') or np.nan
            hs = m.get('headshots') or (m.get('stats') or {}).get('headshots') or np.nan
            hs_pct = None
            try:
                if kills and hs:
                    hs_pct = round(100 * float(hs) / float(kills), 2) if float(kills) != 0 else np.nan
            except:
                hs_pct = np.nan
            opponent = m.get('opponent') or m.get('teamOpp') or m.get('event') or ""
            rows.append({
                'DATE': date,
                'PLAYER': player.get('name'),
                'OPPONENT': opponent,
                'KILLS': kills,
                'HEADSHOTS': hs,
                'HS_PCT': hs_pct
            })
        if not rows:
            # Sometimes API returns stats directly under pdata['stats']
            stats = pdata.get('stats')
            if stats:
                # create synthetic rows from aggregated stats
                rows.append({
                    'DATE': pd.NaT,
                    'PLAYER': player.get('name'),
                    'OPPONENT': '',
                    'KILLS': stats.get('kills', np.nan),
                    'HEADSHOTS': stats.get('headshots', np.nan),
                    'HS_PCT': stats.get('hsPct', np.nan)
                })
        df = pd.DataFrame(rows)
        if df.empty:
            return None
        df = df.sort_values('DATE', ascending=False)
        return df
    except Exception:
        return None

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
elif sport == "CS2" and player:
    df = load_cs2_stats(player)
elif player:
    # for esports we haven't implemented API-key based sources yet
    st.sidebar.info("LoL/Valorant/Dota 2 require API keys or are not enabled in this build. Falling back to backup dummy.")
    df = None

if df is None or (isinstance(df, pd.DataFrame) and df.empty):
    st.warning("No data found for this player — using backup dummy")
    df = pd.read_csv(BACKUP_CSV)

# -------------------------------
# NORMALIZE/SANITIZE DATAFRAME
# -------------------------------
# Ensure we have a PLAYER column (fallback)
if 'PLAYER' not in df.columns:
    # try to create PLAYER from input
    df['PLAYER'] = player if player else df.columns[0] if df.shape[1] > 0 else "UNKNOWN"

# ensure DATE column
if 'DATE' not in df.columns:
    # try to find any date-like column
    for c in df.columns:
        if 'date' in c.lower():
            df['DATE'] = pd.to_datetime(df[c], errors='coerce')
            break
    if 'DATE' not in df.columns:
        df['DATE'] = pd.NaT

# coerce stat column to numeric if present
if stat not in df.columns:
    # attempt to create stat from combinations (e.g., PRA)
    if stat == "PRA" and set(['PTS','REB','AST']).issubset(df.columns):
        df['PRA'] = df['PTS'].fillna(0) + df['REB'].fillna(0) + df['AST'].fillna(0)
    else:
        # add numeric NaNs for requested stat so code doesn't blow up
        df[stat] = np.nan

df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
df = df.sort_values('DATE', ascending=False)

# -------------------------------
# H2H filtering
# -------------------------------
if opponent.strip():
    if 'OPPONENT' in df.columns:
        h2h = df[df['OPPONENT'].astype(str).str.contains(opponent, case=False, na=False)]
        if not h2h.empty:
            try:
                st.sidebar.success(f"Avg last H2H vs {opponent}: {round(h2h[stat].mean(),2)}")
            except Exception:
                st.sidebar.success(f"Found H2H rows vs {opponent} (couldn't calculate mean for selected stat).")
    else:
        st.sidebar.info("Opponent filtering not available: dataset has no OPPONENT column.")

# -------------------------------
# WINDOW
# -------------------------------
if window == "Season":
    sample = df
else:
    try:
        num = int(window.split()[1])
    except:
        num = 5
    sample = df.head(num)

# compute avg/projection/line/edge
try:
    avg = round(float(sample[stat].astype(float).mean()), 2)
except Exception:
    avg = 0.0
projection = round(avg * 1.06, 2)

line = st.number_input("Line", value=float(avg), step=0.5)
edge = projection - line

# -------------------------------
# METRICS
# -------------------------------
col1, col2, col3 = st.columns(3)
col1.metric(f"{window} Avg", avg)
col2.metric("Projection", projection, f"{edge:+.2f}")

# Show the pick as the main value and the line as the delta (so it displays sensibly)
if edge > THRESH:
    pick = "MORE"
elif edge < -THRESH:
    pick = "LESS"
else:
    pick = "Pass"

# display pick prominently: label = "Pick", value = pick, delta = line (so delta shows the line)
col3.metric("Pick", pick, f"Line: {line}")

# -------------------------------
# LAST GAMES TABLE
# -------------------------------
with st.expander("Last Games Used"):
    # show only safe columns
    show_cols = []
    for c in ["DATE","OPPONENT", stat]:
        if c in sample.columns:
            show_cols.append(c)
    if not show_cols:
        st.write("No game-level columns available to show.")
    else:
        show = sample[show_cols].copy()
        if "DATE" in show.columns:
            show["DATE"] = pd.to_datetime(show["DATE"], errors='coerce').dt.strftime("%Y-%m-%d")
        st.dataframe(show)

st.balloons()

