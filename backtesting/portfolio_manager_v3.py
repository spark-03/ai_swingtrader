import heapq
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# ======================================
# CONFIGURATION
# ======================================
INITIAL_CAPITAL = 1_000_000.0
HOLDING_BARS = 80

SLOTS = {
    1: 500_000.0,
    2: 300_000.0,
    3: 200_000.0,
}

INPUT_TQS_FILE = Path("logs/tqs_live_v1_ranked.csv")
INPUT_LIFECYCLE_FILE = Path("logs/trade_lifecycle_research.csv")
OUTPUT_TRADES_FILE = Path("logs/portfolio_manager_v3_trades.csv")
OUTPUT_EQUITY_FILE = Path("logs/portfolio_manager_v3_equity.csv")


@dataclass
class Position:
    """Represents one open position occupying exactly one capital slot."""

    trade_id: int
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    slot_id: int
    capital_allocated: float
    tqs_live: float
    return_pct: float


def load_inputs() -> pd.DataFrame:
    """Load and validate trade candidates used by the portfolio engine."""
    tqs = pd.read_csv(INPUT_TQS_FILE)
    lifecycle = pd.read_csv(INPUT_LIFECYCLE_FILE)

    required_tqs_cols = {
        "trade_id",
        "symbol",
        "entry_date",
        "tqs_live",
        "final_return_80",
    }
    required_lifecycle_cols = {
        "trade_id",
        "symbol",
        "entry_date",
        "final_return_80",
    }

    missing_tqs = required_tqs_cols - set(tqs.columns)
    missing_lifecycle = required_lifecycle_cols - set(lifecycle.columns)

    if missing_tqs:
        raise ValueError(f"Missing columns in {INPUT_TQS_FILE}: {sorted(missing_tqs)}")
    if missing_lifecycle:
        raise ValueError(
            f"Missing columns in {INPUT_LIFECYCLE_FILE}: {sorted(missing_lifecycle)}"
        )

    tqs["entry_date"] = pd.to_datetime(tqs["entry_date"], utc=False)
    lifecycle["entry_date"] = pd.to_datetime(lifecycle["entry_date"], utc=False)

    # Merge lifecycle only as a consistency check / fallback reference.
    merged = tqs.merge(
        lifecycle[["trade_id", "symbol", "entry_date", "final_return_80"]].rename(
            columns={"final_return_80": "lifecycle_final_return_80"}
        ),
        on=["trade_id", "symbol", "entry_date"],
        how="left",
    )

    # If ranked file has missing returns, fill from lifecycle where available.
    missing_returns = merged["final_return_80"].isna()
    merged.loc[missing_returns, "final_return_80"] = merged.loc[
        missing_returns, "lifecycle_final_return_80"
    ]

    # Drop rows still missing essential values.
    merged = merged.dropna(subset=["entry_date", "tqs_live", "final_return_80"]).copy()

    # Ensure deterministic order for tie-breaking.
    merged = merged.sort_values(
        ["entry_date", "tqs_live", "trade_id"],
        ascending=[True, False, True],
    ).reset_index(drop=True)

    return merged


def build_bar_calendar(df: pd.DataFrame) -> tuple[list[pd.Timestamp], pd.Timedelta]:
    """
    Build global bar timestamp calendar from observed entry timestamps.

    Assumption:
    - Entry timestamps represent valid tradable bar timestamps.
    - 80-bar exits are computed via this observed calendar.
    - If future bars are unavailable near dataset end, we extend using median bar interval.
    """
    bar_times = sorted(df["entry_date"].dropna().unique().tolist())
    if len(bar_times) < 2:
        raise ValueError("Need at least 2 unique timestamps to infer bar interval.")

    deltas = pd.Series(bar_times).diff().dropna()
    median_delta = deltas.median()

    if pd.isna(median_delta) or median_delta <= pd.Timedelta(0):
        raise ValueError("Unable to infer a positive median bar interval.")

    return bar_times, median_delta


