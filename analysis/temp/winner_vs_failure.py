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

WINNER_PERCENTILE = 0.95

FAILURE_PERCENTILE = 0.20


FEATURES = [

    "trend_strength",

    "breakout_pressure",

    "momentum_score",

    "compression_score",

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
# PREPARE
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
    # DROP NA
    # ==================================================

    df = df.dropna(
        subset=["future_return"]
    )

    return df


# ======================================================
# IDENTIFY WINNERS
# ======================================================

def identify_winners(df):

    threshold = df[
        "future_return"
    ].quantile(
        WINNER_PERCENTILE
    )

    return df[
        df["future_return"]
        >= threshold
    ].copy()


# ======================================================
# IDENTIFY FAILURES
# ======================================================

def identify_failures(df):

    threshold = df[
        "future_return"
    ].quantile(
        FAILURE_PERCENTILE
    )

    return df[
        df["future_return"]
        <= threshold
    ].copy()


# ======================================================
# EFFECT SIZE
# ======================================================

def compute_effect_size(

    winner_values,

    failure_values

):

    winner_mean = np.mean(
        winner_values
    )

    failure_mean = np.mean(
        failure_values
    )

    pooled_std = np.sqrt(

        (
            np.var(winner_values)

            +

            np.var(failure_values)
        )

        / 2
    )

    if pooled_std == 0:

        return 0.0

    return (

        winner_mean
        - failure_mean

    ) / pooled_std


# ======================================================
# MAIN
# ======================================================

def main():

    parquet_files = sorted(
        DATA_DIR.glob("*.parquet")
    )

    all_winners = []

    all_failures = []

    # ==================================================
    # PROCESS FILES
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

        winners = identify_winners(df)

        failures = identify_failures(df)

        all_winners.append(
            winners
        )

        all_failures.append(
            failures
        )

    # ==================================================
    # COMBINE
    # ==================================================

    winners_df = pd.concat(
        all_winners,
        ignore_index=True
    )

    failures_df = pd.concat(
        all_failures,
        ignore_index=True
    )

    # ==================================================
    # ANALYSIS
    # ==================================================

    rows = []

    for feature in FEATURES:

        if (
            feature not in winners_df.columns
            or
            feature not in failures_df.columns
        ):

            continue

        winner_values = (

            winners_df[feature]

            .dropna()

            .values
        )

        failure_values = (

            failures_df[feature]

            .dropna()

            .values
        )

        if (
            len(winner_values) == 0
            or
            len(failure_values) == 0
        ):

            continue

        effect_size = compute_effect_size(

            winner_values,

            failure_values
        )

        rows.append({

            "feature": feature,

            "winner_mean":
                np.mean(winner_values),

            "failure_mean":
                np.mean(failure_values),

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

    print(
        "\n=== WINNER VS FAILURE ===\n"
    )

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

        "logs/winner_vs_failure.csv",

        index=False
    )

    print(
        "\nSaved:"
        " logs/winner_vs_failure.csv"
    )


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    main()