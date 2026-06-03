from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from paper_trading.live_candidate_engine import CandidateEngineConfig, LiveCandidateEngine
from paper_trading.portfolio_engine import PortfolioEngine, PortfolioEngineConfig
from paper_trading.rl_exit_engine import RLExitEngine
from paper_trading.rotation_engine import RotationEngine


def _write_sample_hourly_parquet(path: Path, symbol: str) -> None:
    dt = pd.date_range("2026-01-01 09:15:00", periods=240, freq="h")
    df = pd.DataFrame(
        {
            "datetime": dt,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": [100 + (i * 0.05) for i in range(len(dt))],
            "volume": 1000,
        }
    )
    df.to_parquet(path / f"{symbol}.parquet", index=False)


def run_smoke() -> None:
    with TemporaryDirectory() as td:
        root = Path(td)
        hourly = root / "hourly"
        logs = root / "logs"
        hourly.mkdir(parents=True, exist_ok=True)
        logs.mkdir(parents=True, exist_ok=True)

        _write_sample_hourly_parquet(hourly, "360ONE-EQ")
        _write_sample_hourly_parquet(hourly, "3MINDIA-EQ")
        _write_sample_hourly_parquet(hourly, "AADHARHFC-EQ")
        _write_sample_hourly_parquet(hourly, "AARTIIND-EQ")

        cands_file = logs / "live_candidates.csv"
        candidates = LiveCandidateEngine(
            CandidateEngineConfig(hourly_data_dir=hourly, output_file=cands_file)
        ).generate_candidates()
        assert not candidates.empty

        portfolio_file = root / "current_portfolio.csv"
        portfolio = PortfolioEngine(
            PortfolioEngineConfig(candidates_file=cands_file, portfolio_file=portfolio_file)
        ).update_from_candidates(candidates)
        assert "status" in portfolio.columns

        open_positions = portfolio[portfolio["status"] == "OPEN"].copy()
        rl = RLExitEngine()
        decisions = rl.decide(open_positions, candidates)
        assert set(decisions.columns) >= {"symbol", "decision"}

        rotated, rotation_log = RotationEngine().evaluate_and_rotate(portfolio, candidates)
        assert isinstance(rotated, pd.DataFrame)
        assert isinstance(rotation_log, pd.DataFrame)


if __name__ == "__main__":
    run_smoke()
    print("Smoke test passed.")

