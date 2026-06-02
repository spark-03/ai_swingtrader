from __future__ import annotations

import pandas as pd

from paper_trading.state_manager import PORTFOLIO_COLUMNS, StateManager


def test_state_manager_creates_missing_files(tmp_path):
    state = StateManager(
        portfolio_file=tmp_path / "current_portfolio.csv",
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )

    assert state.portfolio_file.exists()
    assert state.last_processed_slot_file.exists()
    assert list(state.load_portfolio().columns) == PORTFOLIO_COLUMNS
    assert state.load_last_processed_slot() is None


def test_state_manager_atomic_slot_roundtrip(tmp_path):
    state = StateManager(
        portfolio_file=tmp_path / "current_portfolio.csv",
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )

    state.save_last_processed_slot("2026-06-01 11")

    assert state.load_last_processed_slot() == "2026-06-01 11"


def test_state_manager_recovers_corrupt_portfolio(tmp_path):
    portfolio_file = tmp_path / "current_portfolio.csv"
    portfolio_file.write_text("not,a,valid\ncsv-without-required-columns", encoding="utf-8")
    state = StateManager(
        portfolio_file=portfolio_file,
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )

    portfolio = state.load_portfolio()

    assert set(PORTFOLIO_COLUMNS).issubset(portfolio.columns)


def test_state_manager_saves_portfolio(tmp_path):
    state = StateManager(
        portfolio_file=tmp_path / "current_portfolio.csv",
        last_processed_slot_file=tmp_path / "logs" / "last_processed_slot.txt",
    )
    portfolio = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "entry_timestamp": "2026-06-01T09:15:00",
                "entry_price": 100,
                "quantity": 10,
                "slot_id": 1,
                "slot_capital": 1000,
                "pqs": 1.2,
                "status": "OPEN",
            }
        ]
    )

    state.save_portfolio(portfolio)

    loaded = state.load_portfolio()
    assert loaded.loc[0, "symbol"] == "AAA"
