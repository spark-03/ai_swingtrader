
import argparse
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.load_historical_data import load_historical_data
try:
    from backtesting.backtester import run_backtest
except Exception:
    run_backtest = None


def _safe_profit_factor(group_df: pd.DataFrame) -> float:
    profit = group_df.loc[group_df["pnl"] > 0, "pnl"].sum()
    loss = -group_df.loc[group_df["pnl"] < 0, "pnl"].sum()
    if loss <= 0:
        return float("inf") if profit > 0 else 0.0
    return float(profit / loss)


def _bucket_confidence(series: pd.Series) -> pd.Series:
    bins = [0, 20, 40, 60, 80, 100]
    labels = ["00-20", "21-40", "41-60", "61-80", "81-100"]
    clipped = series.clip(lower=0, upper=100)
    return pd.cut(clipped, bins=bins, labels=labels, include_lowest=True)


def _enrich_trades(trades_df: pd.DataFrame) -> pd.DataFrame:
    df = trades_df.copy()

    if "confidence" not in df.columns:
        df["confidence"] = 0.0
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)

    if "market_regime" not in df.columns:
        df["market_regime"] = "UNKNOWN"
    df["market_regime"] = df["market_regime"].fillna("UNKNOWN").astype(str)

    if "signal" not in df.columns:
        df["signal"] = "UNKNOWN"
    df["signal"] = df["signal"].fillna("UNKNOWN").astype(str)

    if "risk_multiple" not in df.columns:
        df["risk_multiple"] = np.nan

    # Backward-compatible fallback: estimate risk multiple from pnl/ATR if missing.
    if "atr" in df.columns:
        atr = pd.to_numeric(df["atr"], errors="coerce").fillna(0.0)
    else:
        atr = pd.Series(0.0, index=df.index)
    fallback_risk = 1.2 * atr
    fallback_rm = np.where(fallback_risk > 0, df["pnl"] / (fallback_risk + 1e-9), 0.0)

    df["risk_multiple"] = pd.to_numeric(df["risk_multiple"], errors="coerce")
    df["risk_multiple"] = df["risk_multiple"].fillna(pd.Series(fallback_rm, index=df.index))

    df["win"] = (df["pnl"] > 0).astype(int)
    df["confidence_bucket"] = _bucket_confidence(df["confidence"])

    return df


def _build_group_report(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = []
    for keys, g in df.groupby(group_cols, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        row = {col: val for col, val in zip(group_cols, keys)}
        row["trades"] = int(len(g))
        row["trade_frequency_pct"] = round((len(g) / max(len(df), 1)) * 100, 2)
        row["win_rate_pct"] = round(float(g["win"].mean() * 100), 2)
        row["avg_pnl"] = round(float(g["pnl"].mean()), 4)
        row["avg_risk_multiple"] = round(float(g["risk_multiple"].mean()), 4)
        pf = _safe_profit_factor(g)
        row["profit_factor"] = round(pf, 4) if np.isfinite(pf) else "inf"
        grouped.append(row)

    if not grouped:
        return pd.DataFrame(columns=group_cols + [
            "trades", "trade_frequency_pct", "win_rate_pct", "avg_pnl", "avg_risk_multiple", "profit_factor"
        ])

    out = pd.DataFrame(grouped)
    sort_cols = ["trades", "avg_pnl"]
    return out.sort_values(sort_cols, ascending=[False, False]).reset_index(drop=True)


def _print_summary(df: pd.DataFrame, by_conf: pd.DataFrame, by_regime: pd.DataFrame) -> None:
    total_trades = len(df)
    win_rate = df["win"].mean() * 100 if total_trades else 0.0
    avg_pnl = df["pnl"].mean() if total_trades else 0.0
    overall_pf = _safe_profit_factor(df) if total_trades else 0.0

    print("\n=== SIGNAL QUALITY SUMMARY ===")
    print(f"Total trades: {total_trades}")
    print(f"Win rate: {win_rate:.2f}%")
    print(f"Average pnl: {avg_pnl:.4f}")
    print(f"Profit factor: {overall_pf:.4f}" if np.isfinite(overall_pf) else "Profit factor: inf")

    print("\nConfidence bucket snapshot:")
    if by_conf.empty:
        print("No confidence-bucket data.")
    else:
        print(by_conf[["confidence_bucket", "trades", "win_rate_pct", "avg_pnl", "avg_risk_multiple", "profit_factor"]].to_string(index=False))

    print("\nRegime snapshot:")
    if by_regime.empty:
        print("No regime data.")
    else:
        print(by_regime[["market_regime", "trades", "win_rate_pct", "avg_pnl", "avg_risk_multiple", "profit_factor"]].to_string(index=False))


def _load_trades_via_backtest_or_logs(data_path: str) -> pd.DataFrame:
    if run_backtest is not None:
        df = load_historical_data(data_path)
        trades = run_backtest(df)
        return pd.DataFrame(trades)

    fallback_path = Path("logs/backtest_trades.csv")
    if fallback_path.exists():
        print("Backtester import unavailable; using logs/backtest_trades.csv fallback.")
        return pd.read_csv(fallback_path, on_bad_lines="skip", engine="python")

    raise RuntimeError(
        "Unable to run backtesting pipeline and no fallback trade log found at logs/backtest_trades.csv."
    )


def run_signal_quality_report(data_path: str, output_csv: str) -> dict:
    trades_df = _load_trades_via_backtest_or_logs(data_path)

    if trades_df.empty:
        print("No trades produced by backtest. Report not generated.")
        return {"status": "empty"}

    enriched = _enrich_trades(trades_df)

    by_conf = _build_group_report(enriched, ["confidence_bucket"])
    by_regime = _build_group_report(enriched, ["market_regime"])
    by_signal = _build_group_report(enriched, ["signal"])
    by_combo = _build_group_report(enriched, ["confidence_bucket", "market_regime", "signal"])

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    by_conf.to_csv(output_path.with_name(output_path.stem + "_by_confidence.csv"), index=False)
    by_regime.to_csv(output_path.with_name(output_path.stem + "_by_regime.csv"), index=False)
    by_signal.to_csv(output_path.with_name(output_path.stem + "_by_signal.csv"), index=False)
    by_combo.to_csv(output_path, index=False)

    _print_summary(enriched, by_conf, by_regime)

    print("\nSaved reports:")
    print(str(output_path.with_name(output_path.stem + "_by_confidence.csv")))
    print(str(output_path.with_name(output_path.stem + "_by_regime.csv")))
    print(str(output_path.with_name(output_path.stem + "_by_signal.csv")))
    print(str(output_path))

    return {
        "status": "ok",
        "trades": int(len(enriched)),
        "paths": [
            str(output_path.with_name(output_path.stem + "_by_confidence.csv")),
            str(output_path.with_name(output_path.stem + "_by_regime.csv")),
            str(output_path.with_name(output_path.stem + "_by_signal.csv")),
            str(output_path),
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal quality diagnostics report")
    parser.add_argument("--data", default="historical_data/ICICIBANK.csv", help="Path to OHLCV CSV")
    parser.add_argument("--output", default="logs/signal_quality_report.csv", help="Output CSV path for combined report")
    args = parser.parse_args()

    run_signal_quality_report(args.data, args.output)
