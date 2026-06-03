

from dataclasses import dataclass
from typing import Any

import os
import requests
import pandas as pd
from dotenv import load_dotenv

from paper_trading.logging_config import get_system_logger
from paper_trading.retry_utils import retry_call

load_dotenv()

@dataclass
class SupabaseConfig:
url: str
key: str

```
@classmethod
def from_env(cls) -> "SupabaseConfig":
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are required.")

    return cls(
        url=url.rstrip("/"),
        key=key,
    )
```

class SupabaseLogger:
def **init**(
self,
config: SupabaseConfig | None = None,
) -> None:

```
    self.config = config or SupabaseConfig.from_env()

    self.logger = get_system_logger(
        "paper_trading.supabase"
    )

    self.session = requests.Session()

    self.session.headers.update(
        {
            "apikey": self.config.key,
            "Authorization": f"Bearer {self.config.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
    )

def _insert_rows(
    self,
    table: str,
    rows: list[dict[str, Any]],
) -> None:

    if not rows:
        return

    endpoint = f"{self.config.url}/rest/v1/{table}"

    def insert_once() -> None:
        resp = self.session.post(
            endpoint,
            json=rows,
            timeout=20,
        )
        resp.raise_for_status()

    retry_call(
        insert_once,
        attempts=int(
            os.getenv(
                "SUPABASE_MAX_RETRIES",
                "3",
            )
        ),
        initial_delay=float(
            os.getenv(
                "SUPABASE_RETRY_INITIAL_DELAY",
                "1.0",
            )
        ),
        backoff=float(
            os.getenv(
                "SUPABASE_RETRY_BACKOFF",
                "2.0",
            )
        ),
        retry_exceptions=(
            requests.RequestException,
        ),
    )

    self.logger.info(
        "Supabase insert table=%s rows=%s",
        table,
        len(rows),
    )

def log_paper_trades(
    self,
    rows: list[dict[str, Any]],
) -> None:
    self._insert_rows(
        "paper_trades",
        rows,
    )

def log_portfolio_snapshots(
    self,
    rows: list[dict[str, Any]],
) -> None:
    self._insert_rows(
        "portfolio_snapshots",
        rows,
    )

def log_rotation(
    self,
    rows: list[dict[str, Any]],
) -> None:
    self._insert_rows(
        "rotation_log",
        rows,
    )

def log_pqs_rankings(
    self,
    rows: list[dict[str, Any]],
) -> None:
    self._insert_rows(
        "pqs_rankings",
        rows,
    )

def log_open_positions(
    self,
    rows: list[dict[str, Any]],
) -> None:
    self._insert_rows(
        "open_positions",
        rows,
    )

def upsert_market_candles(
    self,
    symbol: str,
    candles_df: pd.DataFrame,
) -> None:

    if candles_df.empty:
        return

    delete_resp = self.session.delete(
        f"{self.config.url}/rest/v1/market_candles_2h?symbol=eq.{symbol}",
        timeout=30,
    )

    delete_resp.raise_for_status()

    rows = []

    for _, row in candles_df.iterrows():

        rows.append(
            {
                "symbol": symbol,
                "candle_time": pd.Timestamp(
                    row["datetime"]
                ).isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            }
        )

    self._insert_rows(
        "market_candles_2h",
        rows,
    )
```
