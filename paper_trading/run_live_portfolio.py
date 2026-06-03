from __future__ import annotations

import argparse
import time

import pandas as pd

from paper_trading.live_candidate_engine import LiveCandidateEngine
from paper_trading.logging_config import get_system_logger
from paper_trading.metrics import record_cycle_error, record_cycle_start, update_cycle_metrics
from paper_trading.portfolio_engine import PortfolioEngine
from paper_trading.rl_exit_engine import RLExitEngine
from paper_trading.rotation_engine import RotationEngine
from paper_trading.state_manager import StateManager
from paper_trading.supabase_logger import SupabaseLogger


def fetch_latest_market_data() -> None:
    # Placeholder: data refresh should be implemented via broker/API sync job.
    # This orchestrator assumes data/historical/hourly/*.parquet is continuously updated.
    return


def apply_rl_exits(portfolio_df: pd.DataFrame, decisions_df: pd.DataFrame) -> pd.DataFrame:
    if portfolio_df.empty or decisions_df.empty:
        return portfolio_df
    if "exit_timestamp" not in portfolio_df.columns:
        portfolio_df["exit_timestamp"] = pd.Series(dtype="object")

    if "close_reason" not in portfolio_df.columns:
        portfolio_df["close_reason"] = pd.Series(dtype="object")
    if "exit_price" not in portfolio_df.columns:
    portfolio_df["exit_price"] = pd.Series(dtype="float64")

    if "realized_pnl" not in portfolio_df.columns:
    portfolio_df["realized_pnl"] = pd.Series(dtype="float64")

    if "realized_pnl_pct" not in portfolio_df.columns:
    portfolio_df["realized_pnl_pct"] = pd.Series(dtype="float64")
    portfolio_df["exit_timestamp"] = portfolio_df["exit_timestamp"].astype("object")
    portfolio_df["close_reason"] = portfolio_df["close_reason"].astype("object")
    candidate_prices = (
    candidates_df[["symbol", "last_price"]]
    .drop_duplicates(subset=["symbol"])
    .set_index("symbol")["last_price"]
    .to_dict()
    )
    sells = set(decisions_df[decisions_df["decision"] == "SELL"]["symbol"].tolist())
    mask = (portfolio_df["status"] == "OPEN") & (portfolio_df["symbol"].isin(sells))
    
    portfolio_df.loc[mask, "status"] = "CLOSED_RL"
portfolio_df.loc[mask, "close_reason"] = "rl_exit"
portfolio_df.loc[mask, "exit_timestamp"] = pd.Timestamp.now("UTC").floor("s")

for idx in portfolio_df[mask].index:

    symbol = str(portfolio_df.at[idx, "symbol"])

    entry_price = float(
        portfolio_df.at[idx, "entry_price"]
    )

    quantity = int(
        portfolio_df.at[idx, "quantity"]
    )

    exit_price = float(
        candidate_prices.get(
            symbol,
            entry_price
        )
    )

    realized_pnl = (
        exit_price - entry_price
    ) * quantity

    realized_pnl_pct = (
        ((exit_price - entry_price) / entry_price) * 100
        if entry_price > 0
        else 0.0
    )

    portfolio_df.at[idx, "exit_price"] = exit_price
    portfolio_df.at[idx, "realized_pnl"] = realized_pnl
    portfolio_df.at[idx, "realized_pnl_pct"] = realized_pnl_pct

    return portfolio_df


