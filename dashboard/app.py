from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="Paper Trading Dashboard", layout="wide")


def get_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        st.error(f"Missing environment variable: {name}")
        st.stop()
    return v


@st.cache_data(ttl=120)
def fetch_table(table: str) -> pd.DataFrame:
    url = get_env("SUPABASE_URL").rstrip("/")
    key = get_env("SUPABASE_KEY")
    endpoint = f"{url}/rest/v1/{table}?select=*"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    resp = requests.get(endpoint, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return pd.DataFrame(data)


st.title("Live Paper Trading Dashboard")

page = st.sidebar.radio(
    "Page",
    [
        "Current Portfolio",
        "Open Positions",
        "Closed Trades",
        "Rotation History",
        "Equity Curve",
        "Daily Performance",
        "TQS Rankings",
    ],
)

trades = fetch_table("paper_trades")
snapshots = fetch_table("portfolio_snapshots")
rotations = fetch_table("rotation_log")

if page == "Current Portfolio":
    st.subheader("Latest Portfolio Snapshot")
    if snapshots.empty:
        st.info("No snapshots yet.")
    else:
        snapshots["timestamp"] = pd.to_datetime(snapshots["timestamp"], errors="coerce")
        latest = snapshots.sort_values("timestamp").iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cash", f"{latest['cash']:.2f}")
        c2.metric("Equity", f"{latest['equity']:.2f}")
        c3.metric("Positions", int(latest["positions"]))
        c4.metric("Daily PnL", f"{latest['daily_pnl']:.2f}")

elif page == "Open Positions":
    st.subheader("Open Positions (BUY without matching SELL)")
    if trades.empty:
        st.info("No trades yet.")
    else:
        t = trades.copy()
        t["timestamp"] = pd.to_datetime(t["timestamp"], errors="coerce")
        buys = t[t["action"] == "BUY"]
        sells = t[t["action"] == "SELL"]["symbol"].value_counts()
        buys = buys.assign(close_count=buys["symbol"].map(sells).fillna(0).astype(int))
        open_df = buys[buys["close_count"] == 0].sort_values("timestamp", ascending=False)
        st.dataframe(open_df, use_container_width=True)

elif page == "Closed Trades":
    st.subheader("Closed Trades")
    st.dataframe(trades[trades["action"] == "SELL"], use_container_width=True)

elif page == "Rotation History":
    st.subheader("Rotation Log")
    st.dataframe(rotations.sort_values("timestamp", ascending=False), use_container_width=True)

elif page == "Equity Curve":
    st.subheader("Equity Curve")
    if snapshots.empty:
        st.info("No snapshots yet.")
    else:
        s = snapshots.copy()
        s["timestamp"] = pd.to_datetime(s["timestamp"], errors="coerce")
        s = s.sort_values("timestamp")
        st.line_chart(s.set_index("timestamp")["equity"])

elif page == "Daily Performance":
    st.subheader("Daily Performance")
    if snapshots.empty:
        st.info("No snapshots yet.")
    else:
        s = snapshots.copy()
        s["timestamp"] = pd.to_datetime(s["timestamp"], errors="coerce")
        s["date"] = s["timestamp"].dt.date
        daily = s.groupby("date", as_index=False)["daily_pnl"].sum()
        st.bar_chart(daily.set_index("date")["daily_pnl"])
        st.dataframe(daily.sort_values("date", ascending=False), use_container_width=True)

elif page == "TQS Rankings":
    st.subheader("Latest Candidate Rankings")
    try:
        cands = pd.read_csv("logs/live_candidates.csv")
    except Exception:
        cands = pd.DataFrame()
    if cands.empty:
        st.info("No live candidates found yet.")
    else:
        st.dataframe(cands.sort_values("candidate_score", ascending=False), use_container_width=True)

