from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


class CandleStorage:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_KEY", "")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY are required."
            )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
        )

    def save_symbol_candles(
        self,
        symbol: str,
        candles: pd.DataFrame,
    ) -> None:

        if candles.empty:
            return

        candles = candles.tail(60).copy()

        delete_url = (
            f"{self.url}/rest/v1/market_candles_2h"
            f"?symbol=eq.{symbol}"
        )

        delete_resp = self.session.delete(
            delete_url,
            timeout=30,
        )

        delete_resp.raise_for_status()

        rows: list[dict[str, Any]] = []

        for _, row in candles.iterrows():

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

        insert_url = (
            f"{self.url}/rest/v1/market_candles_2h"
        )

        insert_resp = self.session.post(
            insert_url,
            json=rows,
            timeout=60,
        )

        insert_resp.raise_for_status()

        print(
            f"Saved {len(rows)} candles for {symbol}"
                  )
