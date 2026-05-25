from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ======================================================
# CONFIG
# ======================================================

DATA_DIR = Path(
    "data/features/4h"
)

LOOKAHEAD = 12

N_CLUSTERS = 6


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
    # CLEAN
    # ==================================================

    required = FEATURES + [
        "future_return"
    ]

    df = df.dropna(
        subset=required
    )

    return df


# ======================================================
# MAIN
# ======================================================

def main():

    parquet_files = sorted(
        DATA_DIR.glob("*.parquet")
    )

    all_data = []

    # ==================================================
    # LOAD FILES
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

        if df.empty:

            continue

        df["symbol"] = (
            path.stem
        )

        all_data.append(df)

    # ==================================================
    # COMBINE
    # ==================================================

    combined = pd.concat(
        all_data,
        ignore_index=True
    )

    print(
        f"\nTotal rows:"
        f" {len(combined)}"
    )

    # ==================================================
    # FEATURE MATRIX
    # ==================================================

    X = combined[
        FEATURES
    ].copy()

    # ==================================================
    # NORMALIZE
    # ==================================================

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X
    )

    # ==================================================
    # CLUSTERING
    # ==================================================

    model = KMeans(

        n_clusters=N_CLUSTERS,

        random_state=42,

        n_init=20
    )

    combined["cluster"] = model.fit_predict(
        X_scaled
    )

    # ==================================================
    # SORT FOR TRANSITIONS
    # ==================================================

    if "datetime" not in combined.columns:

        combined = combined.reset_index()

    combined = combined.sort_values([

    "symbol",

    "datetime"
])

    # ==================================================
    # NEXT CLUSTER
    # ==================================================

    combined["next_cluster"] = (

        combined
        .groupby("symbol")["cluster"]
        .shift(-1)
    )

    combined = combined.dropna(
        subset=["next_cluster"]
    )

    combined["next_cluster"] = (
        combined["next_cluster"]
        .astype(int)
    )

    # ==================================================
    # TRANSITION COUNTS
    # ==================================================

    transition_counts = pd.crosstab(

        combined["cluster"],

        combined["next_cluster"]
    )

    # ==================================================
    # TRANSITION PROBABILITIES
    # ==================================================

    transition_probs = (

        transition_counts

        .div(
            transition_counts.sum(axis=1),
            axis=0
        )
    )

    # ==================================================
    # SAVE
    # ==================================================

    Path("logs").mkdir(
        parents=True,
        exist_ok=True
    )

    transition_counts.to_csv(
        "logs/state_transition_counts.csv"
    )

    transition_probs.to_csv(
        "logs/state_transition_probabilities.csv"
    )

    print(
        "\n=== TRANSITION COUNTS ===\n"
    )

    print(
        transition_counts.to_string()
    )

    print(
        "\n=== TRANSITION PROBABILITIES ===\n"
    )

    print(
        transition_probs.round(3).to_string()
    )

    print(
        "\nSaved:"
        " logs/state_transition_counts.csv"
    )

    print(
        "Saved:"
        " logs/state_transition_probabilities.csv"
    )


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    main()
