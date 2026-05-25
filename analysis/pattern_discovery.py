from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("data/features/5min")
OUTPUT_CSV = Path("logs/pattern_discovery.csv")

# =========================================================
# REQUIRED COLUMNS
# =========================================================

REQUIRED_COLUMNS = {
    "datetime",
    "close",
    "breakout_pressure",
    "momentum_persistence",
    "ATR",
    "VWAP",
    "volume",
    "EMA20",
    "EMA50",
    "trend_strength",
    "momentum_score",
    "compression_score",
    "volatility_score",
    "higher_low_strength",
    "price_position",
}

# =========================================================
# BASE FEATURES
# =========================================================

BASE_FEATURES = [

    "breakout_pressure",

    "momentum_persistence",

    "ATR",

    "VWAP",

    "volume",

    "EMA20",

    "EMA50",

    "trend_strength",

    "momentum_score",

    "compression_score",

    "volatility_score",

    "higher_low_strength",

    "price_position",
]

# =========================================================
# ENGINEERED FEATURES
# =========================================================

ENGINEERED_FEATURES = [

    "ema_spread",

    "atr_pct",

    "vwap_distance",
]

ALL_FEATURES = (
    BASE_FEATURES
    + ENGINEERED_FEATURES
)

# =========================================================
# SAFE PARQUET LOADER
# =========================================================

def _load_parquet_safe(
    path: Path
) -> pd.DataFrame | None:

    try:

        return pd.read_parquet(path)

    except Exception as exc:

        print(
            f"[SKIP] Corrupt/unreadable parquet:"
            f" {path.name} ({exc})"
        )

        return None

# =========================================================
# FILE PREPARATION
# =========================================================

def _prepare_file(
    df: pd.DataFrame,
    path: Path
) -> pd.DataFrame | None:

    # =====================================================
    # REQUIRED COLUMN CHECK
    # =====================================================

    missing = [

        c

        for c in REQUIRED_COLUMNS

        if c not in df.columns
    ]

    if missing:

        print(
            f"[SKIP] Missing required columns"
            f" in {path.name}: {missing}"
        )

        return None

    # =====================================================
    # COPY
    # =====================================================

    out = df.copy()

    # =====================================================
    # DATETIME
    # =====================================================

    out["datetime"] = pd.to_datetime(
        out["datetime"],
        errors="coerce"
    )

    out = out.dropna(
        subset=["datetime", "close"]
    )

    out = out.sort_values(
        "datetime"
    )

    # =====================================================
    # FEATURE ENGINEERING
    # =====================================================

    # EMA spread
    out["ema_spread"] = (
        out["EMA20"]
        - out["EMA50"]
    )

    # ATR %
    out["atr_pct"] = (
        out["ATR"]
        / (out["close"] + 1e-9)
    )

    # VWAP distance
    out["vwap_distance"] = (

        (
            out["close"]
            - out["VWAP"]
        )

        / (
            out["close"]
            + 1e-9
        )
    )

    # =====================================================
    # FUTURE RETURN LABEL
    # =====================================================

    out["future_return"] = (
        out["close"].shift(-5)
        - out["close"]
    )

    out = out.dropna(
        subset=["future_return"]
    )

    # =====================================================
    # KEEP ANALYTICAL COLUMNS
    # =====================================================

    keep_cols = (
        ALL_FEATURES
        + ["future_return"]
    )

    out = out[keep_cols]

    # =====================================================
    # NUMERIC COERCION
    # =====================================================

    for col in keep_cols:

        out[col] = pd.to_numeric(
            out[col],
            errors="coerce"
        )

    # =====================================================
    # DROP INVALID ROWS
    # =====================================================

    before_drop = len(out)

    out = out.dropna(
        subset=keep_cols
    )

    after_drop = len(out)

    print(
        f"{path.name}"
        f" | Rows Before: {before_drop}"
        f" | Rows After: {after_drop}"
    )

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if out.empty:

        print(
            f"[SKIP] No valid rows"
            f" after cleaning in {path.name}"
        )

        return None

    return out

# =========================================================
# FEATURE SUMMARY
# =========================================================

def _summarize_feature(
    df: pd.DataFrame,
    feature: str
) -> dict:

    winners = df[
        df["future_return"] > 0
    ][feature]

    losers = df[
        df["future_return"] <= 0
    ][feature]

    return {

        "feature": feature,

        "winner_mean":

            float(winners.mean())

            if not winners.empty

            else np.nan,

        "winner_median":

            float(winners.median())

            if not winners.empty

            else np.nan,

        "winner_std":

            float(winners.std())

            if not winners.empty

            else np.nan,

        "loser_mean":

            float(losers.mean())

            if not losers.empty

            else np.nan,

        "loser_median":

            float(losers.median())

            if not losers.empty

            else np.nan,

        "loser_std":

            float(losers.std())

            if not losers.empty

            else np.nan,
    }

# =========================================================
# MAIN PIPELINE
# =========================================================

def run_pattern_discovery(

    data_dir: Path = DATA_DIR,

    output_csv: Path = OUTPUT_CSV

) -> pd.DataFrame:

    parquet_files = sorted(
        data_dir.glob("*.parquet")
    )

    if not parquet_files:

        print(
            f"No parquet files found in:"
            f" {data_dir}"
        )

        return pd.DataFrame()

    analyzed = 0

    prepared_frames = []

    print(
        f"\nParquet files discovered:"
        f" {len(parquet_files)}"
    )

    # =====================================================
    # PROCESS FILES
    # =====================================================

    for path in parquet_files:

        print(
            f"\nProcessing:"
            f" {path.name}"
        )

        raw = _load_parquet_safe(path)

        if raw is None:
            continue

        prepared = _prepare_file(
            raw,
            path
        )

        if prepared is None:
            continue

        prepared_frames.append(
            prepared
        )

        analyzed += 1

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if not prepared_frames:

        print(
            "\nNo valid parquet files"
            " could be analyzed."
        )

        return pd.DataFrame()

    # =====================================================
    # COMBINE
    # =====================================================

    combined = pd.concat(
        prepared_frames,
        ignore_index=True
    )

    # =====================================================
    # SUMMARY ROWS
    # =====================================================

    rows = [

        _summarize_feature(
            combined,
            feat
        )

        for feat in ALL_FEATURES
    ]

    report = pd.DataFrame(rows)

    # =====================================================
    # SAVE REPORT
    # =====================================================

    output_csv.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report.to_csv(
        output_csv,
        index=False
    )

    # =====================================================
    # WINNER / LOSER COUNTS
    # =====================================================

    winners_n = int(
        (
            combined["future_return"] > 0
        ).sum()
    )

    losers_n = int(
        (
            combined["future_return"] <= 0
        ).sum()
    )

    # =====================================================
    # CONSOLE OUTPUT
    # =====================================================

    print("\n=== PATTERN DISCOVERY SUMMARY ===")

    print(
        f"Parquet files analyzed:"
        f" {analyzed}"
    )

    print(
        f"Total states analyzed:"
        f" {len(combined)}"
    )

    print(
        f"Winner states:"
        f" {winners_n}"
    )

    print(
        f"Loser states:"
        f" {losers_n}"
    )

    print(
        f"Saved report:"
        f" {output_csv}"
    )

    display_cols = [

        "feature",

        "winner_mean",

        "loser_mean",

        "winner_std",

        "loser_std",
    ]

    print(
        "\nFeature separation snapshot:"
    )

    print(
        report[display_cols]
        .to_string(index=False)
    )

    return report

# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    run_pattern_discovery()