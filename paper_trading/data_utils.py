from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pyotp
import requests
from dotenv import load_dotenv
from SmartApi import SmartConnect
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")

UNIVERSE_FILE = Path("configs/nifty500_symbols.txt")
TOKENS_CACHE = Path("data/instruments.json")
LIVE_2H_DIR = Path("data/live/2h")
LOG_FILE = Path("logs/data_update_log.csv")


@dataclass
class AngelCredentials:
    client_id: str
    api_key: str
    pin: str
    totp_secret: str


@dataclass
class UpdateResult:
    timestamp: str
    symbol: str
    bars_saved: int
    latest_close: float
    status: str
    error: str


def load_credentials_from_env() -> AngelCredentials:
    load_dotenv()
    required = {
        "ANGEL_CLIENT_ID": os.getenv("ANGEL_CLIENT_CODE", "").strip(),
        "ANGEL_API_KEY": os.getenv("ANGEL_API_KEY", "").strip(),
        "ANGEL_PIN": os.getenv("ANGEL_PASSWORD", "").strip(),
        "ANGEL_TOTP_SECRET": os.getenv("ANGEL_TOTP", "").strip(),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )
    return AngelCredentials(
        client_id=required["ANGEL_CLIENT_ID"],
        api_key=required["ANGEL_API_KEY"],
        pin=required["ANGEL_PIN"],
        totp_secret=required["ANGEL_TOTP_SECRET"],
    )


def load_nifty500_universe() -> list[str]:
    if not UNIVERSE_FILE.exists():
        raise FileNotFoundError(f"Universe file missing: {UNIVERSE_FILE}")
    with UNIVERSE_FILE.open("r", encoding="utf-8-sig") as f:
        symbols = [line.strip() for line in f if line.strip()]
    return sorted(set(symbols))


def create_smart_session(creds: AngelCredentials) -> SmartConnect:
    smart = SmartConnect(api_key=creds.api_key)
    otp = pyotp.TOTP(creds.totp_secret).now()
    _ = smart.generateSession(creds.client_id, creds.pin, otp)
    return smart


def load_instrument_master(force_refresh: bool = False) -> list[dict[str, Any]]:
    if TOKENS_CACHE.exists() and not force_refresh:
        with TOKENS_CACHE.open("r", encoding="utf-8") as f:
            return json.load(f)

    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    resp = requests.get(url, timeout=40)
    resp.raise_for_status()
    data = resp.json()
    TOKENS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with TOKENS_CACHE.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def build_symbol_token_map(master: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in master:
        if row.get("exch_seg") != "NSE":
            continue
        symbol = str(row.get("symbol", "")).strip()
        token = str(row.get("token", "")).strip()
        if not symbol or not token:
            continue
        # Prefer EQ symbols if multiple rows exist.
        if symbol.endswith("-EQ"):
            out[symbol] = token
        elif symbol not in out:
            out[symbol] = token
    return out


def _smart_get_candles(
    smart: SmartConnect,
    symbol_token: str,
    from_dt_ist: datetime,
    to_dt_ist: datetime,
) -> pd.DataFrame:
    params = {
        "exchange": "NSE",
        "symboltoken": str(symbol_token),
        "interval": "ONE_HOUR",
        "fromdate": from_dt_ist.strftime("%Y-%m-%d %H:%M"),
        "todate": to_dt_ist.strftime("%Y-%m-%d %H:%M"),
    }
    raw = smart.getCandleData(params)
    if isinstance(raw, dict):
        status = raw.get("status")
        message = " ".join(
            str(raw.get(k, ""))
            for k in ("message", "error", "errorcode")
            if raw.get(k)
        )
        retryable = any(
            marker in message.lower()
            for marker in ("429", "rate limit", "timeout", "timed out", "too many requests")
        )
        if status is False and retryable:
            raise RuntimeError(f"Angel API retryable error: {message or raw}")

    rows = raw.get("data") if isinstance(raw, dict) else None
    if not rows:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True).dt.tz_convert(IST)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["datetime", "open", "high", "low", "close", "volume"])
    return df.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)


def fetch_recent_hourly_data(
    smart: SmartConnect,
    symbol_token: str,
    existing_2h_file: Path,
    days_bootstrap: int = 45,
    days_incremental: int = 7,
    pause_sec: float = 0.05,
) -> pd.DataFrame:
    now_ist = datetime.now(IST)
    if existing_2h_file.exists():
        from_dt = now_ist - timedelta(days=days_incremental)
    else:
        from_dt = now_ist - timedelta(days=days_bootstrap)

    # Chunk requests to reduce SmartAPI window errors on long ranges.
    frames: list[pd.DataFrame] = []
    cursor = from_dt
    while cursor < now_ist:
        chunk_to = min(cursor + timedelta(days=20), now_ist)
        chunk_df = _smart_get_candles(smart, symbol_token, cursor, chunk_to)
        if not chunk_df.empty:
            frames.append(chunk_df)
        cursor = chunk_to + timedelta(minutes=1)
        time.sleep(pause_sec)

    if not frames:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)
    return out


