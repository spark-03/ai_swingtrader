from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class SupabaseConfig:
    url: str
    key: str

    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_KEY", "").strip()
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required.")
        return cls(url=url.rstrip("/"), key=key)


class SupabaseLogger:
    def __init__(self, config: SupabaseConfig | None = None) -> None:
        self.config = config or SupabaseConfig.from_env()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "apikey": self.config.key,
                "Authorization": f"Bearer {self.config.key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
        )

    def _insert_rows(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        endpoint = f"{self.config.url}/rest/v1/{table}"
        resp = self.session.post(endpoint, json=rows, timeout=20)
        resp.raise_for_status()

    def log_paper_trades(self, rows: list[dict[str, Any]]) -> None:
        self._insert_rows("paper_trades", rows)

    def log_portfolio_snapshots(self, rows: list[dict[str, Any]]) -> None:
        self._insert_rows("portfolio_snapshots", rows)

    def log_rotation(self, rows: list[dict[str, Any]]) -> None:
        self._insert_rows("rotation_log", rows)

