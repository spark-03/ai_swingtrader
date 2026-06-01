from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from metrics import compute_portfolio_metrics, print_metrics
from portfolio_utils import (
    build_state_v3_mask,
    calculate_position_value,
    compute_state_v3_thresholds,
    ensure_log_dir,
    load_feature_data,
    load_recovery_data,
    rank_candidates,
)

FEATURES_PATH = "data/features/2h/multi_stock_2h_features.parquet"
RECOVERY_PATH = "data/recovery/recovery_intelligence.csv"

TRADES_OUT = "logs/portfolio_manager_v1_trades.csv"
EQUITY_OUT = "logs/portfolio_manager_v1_equity.csv"

INITIAL_CAPITAL = 10_00_000.0
MAX_OPEN_POSITIONS = 3
ALLOC_WEIGHTS = [0.50, 0.30, 0.20]


@dataclass
class Position:
    symbol: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    capital_allocated: float


def _position_to_trade_row(pos: Position, exit_date: pd.Timestamp, exit_price: float, reason: str) -> dict:
    pnl = (float(exit_price) - pos.entry_price) * pos.shares
    ret = (float(exit_price) - pos.entry_price) / pos.entry_price
    return {
        "symbol": pos.symbol,
        "entry_date": pos.entry_date,
        "entry_price": pos.entry_price,
        "exit_date": exit_date,
        "exit_price": float(exit_price),
        "shares": pos.shares,
        "capital_allocated": pos.capital_allocated,
        "pnl": float(pnl),
        "return_pct": float(ret),
        "exit_reason": reason,
    }


def run_portfolio_manager_v1() -> None:
    features = load_feature_data(FEATURES_PATH)
    recovery = load_recovery_data(RECOVERY_PATH)

    thresholds = compute_state_v3_thresholds(features)
    features["is_state_v3"] = build_state_v3_mask(features, thresholds)

    open_positions: List[Position] = []
    trade_log: List[dict] = []
    equity_log: List[dict] = []
    last_close: Dict[str, float] = {}

    cash = float(INITIAL_CAPITAL)

    for ts, bar in features.groupby("date", sort=True):
        bar = bar.copy()
        bar_map = {row["symbol"]: row for _, row in bar.iterrows()}

        for _, row in bar.iterrows():
            last_close[row["symbol"]] = float(row["close"])

        still_open: List[Position] = []
        for pos in open_positions:
            row = bar_map.get(pos.symbol)
            should_exit = False
            if row is not None:
                should_exit = bool((row["momentum_score"] > 0) and (row["close"] > pos.entry_price))

            if should_exit:
                exit_price = float(row["close"])
                cash += pos.shares * exit_price
                trade_log.append(_position_to_trade_row(pos, ts, exit_price, "RECOVERY_EXIT"))
            else:
                still_open.append(pos)

        open_positions = still_open

        available_slots = MAX_OPEN_POSITIONS - len(open_positions)
        if available_slots > 0:
            candidates = bar[bar["is_state_v3"]].copy()
            if not candidates.empty:
                open_symbols = {p.symbol for p in open_positions}
                candidates = candidates[~candidates["symbol"].isin(open_symbols)]

                if not candidates.empty:
                    ranked = rank_candidates(candidates, recovery)
                    ranked = ranked.head(available_slots)

                    for idx, (_, row) in enumerate(ranked.iterrows()):
                        if idx >= len(ALLOC_WEIGHTS):
                            break

                        alloc = ALLOC_WEIGHTS[idx] * (cash + calculate_position_value(open_positions, last_close))
                        alloc = min(alloc, cash)

                        entry_price = float(row["close"])
                        shares = int(np.floor(alloc / entry_price)) if entry_price > 0 else 0

                        if shares <= 0:
                            continue

                        capital_used = shares * entry_price
                        cash -= capital_used

                        open_positions.append(
                            Position(
                                symbol=row["symbol"],
                                entry_date=ts,
                                entry_price=entry_price,
                                shares=shares,
                                capital_allocated=float(capital_used),
                            )
                        )

        position_value = calculate_position_value(open_positions, last_close)
        equity = cash + position_value

        equity_log.append(
            {
                "date": ts,
                "cash": float(cash),
                "position_value": float(position_value),
                "equity": float(equity),
                "open_positions": len(open_positions),
            }
        )

    final_date = features["date"].max()
    for pos in open_positions:
        mtm_price = float(last_close.get(pos.symbol, pos.entry_price))
        cash += pos.shares * mtm_price
        trade_log.append(_position_to_trade_row(pos, final_date, mtm_price, "MARK_TO_MARKET"))

    # Final snapshot after forced mark-to-market closure.
    equity_log.append(
        {
            "date": final_date,
            "cash": float(cash),
            "position_value": 0.0,
            "equity": float(cash),
            "open_positions": 0,
        }
    )

    trades_df = pd.DataFrame(trade_log)
    equity_df = pd.DataFrame(equity_log)

    if not trades_df.empty:
        trades_df = trades_df.sort_values(["entry_date", "symbol"]).reset_index(drop=True)
    if not equity_df.empty:
        equity_df = equity_df.sort_values("date").reset_index(drop=True)

    ensure_log_dir(TRADES_OUT)
    ensure_log_dir(EQUITY_OUT)

    trades_df.to_csv(TRADES_OUT, index=False)
    equity_df.to_csv(EQUITY_OUT, index=False)

    metrics = compute_portfolio_metrics(trades_df, equity_df, INITIAL_CAPITAL)

    print(f"Saved trades: {TRADES_OUT}")
    print(f"Saved equity: {EQUITY_OUT}")
    print_metrics(metrics)


if __name__ == "__main__":
    run_portfolio_manager_v1()