def build_2h_bars_from_hourly(hourly_df: pd.DataFrame) -> pd.DataFrame:
    if hourly_df.empty:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    sdf = hourly_df.copy()
    sdf = sdf.set_index("datetime")
    sdf = sdf.between_time("09:15", "15:30")
    if sdf.empty:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    sdf["date"] = sdf.index.date
    sessions = [("09:15", "11:15"), ("11:15", "13:15"), ("13:15", "15:30")]
    rows: list[dict[str, Any]] = []
    for _, day_df in sdf.groupby("date"):
        for start, end in sessions:
            chunk = day_df.between_time(start, end)
            if chunk.empty:
                continue
            rows.append(
                {
                    "datetime": chunk.index[0],
                    "open": float(chunk["open"].iloc[0]),
                    "high": float(chunk["high"].max()),
                    "low": float(chunk["low"].min()),
                    "close": float(chunk["close"].iloc[-1]),
                    "volume": float(chunk["volume"].sum()),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    out = out.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)
    return out


def filter_completed_2h_bars(bars: pd.DataFrame, now_ist: datetime | None = None) -> pd.DataFrame:
    if bars.empty:
        return bars
    now_ist = now_ist or datetime.now(IST)
    df = bars.copy()
    dt = pd.to_datetime(df["datetime"], errors="coerce")
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize(IST)
    else:
        dt = dt.dt.tz_convert(IST)
    end_dt = dt.copy()

    hours = dt.dt.hour
    mins = dt.dt.minute
    # Session starts: 09:15, 11:15, 13:15
    end_dt = end_dt.mask((hours == 9) & (mins == 15), dt.dt.normalize() + pd.Timedelta(hours=11, minutes=15))
    end_dt = end_dt.mask((hours == 11) & (mins == 15), dt.dt.normalize() + pd.Timedelta(hours=13, minutes=15))
    end_dt = end_dt.mask((hours == 13) & (mins == 15), dt.dt.normalize() + pd.Timedelta(hours=15, minutes=30))
    completed_mask = end_dt <= pd.Timestamp(now_ist)
    out = df.loc[completed_mask].copy()
    out["datetime"] = dt.loc[completed_mask]
    return out.reset_index(drop=True)


def merge_with_existing_and_trim(existing_file: Path, new_bars: pd.DataFrame, keep_last: int = 60) -> pd.DataFrame:
    cols = ["datetime", "open", "high", "low", "close", "volume"]
    frames: list[pd.DataFrame] = []
    if existing_file.exists():
        old = pd.read_parquet(existing_file)
        old = old[cols].copy()
        old["datetime"] = pd.to_datetime(old["datetime"], errors="coerce", utc=True).dt.tz_convert(IST)
        frames.append(old)
    if not new_bars.empty:
        n = new_bars[cols].copy()
        n["datetime"] = pd.to_datetime(n["datetime"], errors="coerce")
        if n["datetime"].dt.tz is None:
            n["datetime"] = n["datetime"].dt.tz_localize(IST)
        else:
            n["datetime"] = n["datetime"].dt.tz_convert(IST)
        frames.append(n)

    if not frames:
        return pd.DataFrame(columns=cols)

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["datetime"]).sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")
    out = out.tail(keep_last).reset_index(drop=True)
    return out[cols]


def save_symbol_2h_parquet(symbol: str, bars: pd.DataFrame) -> Path:
    LIVE_2H_DIR.mkdir(parents=True, exist_ok=True)
    out_file = LIVE_2H_DIR / f"{symbol}.parquet"
    # Store naive timestamp for compatibility with current candidate loader.
    to_save = bars.copy()
    to_save["datetime"] = pd.to_datetime(to_save["datetime"], errors="coerce").dt.tz_convert(IST).dt.tz_localize(None)
    to_save.to_parquet(out_file, index=False)
    return out_file


def append_update_log(rows: list[UpdateResult]) -> None:
    if not rows:
        return
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        [
            {
                "timestamp": r.timestamp,
                "symbol": r.symbol,
                "bars_saved": r.bars_saved,
                "latest_close": r.latest_close,
                "status": r.status,
                "error": r.error,
            }
            for r in rows
        ]
    )
    if LOG_FILE.exists():
        old = pd.read_csv(LOG_FILE)
        out = pd.concat([old, df], ignore_index=True)
    else:
        out = df
    out.to_csv(LOG_FILE, index=False)


class ThreadSafeCounter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.success = 0
        self.failed = 0

    def mark_success(self) -> None:
        with self._lock:
            self.success += 1

    def mark_failed(self) -> None:
        with self._lock:
            self.failed += 1
