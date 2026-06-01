import numpy as np
import pandas as pd
from typing import Dict


def compute_portfolio_metrics(trades: pd.DataFrame, equity: pd.DataFrame, initial_capital: float) -> Dict[str, float]:
    """Compute requested performance metrics from trade/equity logs."""
    closed = trades.copy()

    total_trades = int(len(closed))
    returns = closed["return_pct"].dropna() if total_trades else pd.Series(dtype=float)

    wins = closed[closed["pnl"] > 0] if total_trades else closed
    losses = closed[closed["pnl"] < 0] if total_trades else closed

    win_rate = float((len(wins) / total_trades) * 100.0) if total_trades else 0.0
    avg_trade_return = float(returns.mean() * 100.0) if not returns.empty else 0.0
    median_trade_return = float(returns.median() * 100.0) if not returns.empty else 0.0

    gross_profit = float(wins["pnl"].sum()) if not wins.empty else 0.0
    gross_loss = float(losses["pnl"].sum()) if not losses.empty else 0.0

    if gross_loss == 0.0:
        profit_factor = np.inf if gross_profit > 0.0 else 0.0
    else:
        profit_factor = gross_profit / abs(gross_loss)

    equity_series = equity["equity"].astype(float)
    running_peak = equity_series.cummax()
    drawdown = ((equity_series / running_peak) - 1.0) * 100.0
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    final_equity = float(equity_series.iloc[-1]) if not equity_series.empty else float(initial_capital)
    total_return_pct = ((final_equity / float(initial_capital)) - 1.0) * 100.0

    return {
        "initial_capital": float(initial_capital),
        "final_equity": final_equity,
        "total_return_pct": float(total_return_pct),
        "total_trades": total_trades,
        "win_rate": float(win_rate),
        "average_trade_return_pct": float(avg_trade_return),
        "median_trade_return_pct": float(median_trade_return),
        "profit_factor": float(profit_factor) if np.isfinite(profit_factor) else np.inf,
        "max_drawdown_pct": float(max_drawdown),
    }


def print_metrics(metrics: Dict[str, float]) -> None:
    """Print metrics in requested format."""
    print("\n=== PORTFOLIO MANAGER V1 METRICS ===")
    print(f"Initial Capital: {metrics['initial_capital']:,.2f}")
    print(f"Final Equity: {metrics['final_equity']:,.2f}")
    print(f"Total Return %: {metrics['total_return_pct']:.2f}%")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2f}%")
    print(f"Average Trade Return: {metrics['average_trade_return_pct']:.2f}%")
    print(f"Median Trade Return: {metrics['median_trade_return_pct']:.2f}%")

    pf = metrics["profit_factor"]
    pf_str = "inf" if np.isinf(pf) else f"{pf:.4f}"
    print(f"Profit Factor: {pf_str}")
    print(f"Max Drawdown %: {metrics['max_drawdown_pct']:.2f}%")
