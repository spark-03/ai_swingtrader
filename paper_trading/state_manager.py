from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from paper_trading.retry_utils import retry_call
from paper_trading.supabase_logger import SupabaseLogger

PORTFOLIO_COLUMNS = [
    "symbol",
    "entry_timestamp",
    "entry_price",
    "quantity",
    "slot_id",
    "slot_capital",
    "pqs",
    "status",
]


@dataclass
class StateManager:
    last_processed_slot_file: Path = Path("logs/last_processed_slot.txt")
    backup_dir: Path = Path("logs/state_backups")
    retry_attempts: int = 3

    def __post_init__(self) -> None:
        self.last_processed_slot_file = Path(self.last_processed_slot_file)
        self.backup_dir = Path(self.backup_dir)
        self.last_processed_slot_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.last_processed_slot_file.exists():
            self.save_last_processed_slot("", create_backup=False)

    def _timestamp_suffix(self) -> str:
        return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

    def _backup_file(self, path: Path, reason: str = "bak") -> Path | None:
        if not path.exists() or path.stat().st_size == 0:
            return None

        backup_path = self.backup_dir / f"{path.name}.{reason}.{self._timestamp_suffix()}"
        shutil.copy2(path, backup_path)
        return backup_path

    def _atomic_write_text(self, path: Path, text: str) -> None:
        def write_once() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_name(f".{path.name}.{self._timestamp_suffix()}.tmp")
            tmp_path.write_text(text, encoding="utf-8")
            tmp_path.replace(path)

        retry_call(write_once, attempts=self.retry_attempts, retry_exceptions=(OSError,))

    def load_portfolio(self) -> pd.DataFrame:
        try:
            supabase_logger = SupabaseLogger()
            
            def fetch_data():
                resp = supabase_logger.session.get(
                    f"{supabase_logger.config.url}/rest/v1/current_portfolio?select=*"
                )
                resp.raise_for_status()
                return resp.json()

            data = retry_call(fetch_data, attempts=self.retry_attempts, retry_exceptions=(Exception,))
            
            if not data:
                return pd.DataFrame(columns=PORTFOLIO_COLUMNS)

            portfolio = pd.DataFrame(data)
            
            # Ensure all target columns exist in the DataFrame
            for column in PORTFOLIO_COLUMNS:
                if column not in portfolio.columns:
                    portfolio[column] = pd.NA
                    
            # Reorder columns to align with expected portfolio specifications
            return portfolio[PORTFOLIO_COLUMNS]
            
        except Exception:
            return pd.DataFrame(columns=PORTFOLIO_COLUMNS)

    def save_portfolio(self, portfolio: pd.DataFrame, *, create_backup: bool = True) -> None:
        supabase_logger = SupabaseLogger()

        def sync_db() -> None:
            # 1. Purge existing portfolio table records
            delete_resp = supabase_logger.session.delete(
                f"{supabase_logger.config.url}/rest/v1/current_portfolio?id=gt.0"
            )
            delete_resp.raise_for_status()

            # 2. Bulk insert active dataframe records if not empty
            if not portfolio.empty:
                # Convert DataFrame rows into clean dict payloads
                payload_rows = []
                for _, row in portfolio.iterrows():
                    payload_rows.append({
                        "symbol": str(row["symbol"]),
                        "entry_timestamp": pd.Timestamp(row["entry_timestamp"]).isoformat() if pd.notna(row["entry_timestamp"]) else None,
                        "entry_price": float(row["entry_price"]) if pd.notna(row["entry_price"]) else 0.0,
                        "quantity": int(row["quantity"]) if pd.notna(row["quantity"]) else 0,
                        "slot_id": int(row["slot_id"]) if pd.notna(row["slot_id"]) else 0,
                        "slot_capital": float(row["slot_capital"]) if pd.notna(row["slot_capital"]) else 0.0,
                        "pqs": float(row["pqs"]) if pd.notna(row["pqs"]) else 0.0,
                        "status": str(row["status"]),
                    })

                insert_resp = supabase_logger.session.post(
                    f"{supabase_logger.config.url}/rest/v1/current_portfolio",
                    json=payload_rows
                )
                insert_resp.raise_for_status()

        retry_call(sync_db, attempts=self.retry_attempts, retry_exceptions=(Exception,))

    def load_last_processed_slot(self) -> str | None:
        try:
            if not self.last_processed_slot_file.exists():
                self.save_last_processed_slot("", create_backup=False)
                return None

            slot = self.last_processed_slot_file.read_text(encoding="utf-8").strip()
            return slot or None
        except Exception:
            self._backup_file(self.last_processed_slot_file, reason="corrupt")
            self.save_last_processed_slot("", create_backup=False)
            return None

    def save_last_processed_slot(self, slot: str, *, create_backup: bool = True) -> None:
        if create_backup:
            self._backup_file(self.last_processed_slot_file)
        body = f"{slot.strip()}\n" if slot.strip() else ""
        self._atomic_write_text(self.last_processed_slot_file, body)
