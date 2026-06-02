from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from paper_trading import market_scheduler
from paper_trading.state_manager import StateManager


IST = ZoneInfo("Asia/Kolkata")


def _write_candle_file(path: Path, timestamps: list[str]) -> None:
    df = pd.DataFrame(
        {
            "datetime": pd.to_datetime(timestamps),
            "open": [1.0] * len(timestamps),
            "high": [1.0] * len(timestamps),
            "low": [1.0] * len(timestamps),
            "close": [1.0] * len(timestamps),
            "volume": [100.0] * len(timestamps),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_latest_available_candle_timestamp(tmp_path):
    data_dir = tmp_path / "data" / "live" / "2h"
    _write_candle_file(data_dir / "AAA.parquet", ["2026-06-01 09:15", "2026-06-01 11:15"])
    _write_candle_file(data_dir / "BBB.parquet", ["2026-06-01 09:15", "2026-06-01 13:15"])

    availability = market_scheduler.get_latest_available_candle_timestamp(data_dir)

    assert availability.slot_key == "2026-06-01 13"
    assert availability.scanned_files == 2
    assert availability.readable_files == 2


def test_scheduler_updates_slot_only_after_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data" / "live" / "2h"
    _write_candle_file(data_dir / "AAA.parquet", ["2026-06-01 09:15"])
    state = StateManager(
        portfolio_file=tmp_path / "current_portfolio.csv",
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )

    monkeypatch.setattr(market_scheduler, "get_current_time", lambda: datetime(2026, 6, 1, 9, 15, tzinfo=IST))
    monkeypatch.setattr(market_scheduler, "run_cycle", lambda slot=None: None)

    market_scheduler.process_scheduler_tick(state_manager=state, data_dir=data_dir)

    assert state.load_last_processed_slot() == "2026-06-01 09"


def test_scheduler_does_not_update_slot_after_failed_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data" / "live" / "2h"
    _write_candle_file(data_dir / "AAA.parquet", ["2026-06-01 09:15"])
    state = StateManager(
        portfolio_file=tmp_path / "current_portfolio.csv",
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )

    def fail_cycle(slot=None) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(market_scheduler, "get_current_time", lambda: datetime(2026, 6, 1, 9, 15, tzinfo=IST))
    monkeypatch.setattr(market_scheduler, "run_cycle", fail_cycle)

    market_scheduler.process_scheduler_tick(state_manager=state, data_dir=data_dir)

    assert state.load_last_processed_slot() is None


def test_scheduler_skips_duplicate_slot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data" / "live" / "2h"
    _write_candle_file(data_dir / "AAA.parquet", ["2026-06-01 11:15"])
    state = StateManager(
        portfolio_file=tmp_path / "current_portfolio.csv",
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )
    state.save_last_processed_slot("2026-06-01 11")
    calls = {"count": 0}

    def run_cycle(slot=None) -> None:
        calls["count"] += 1

    monkeypatch.setattr(market_scheduler, "get_current_time", lambda: datetime(2026, 6, 1, 11, 15, tzinfo=IST))
    monkeypatch.setattr(market_scheduler, "run_cycle", run_cycle)

    market_scheduler.process_scheduler_tick(state_manager=state, data_dir=data_dir)

    assert calls["count"] == 0
