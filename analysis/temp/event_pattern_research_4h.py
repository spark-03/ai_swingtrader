from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================
# CONFIG
# ======================================================

DATA_DIR = Path(
    "data/features/4h"
)

OUTPUT_DIR = Path(
    "logs"
)

EVENT_OUTPUT = (
    OUTPUT_DIR
    / "event_sequences.csv"
)

EVOLUTION_OUTPUT = (
    OUTPUT_DIR
    / "event_feature_evolution.csv"
)

LOOKAHEAD = 12

PRE_EVENT_WINDOW = 10

TOP_EVENT_PERCENTILE = 0.95


# ======================================================
# FEATURES TO TRACK
# ======================================================

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
# PREPARE DATAFRAME
# ======================================================

def prepare_dataframe(df):

    # ==================================================
    # DATETIME
    # ==================================================

    if "datetime" in df.columns:

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce"
        )

        df = df.sort_values(
            "datetime"
        )

    # ==================================================
    # EMA SPREAD
    # ==================================================

    if (
        "EMA20" in df.columns
        and
        "EMA50" in df.columns
    ):

        df["ema_spread"] = (
            df["EMA20"]
            - df["EMA50"]
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

    df = df.dropna(
        subset=["future_return"]
    )

    return df


# ======================================================
# FIND EXPLOSIVE EVENTS
# ======================================================

def identify_events(df):

    threshold = df[
        "future_return"
    ].quantile(
        TOP_EVENT_PERCENTILE
    )

    events = df[
        df["future_return"]
        >= threshold
    ].copy()

    print(
        f"Explosive events found:"
        f" {len(events)}"
    )

    return events


# ======================================================
# EXTRACT PRE-EVENT WINDOWS
# ======================================================

def extract_event_sequences(
    df,
    events
):

    sequences = []

    for idx in events.index:

        # ==============================================
        # POSITION INDEX
        # ==============================================

        pos = df.index.get_loc(idx)

        start = (
            pos
            - PRE_EVENT_WINDOW
        )

        end = pos

        # ==============================================
        # SAFETY
        # ==============================================

        if start < 0:

            continue

        # ==============================================
        # WINDOW
        # ==============================================

        window = df.iloc[
            start:end
        ].copy()

        if (
            len(window)
            != PRE_EVENT_WINDOW
        ):

            continue

        # ==============================================
        # ANNOTATION
        # ==============================================

        window["event_index"] = idx

        window[
            "steps_before_event"
        ] = list(

            range(
                -PRE_EVENT_WINDOW,
                0
            )
        )

        sequences.append(
            window
        )

    # ==================================================
    # EMPTY
    # ==================================================

    if not sequences:

        return pd.DataFrame()

    return pd.concat(
        sequences,
        ignore_index=True
    )


# ======================================================
# AGGREGATE FEATURE EVOLUTION
# ======================================================

def aggregate_feature_evolution(
    sequences
):

    rows = []

    for step in sorted(

        sequences[
            "steps_before_event"
        ].unique()

    ):

        step_df = sequences[

            sequences[
                "steps_before_event"
            ] == step
        ]

        row = {

            "steps_before_event": step
        }

        for feature in FEATURES:

            if feature not in step_df.columns:

                continue

            row[
                f"{feature}_mean"
            ] = step_df[
                feature
            ].mean()

        rows.append(row)

    return pd.DataFrame(rows)


# ======================================================
# MAIN
# ======================================================

def main():

    parquet_files = sorted(
        DATA_DIR.glob("*.parquet")
    )

    print(
        f"\nParquet files found:"
        f" {len(parquet_files)}"
    )

    all_sequences = []

    for path in parquet_files:

        print(
            f"\nProcessing:"
            f" {path.name}"
        )

        # ==============================================
        # LOAD
        # ==============================================

        df = load_parquet_safe(path)

        if df is None:

            continue

        # ==============================================
        # PREPARE
        # ==============================================

        df = prepare_dataframe(df)

        # ==============================================
        # EVENTS
        # ==============================================

        events = identify_events(df)

        # ==============================================
        # EXTRACT
        # ==============================================

        sequences = extract_event_sequences(
            df,
            events
        )

        if sequences.empty:

            continue

        # ==============================================
        # SYMBOL
        # ==============================================

        sequences["symbol"] = (
            path.stem
        )

        all_sequences.append(
            sequences
        )

    # ==================================================
    # EMPTY CHECK
    # ==================================================

    if not all_sequences:

        print(
            "\nNo sequences extracted."
        )

        return

    # ==================================================
    # COMBINE
    # ==================================================

    combined = pd.concat(
        all_sequences,
        ignore_index=True
    )

    # ==================================================
    # EVOLUTION
    # ==================================================

    evolution = aggregate_feature_evolution(
        combined
    )

    # ==================================================
    # SAVE
    # ==================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    combined.to_csv(
        EVENT_OUTPUT,
        index=False
    )

    evolution.to_csv(
        EVOLUTION_OUTPUT,
        index=False
    )

    # ==================================================
    # SUMMARY
    # ==================================================

    print("\n=== COMPLETE ===")

    print(
        f"\nSequences saved:"
        f"\n{EVENT_OUTPUT}"
    )

    print(
        f"\nEvolution saved:"
        f"\n{EVOLUTION_OUTPUT}"
    )

    print(
        f"\nTotal extracted rows:"
        f" {len(combined)}"
    )


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    main()