def build_snapshot(
    portfolio_df: pd.DataFrame,
    candidates: pd.DataFrame,
    candidates_df: pd.DataFrame
) -> dict:

    now = pd.Timestamp.now("UTC")

    total_capital = 1_000_000.0

    open_positions = (
        portfolio_df[portfolio_df["status"] == "OPEN"].copy()
        if not portfolio_df.empty
        else pd.DataFrame()
    )

    if open_positions.empty:
        return {
            "timestamp": now.isoformat(),
            "cash": total_capital,
            "equity": total_capital,
            "positions": 0,
            "daily_pnl": 0.0,
        }

    candidate_prices = (
        candidates[["symbol", "last_price"]]
        .drop_duplicates(subset=["symbol"])
        .set_index("symbol")["last_price"]
        .to_dict()
    )

    invested = 0.0
    market_value = 0.0

    for _, row in open_positions.iterrows():

        entry_price = float(row["entry_price"])
        quantity = int(row["quantity"])

        invested += entry_price * quantity

        current_price = float(
            candidate_prices.get(
                str(row["symbol"]),
                entry_price,
            )
        )

        market_value += current_price * quantity

    unrealized_pnl = market_value - invested

    cash = total_capital - invested

    equity = cash + market_value

    return {
        "timestamp": now.isoformat(),
        "cash": cash,
        "equity": equity,
        "positions": int(len(open_positions)),
        "daily_pnl": unrealized_pnl,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live paper trading cycle.")
    parser.add_argument("--dry-run", action="store_true", help="Skip Supabase writes.")
    parser.add_argument("--slot", default=None, help="Processed candle slot in YYYY-MM-DD HH format.")
    args = parser.parse_args()
    logger = get_system_logger("paper_trading.live_cycle")
    state_manager = StateManager()
    cycle_started = time.monotonic()
    record_cycle_start()
    logger.info("Cycle start slot=%s dry_run=%s", args.slot, args.dry_run)
    
    try:
        fetch_latest_market_data()

        candidate_engine = LiveCandidateEngine()
        candidates = candidate_engine.generate_candidates()
        
        # Upload Top 100 PQS rankings to Supabase
        if not args.dry_run:
            supabase_logger = SupabaseLogger()

            # Clear previous rankings
            resp = supabase_logger.session.delete(
                f"{supabase_logger.config.url}/rest/v1/pqs_rankings?id=gt.0"
            )
            resp.raise_for_status()

            top_rankings = (
                candidates
                .sort_values("pqs", ascending=False)
                .head(100)
            )

            ranking_rows = []

            for idx, row in top_rankings.reset_index(drop=True).iterrows():
                ranking_rows.append(
                    {
                        "timestamp": pd.Timestamp.now("UTC").isoformat(),
                        "rank": idx + 1,
                        "symbol": str(row["symbol"]),
                        "pqs": float(row["pqs"]),
                        "last_price": float(row.get("last_price", 0.0)),
                    }
                )

            supabase_logger.log_pqs_rankings(ranking_rows)
        
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
        state_manager.save_portfolio(portfolio)
        
        if not args.dry_run:
            supabase_logger = SupabaseLogger()

            resp = supabase_logger.session.delete(
                f"{supabase_logger.config.url}/rest/v1/open_positions?id=gt.0"
            )
            resp.raise_for_status()

            candidate_prices = (
                candidates[["symbol", "last_price"]]
                .drop_duplicates(subset=["symbol"])
                .set_index("symbol")["last_price"]
                .to_dict()
            )

            open_positions_rows = []

            for _, row in portfolio[portfolio["status"] == "OPEN"].iterrows():
                symbol = str(row["symbol"])

                current_price = float(
                    candidate_prices.get(
                        symbol,
                        row["entry_price"]
                    )
                )

                entry_price = float(row["entry_price"])
                quantity = int(row["quantity"])

                cost_basis = entry_price * quantity
                market_value = current_price * quantity

                unrealized_pnl = market_value - cost_basis

                unrealized_pnl_pct = (
                    (unrealized_pnl / cost_basis) * 100
                    if cost_basis > 0
                    else 0.0
                )

                open_positions_rows.append(
                    {
                        "timestamp": pd.Timestamp.now("UTC").isoformat(),
                        "symbol": symbol,
                        "entry_timestamp": pd.Timestamp(
                            row["entry_timestamp"]
                        ).isoformat(),
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "slot_id": int(row["slot_id"]),
                        "slot_capital": float(row["slot_capital"]),
                        "pqs": float(row["pqs"]),
                        "status": str(row["status"]),
                        "current_price": current_price,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_pct": unrealized_pnl_pct,
                    }
                )

            supabase_logger.log_open_positions(open_positions_rows)

        rl_engine = RLExitEngine()
        exit_decisions = rl_engine.decide(open_positions, candidates)
        snapshot = build_snapshot(
          portfolio,
          candidates,
        )

        if not args.dry_run:
            supabase_logger = SupabaseLogger()
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
            supabase_logger.log_paper_trades(trade_rows)
            supabase_logger.log_portfolio_snapshots([snapshot])
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
                supabase_logger.log_rotation(rows)

        duration = time.monotonic() - cycle_started
        trades_executed = len(exit_decisions) + len(buy_decisions)
        exits_triggered = int((exit_decisions["decision"] == "SELL").sum()) if not exit_decisions.empty else 0
        rotations_triggered = len(rotation_log)
        update_cycle_metrics(
            portfolio=portfolio,
            trades_executed=trades_executed,
            exits_triggered=exits_triggered,
            rotations_triggered=rotations_triggered,
            cycle_duration_seconds=duration,
            last_processed_slot=args.slot,
        )
        logger.info(
            "Cycle completion slot=%s duration_seconds=%.3f candidates=%s exits=%s buys=%s rotations=%s",
            args.slot,
            duration,
            len(candidates),
            len(exit_decisions),
            len(buy_decisions),
            rotations_triggered,
        )

    except Exception as exc:
        record_cycle_error(str(exc))
        logger.exception("Cycle failed slot=%s", args.slot)
        raise

    print("Live cycle complete.")
    print(f"Candidates: {len(candidates)}")
    print(f"Exit decisions: {len(exit_decisions)}")
    print(f"Buy decisions: {len(buy_decisions)}")
    print("Saved: logs/live_candidates.csv")
    print("Saved: current_portfolio.csv")


if __name__ == "__main__":
    main()
