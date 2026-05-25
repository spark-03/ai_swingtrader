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

    clusters = model.fit_predict(
        X_scaled
    )

    combined["cluster"] = clusters

    # ==================================================
    # CLUSTER ANALYSIS
    # ==================================================

    rows = []

    for cluster_id in sorted(

        combined["cluster"].unique()

    ):

        cluster_df = combined[
            combined["cluster"]
            == cluster_id
        ]

        row = {

            "cluster":
                cluster_id,

            "samples":
                len(cluster_df),

            "avg_future_return":
                cluster_df[
                    "future_return"
                ].mean(),

            "median_future_return":
                cluster_df[
                    "future_return"
                ].median(),

            "win_rate":
                (
                    cluster_df[
                        "future_return"
                    ] > 0
                ).mean(),
        }

        # ==============================================
        # FEATURE AVERAGES
        # ==============================================

        for feature in FEATURES:

            row[
                f"{feature}_mean"
            ] = cluster_df[
                feature
            ].mean()

        rows.append(row)

    # ==================================================
    # RESULTS
    # ==================================================

    results = pd.DataFrame(rows)

    results = results.sort_values(

        "avg_future_return",

        ascending=False
    )

    print(
        "\n=== MARKET STATE CLUSTERS ===\n"
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

        "logs/market_state_clusters.csv",

        index=False
    )

    combined.to_csv(

        "logs/market_state_assignments.csv",

        index=False
    )

    print(
        "\nSaved:"
        " logs/market_state_clusters.csv"
    )

    print(
        "Saved:"
        " logs/market_state_assignments.csv"
    )


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    main()