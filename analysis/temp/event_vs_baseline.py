from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================
# CONFIG
# ======================================================

DATA_DIR = Path(
    "data/features/4h"
)

LOOKAHEAD = 12

TOP_EVENT_PERCENTILE = 0.95

BASELINE_SAMPLE_SIZE = 5000

FEATURES = [

    "breakout_pressure",

    "momentum_score",

    "compression_score",

    "trend_strength",

    "volatility_score",

    "momentum_persistence",

    "higher_low_strength",

    "price_position",

    "volume",

    "ema_spread",
]


# ======================================================
# LOAD SAFE
# ======================================================

def load_parquet_safe(path):

    try:

        return pd.read_parquet(path)

    except Exception as exc:

        print(
            f"[SKIP] {path.name} -> {exc}"
        )

        return None


# ======================================================
# PREPARE DATA
# ======================================================

def prepare_dataframe(df):

    if "datetime" in df.columns:

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce"
        )

        df = df.sort_values(
            "datetime"
        )

    # ==================================================
    # FUTURE RETURN
    # ==================================================

    df["future_return"] = (

        df["close"].shift(-LOOKAHEAD)

        - df["close"]
    )

    # ==================================================
    # DROP INVALID
    # ==================================================

    df = df.dropna(
        subset=["future_return"]
    )

    return df


# ======================================================
# IDENTIFY EVENTS
# ======================================================

def identify_events(df):

    threshold = df[
        "future_return"
    ].quantile(
        TOP_EVENT_PERCENTILE
    )

    return df[
        df["future_return"]
        >= threshold
    ].copy()


# ======================================================
# EFFECT SIZE
# ======================================================

def compute_effect_size(

    event_values,

    baseline_values

):

    event_mean = np.mean(
        event_values
    )

    baseline_mean = np.mean(
        baseline_values
    )

    pooled_std = np.sqrt(

        (
            np.var(event_values)

            +

            np.var(baseline_values)
        )

        / 2
    )

    if pooled_std == 0:

        return 0.0

    return (
        event_mean
        - baseline_mean
    ) / pooled_std


# ======================================================
# MAIN
# ======================================================

def main():

    parquet_files = sorted(
        DATA_DIR.glob("*.parquet")
    )

    all_events = []

    all_baselines = []

    # ==================================================
    # LOAD ALL FILES
    # ==================================================

    for path in parquet_files:

        print(
            f"\nProcessing:"
            f" {path.name}"
        )

        df = load_parquet_safe(path)

        if df is None:

            continue

        df = prepare_dataframe(df)

        # ==============================================
        # EVENTS
        # ==============================================

        events = identify_events(df)

        all_events.append(events)

        # ==============================================
        # BASELINE SAMPLE
        # ==============================================

        baseline = df.sample(

            min(
                len(df),
                BASELINE_SAMPLE_SIZE
            ),

            random_state=42
        )

        all_baselines.append(
            baseline
        )

    # ==================================================
    # COMBINE
    # ==================================================

    events_df = pd.concat(
        all_events,
        ignore_index=True
    )

    baseline_df = pd.concat(
        all_baselines,
        ignore_index=True
    )

    # ==================================================
    # ANALYSIS
    # ==================================================

    rows = []

    for feature in FEATURES:

        if (
            feature not in events_df.columns
            or
            feature not in baseline_df.columns
        ):

            continue

        event_values = (
            events_df[feature]
            .dropna()
            .values
        )

        baseline_values = (
            baseline_df[feature]
            .dropna()
            .values
        )

        if (
            len(event_values) == 0
            or
            len(baseline_values) == 0
        ):

            continue

        effect_size = compute_effect_size(

            event_values,

            baseline_values
        )

        rows.append({

            "feature": feature,

            "event_mean":
                np.mean(event_values),

            "baseline_mean":
                np.mean(baseline_values),

            "effect_size":
                effect_size,
        })

    # ==================================================
    # RESULTS
    # ==================================================

    results = pd.DataFrame(rows)

    results = results.sort_values(

        "effect_size",

        ascending=False
    )

    print("\n=== EVENT VS BASELINE ===\n")

    print(
        results.to_string(
            index=False
        )
    )

    # ==================================================
    # SAVE
    # ==================================================

    Path("logs").mkdir(
        parents=True,
        exist_ok=True
    )

    results.to_csv(

        "logs/event_vs_baseline.csv",

        index=False
    )

    print(
        "\nSaved:"
        " logs/event_vs_baseline.csv"
    )


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    main()