def compute_exit_date(
    entry_dt: pd.Timestamp,
    bar_times: list[pd.Timestamp],
    bar_index_map: dict[pd.Timestamp, int],
    median_delta: pd.Timedelta,
) -> pd.Timestamp:
    """
    Compute exit timestamp as exactly 80 bars after entry.

    Uses observed bar timestamps when available; otherwise extends synthetically
    using the inferred median bar interval.
    """
    idx = bar_index_map[entry_dt]
    target_idx = idx + HOLDING_BARS

    if target_idx < len(bar_times):
        return bar_times[target_idx]

    overflow = target_idx - (len(bar_times) - 1)
    return bar_times[-1] + overflow * median_delta


def max_drawdown_pct(equity_series: pd.Series) -> float:
    if equity_series.empty:
        return 0.0
    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max
    return float(drawdown.min() * 100.0)


def run_portfolio_engine(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    bar_times, median_delta = build_bar_calendar(df)
    bar_index_map = {dt: i for i, dt in enumerate(bar_times)}

    df = df.copy()
    df["exit_date"] = df["entry_date"].apply(
        lambda x: compute_exit_date(x, bar_times, bar_index_map, median_delta)
    )

    entries_by_time: dict[pd.Timestamp, pd.DataFrame] = {
        dt: grp.copy()
        for dt, grp in df.groupby("entry_date", sort=True)
    }

    all_event_times = sorted(set(df["entry_date"]).union(set(df["exit_date"])))

    free_slots: dict[int, float] = dict(SLOTS)
    open_positions: dict[int, Position] = {}

    # Min-heap of (exit_date, slot_id) so we can close positions efficiently.
    exit_heap: list[tuple[pd.Timestamp, int]] = []

    realized_pnl = 0.0
    closed_trades: list[dict] = []
    equity_rows: list[dict] = []

    weighted_concurrency_sum = 0.0
    weighted_utilization_sum = 0.0
    total_time_steps = 0

    for current_time in all_event_times:
        # STEP 1: Close any positions with exit_date <= current_time.
        while exit_heap and exit_heap[0][0] <= current_time:
            _, slot_id = heapq.heappop(exit_heap)
            if slot_id not in open_positions:
                # Safety guard for stale heap entries.
                continue

            pos = open_positions.pop(slot_id)
            pnl = pos.capital_allocated * (pos.return_pct / 100.0)
            realized_pnl += pnl

            # Capital is now unlocked and reusable by this same timestamp.
            free_slots[slot_id] = SLOTS[slot_id]

            closed_trades.append(
                {
                    "entry_date": pos.entry_date,
                    "exit_date": pos.exit_date,
                    "trade_id": pos.trade_id,
                    "symbol": pos.symbol,
                    "slot_id": pos.slot_id,
                    "capital_allocated": pos.capital_allocated,
                    "tqs_live": pos.tqs_live,
                    "return_pct": pos.return_pct,
                    "pnl": pnl,
                }
            )

        # STEP 2: Fetch new candidate entries at current timestamp.
        candidates = entries_by_time.get(current_time)

        # STEP 3/4: Rank by TQS descending, then fill only empty slots.
        if candidates is not None and free_slots:
            ranked_candidates = candidates.sort_values(
                ["tqs_live", "trade_id"], ascending=[False, True]
            )

            # Highest TQS gets the largest currently available slot.
            available_slot_ids = sorted(
                free_slots.keys(), key=lambda sid: free_slots[sid], reverse=True
            )

            max_new_positions = min(len(available_slot_ids), len(ranked_candidates))

            for i in range(max_new_positions):
                row = ranked_candidates.iloc[i]
                slot_id = available_slot_ids[i]
                allocated_capital = free_slots.pop(slot_id)

                pos = Position(
                    trade_id=int(row["trade_id"]),
                    symbol=str(row["symbol"]),
                    entry_date=row["entry_date"],
                    exit_date=row["exit_date"],
                    slot_id=slot_id,
                    capital_allocated=float(allocated_capital),
                    tqs_live=float(row["tqs_live"]),
                    return_pct=float(row["final_return_80"]),
                )

                open_positions[slot_id] = pos
                heapq.heappush(exit_heap, (pos.exit_date, slot_id))

        # Equity excludes unrealized PnL (benchmark exit known only at close),
        # so it is cash-equivalent principal plus realized PnL only.
        deployed_capital = sum(pos.capital_allocated for pos in open_positions.values())
        free_capital = sum(free_slots.values())
        total_equity = INITIAL_CAPITAL + realized_pnl

        equity_rows.append(
            {
                "timestamp": current_time,
                "equity": total_equity,
                "realized_pnl": realized_pnl,
                "deployed_capital": deployed_capital,
                "free_capital": free_capital,
                "open_positions": len(open_positions),
                "capital_utilization_pct": (deployed_capital / INITIAL_CAPITAL) * 100.0,
            }
        )

        weighted_concurrency_sum += len(open_positions)
        weighted_utilization_sum += (deployed_capital / INITIAL_CAPITAL) * 100.0
        total_time_steps += 1

    trades_df = pd.DataFrame(closed_trades).sort_values(
        ["entry_date", "slot_id", "trade_id"]
    )
    equity_df = pd.DataFrame(equity_rows).sort_values("timestamp")

    final_equity = (
        float(equity_df["equity"].iloc[-1]) if not equity_df.empty else INITIAL_CAPITAL
    )
    total_return_pct = ((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0

    if trades_df.empty:
        win_rate = 0.0
        avg_trade_return = 0.0
        median_trade_return = 0.0
        profit_factor = 0.0
    else:
        wins = trades_df[trades_df["pnl"] > 0.0]
        losses = trades_df[trades_df["pnl"] < 0.0]

        win_rate = float((trades_df["return_pct"] > 0).mean() * 100.0)
        avg_trade_return = float(trades_df["return_pct"].mean())
        median_trade_return = float(trades_df["return_pct"].median())

        gross_profit = float(wins["pnl"].sum())
        gross_loss_abs = float(abs(losses["pnl"].sum()))
        profit_factor = np.inf if gross_loss_abs == 0 else gross_profit / gross_loss_abs

    summary = {
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "total_trades": int(len(trades_df)),
        "win_rate_pct": win_rate,
        "average_trade_return_pct": avg_trade_return,
        "median_trade_return_pct": median_trade_return,
        "profit_factor": float(profit_factor),
        "max_drawdown_pct": max_drawdown_pct(equity_df["equity"]),
        "average_concurrent_positions": (
            weighted_concurrency_sum / total_time_steps if total_time_steps else 0.0
        ),
        "capital_utilization_pct": (
            weighted_utilization_sum / total_time_steps if total_time_steps else 0.0
        ),
        "bar_interval_assumption": (
            "Exit is 80 bars after entry using observed global bar timestamps from "
            f"input entry_date values; if insufficient future timestamps exist, "
            f"synthetic extension uses median bar interval = {median_delta}."
        ),
    }

    return trades_df, equity_df, summary


def main() -> None:
    print("Loading inputs...")
    candidates = load_inputs()

    print("Running Portfolio Manager V3 event-driven simulation...")
    trades_df, equity_df, summary = run_portfolio_engine(candidates)

    OUTPUT_TRADES_FILE.parent.mkdir(parents=True, exist_ok=True)
    trades_df.to_csv(OUTPUT_TRADES_FILE, index=False)
    equity_df.to_csv(OUTPUT_EQUITY_FILE, index=False)

    print("\n=== PORTFOLIO MANAGER V3 (CAPITAL-AWARE) ===\n")
    print(f"Initial Capital: {summary['initial_capital']:,.2f}")
    print(f"Final Equity: {summary['final_equity']:,.2f}")
    print(f"Total Return %: {summary['total_return_pct']:.2f}")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate_pct']:.2f}")
    print(f"Average Trade Return: {summary['average_trade_return_pct']:.2f}")
    print(f"Median Trade Return: {summary['median_trade_return_pct']:.2f}")
    print(f"Profit Factor: {summary['profit_factor']:.4f}")
    print(f"Max Drawdown %: {summary['max_drawdown_pct']:.2f}")
    print(
        "Average Concurrent Positions: "
        f"{summary['average_concurrent_positions']:.4f}"
    )
    print(f"Capital Utilization %: {summary['capital_utilization_pct']:.2f}")

    print("\nAssumption:")
    print(summary["bar_interval_assumption"])

    print("\nSaved:")
    print(str(OUTPUT_TRADES_FILE))
    print(str(OUTPUT_EQUITY_FILE))


if __name__ == "__main__":
    main()
