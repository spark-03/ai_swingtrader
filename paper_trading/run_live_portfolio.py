from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from paper_trading.live_candidate_engine import LiveCandidateEngine
from paper_trading.portfolio_engine import PortfolioEngine
from paper_trading.rl_exit_engine import RLExitEngine
from paper_trading.rotation_engine import RotationEngine
from paper_trading.supabase_logger import SupabaseLogger


def fetch_latest_market_data() -> None:
    # Placeholder: data refresh should be implemented via broker/API sync job.
    # This orchestrator assumes data/historical/hourly/*.parquet is continuously updated.
    return


def apply_rl_exits(portfolio_df: pd.DataFrame, decisions_df: pd.DataFrame) -> pd.DataFrame:
    print("portfolio_df.dtypes (before apply_rl_exits):")
    print(portfolio_df.dtypes)

    if portfolio_df.empty or decisions_df.empty:
        return portfolio_df

    portfolio_df = portfolio_df.copy()
    if "exit_timestamp" not in portfolio_df.columns:
        portfolio_df["exit_timestamp"] = pd.NaT

    portfolio_df["exit_timestamp"] = pd.to_datetime(
        portfolio_df["exit_timestamp"],
        utc=True,
        errors="coerce",
    )

    sells = set(decisions_df[decisions_df["decision"] == "SELL"]["symbol"].tolist())
    mask = (portfolio_df["status"] == "OPEN") & (portfolio_df["symbol"].isin(sells))
    portfolio_df.loc[mask, "status"] = "CLOSED_RL"
    portfolio_df.loc[mask, "close_reason"] = "rl_exit"
    portfolio_df.loc[mask, "exit_timestamp"] = pd.Timestamp.now("UTC")

    print('portfolio_df[["symbol","exit_timestamp"]].dtypes:')
    print(portfolio_df[["symbol", "exit_timestamp"]].dtypes)

    return portfolio_df


def build_snapshot(portfolio_df: pd.DataFrame) -> dict:
    now = pd.Timestamp.now("UTC")
    open_positions = portfolio_df[portfolio_df["status"] == "OPEN"].copy() if not portfolio_df.empty else pd.DataFrame()
    invested = float((open_positions["entry_price"] * open_positions["quantity"]).sum()) if not open_positions.empty else 0.0
    total_capital = 1_000_000.0
    cash = total_capital - invested
    equity = total_capital
    return {
        "timestamp": now.isoformat(),
        "cash": cash,
        "equity": equity,
        "positions": int(len(open_positions)),
        "daily_pnl": 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live paper trading cycle.")
    parser.add_argument("--dry-run", action="store_true", help="Skip Supabase writes.")
    args = parser.parse_args()

    fetch_latest_market_data()

    candidate_engine = LiveCandidateEngine()
    candidates = candidate_engine.generate_candidates()

    portfolio_engine = PortfolioEngine()
    portfolio = portfolio_engine.update_from_candidates(candidates)
    open_positions = portfolio[portfolio["status"] == "OPEN"].copy() if not portfolio.empty else pd.DataFrame()

    rl_engine = RLExitEngine()
    exit_decisions = rl_engine.decide(open_positions, candidates)
    portfolio = apply_rl_exits(portfolio, exit_decisions)

    open_positions = portfolio[portfolio["status"] == "OPEN"].copy() if not portfolio.empty else pd.DataFrame()
    free_slots = max(0, 3 - len(open_positions))
    buy_decisions = rl_engine.candidate_entries(open_positions, candidates, free_slots)

    rotation_engine = RotationEngine()
    portfolio, rotation_log = rotation_engine.evaluate_and_rotate(portfolio, candidates)
    portfolio.to_csv(Path("current_portfolio.csv"), index=False)

    snapshot = build_snapshot(portfolio)

    if not args.dry_run:
        logger = SupabaseLogger()
        trade_rows = []
        now = pd.Timestamp.now("UTC").isoformat()
        for _, r in pd.concat([exit_decisions, buy_decisions], ignore_index=True).iterrows():
            trade_rows.append(
                {
                    "timestamp": now,
                    "symbol": str(r["symbol"]),
                    "action": str(r["decision"]),
                    "price": 0.0,
                    "quantity": 0,
                    "tqs": 0.0,
                    "reason": str(r["reason"]),
                }
            )
        logger.log_paper_trades(trade_rows)
        logger.log_portfolio_snapshots([snapshot])
        if not rotation_log.empty:
            rows = []
            for _, row in rotation_log.iterrows():
                rows.append(
                    {
                        "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
                        "old_symbol": str(row["old_symbol"]),
                        "new_symbol": str(row["new_symbol"]),
                        "old_tqs": float(row["old_tqs"]),
                        "new_tqs": float(row["new_tqs"]),
                    }
                )
            logger.log_rotation(rows)

    print("Live cycle complete.")
    print(f"Candidates: {len(candidates)}")
    print(f"Exit decisions: {len(exit_decisions)}")
    print(f"Buy decisions: {len(buy_decisions)}")
    print("Saved: logs/live_candidates.csv")
    print("Saved: current_portfolio.csv")


if __name__ == "__main__":
    main()
