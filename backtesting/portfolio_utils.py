import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


def load_feature_data(path: str) -> pd.DataFrame:
    """Load and normalize feature dataframe with a concrete `date` column."""
    df = pd.read_parquet(path)

    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    if "datetime" in df.columns:
        df = df.rename(columns={"datetime": "date"})
    elif "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "symbol", "close"]).copy()
    df = df.sort_values(["date", "symbol"]).reset_index(drop=True)

    return df


def load_recovery_data(path: str) -> pd.DataFrame:
    """Load recovery intelligence and enforce required numeric defaults."""
    recovery = pd.read_csv(path)

    if "rqs_score" not in recovery.columns:
        recovery["rqs_score"] = 0.0
    if "recovery_rate" not in recovery.columns:
        recovery["recovery_rate"] = 0.0

    recovery["rqs_score"] = pd.to_numeric(recovery["rqs_score"], errors="coerce").fillna(0.0)
    recovery["recovery_rate"] = pd.to_numeric(recovery["recovery_rate"], errors="coerce").fillna(0.0)

    return recovery


def compute_state_v3_thresholds(df: pd.DataFrame) -> Dict[str, float]:
    """Compute full-dataset state thresholds for State V3."""
    return {
        "compression_q90": float(df["compression_score"].quantile(0.90)),
        "volatility_q90": float(df["volatility_score"].quantile(0.90)),
        "momentum_q20": float(df["momentum_score"].quantile(0.20)),
        "trend_q20": float(df["trend_strength"].quantile(0.20)),
    }


def build_state_v3_mask(df: pd.DataFrame, thresholds: Dict[str, float]) -> pd.Series:
    """Return boolean mask indicating State V3 signal rows."""
    return (
        (df["compression_score"] >= thresholds["compression_q90"])
        & (df["volatility_score"] >= thresholds["volatility_q90"])
        & (df["momentum_score"] <= thresholds["momentum_q20"])
        & (df["trend_strength"] <= thresholds["trend_q20"])
    )


def rank_candidates(candidates: pd.DataFrame, recovery: pd.DataFrame) -> pd.DataFrame:
    """Attach recovery intelligence and produce ranking score."""
    cols = ["symbol", "rqs_score", "recovery_rate"]
    rec = recovery[cols].drop_duplicates(subset=["symbol"])

    ranked = candidates.merge(rec, on="symbol", how="left")
    ranked["rqs_score"] = ranked["rqs_score"].fillna(0.0)
    ranked["recovery_rate"] = ranked["recovery_rate"].fillna(0.0)

    ranked["score"] = 0.7 * ranked["rqs_score"] + 0.3 * (ranked["recovery_rate"] * 100.0)
    ranked = ranked.sort_values(["score", "symbol"], ascending=[False, True]).reset_index(drop=True)

    return ranked


def calculate_position_value(open_positions: List[dict], last_close: Dict[str, float]) -> float:
    """Calculate mark-to-market value from latest known prices."""
    total = 0.0
    for pos in open_positions:
        symbol = pos["symbol"] if isinstance(pos, dict) else pos.symbol
        px = last_close.get(symbol)
        if px is not None and not np.isnan(px):
            shares = pos["shares"] if isinstance(pos, dict) else pos.shares
            total += shares * float(px)
    return float(total)


def ensure_log_dir(path: str) -> None:
    """Create parent directory for output path if needed."""
    import os

    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
