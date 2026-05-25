from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================
# CONFIG
# ======================================================

INPUT_DIR = Path(
    "data/features/5min"
)

OUTPUT_DIR = Path(
    "data/features/4h"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


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
# RESAMPLE TO 4h
# ======================================================

def resample_to_4h(df):

    # ==================================================
    # DATETIME
    # ==================================================

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["datetime"]
    )

    df = df.sort_values(
        "datetime"
    )

    df = df.set_index(
        "datetime"
    )

    # ==================================================
    # OHLCV RESAMPLE
    # ==================================================

    ohlcv = df.resample(
        "4h"
    ).agg({

        "open": "first",

        "high": "max",

        "low": "min",

        "close": "last",

        "volume": "sum",
    })

    ohlcv = ohlcv.dropna()

    return ohlcv


# ======================================================
# FEATURE ENGINEERING
# ======================================================

def build_features(df):

    out = df.copy()

    # ==================================================
    # EMA
    # ==================================================

    out["EMA20"] = (
        out["close"]
        .ewm(span=20)
        .mean()
    )

    out["EMA50"] = (
        out["close"]
        .ewm(span=50)
        .mean()
    )

    # ==================================================
    # EMA SPREAD
    # ==================================================

    out["ema_spread"] = (
        out["EMA20"]
        - out["EMA50"]
    )

    # ==================================================
    # RETURNS
    # ==================================================

    out["RETURN_1"] = (
        out["close"]
        .pct_change(1)
    )

    out["RETURN_5"] = (
        out["close"]
        .pct_change(5)
    )

    # ==================================================
    # VOLATILITY
    # ==================================================

    out["rolling_volatility"] = (

        out["RETURN_1"]

        .rolling(10)

        .std()
    )

    out["volatility_score"] = (

        out["rolling_volatility"]

        / (
            out["close"]
            .rolling(10)
            .mean()

            + 1e-9
        )
    )

    # ==================================================
    # MOMENTUM
    # ==================================================

    out["momentum_score"] = (

        out["RETURN_5"]

        .rolling(5)

        .mean()
    )

    out["momentum_persistence"] = (

        (
            out["RETURN_1"] > 0
        )

        .rolling(5)

        .mean()
    )

    # ==================================================
    # TREND STRENGTH
    # ==================================================

    out["trend_strength"] = (

        abs(out["ema_spread"])

        / (
            out["close"]
            + 1e-9
        )
    )

    # ==================================================
    # BREAKOUT PRESSURE
    # ==================================================

    out["rolling_high"] = (
        out["high"]
        .rolling(20)
        .max()
    )

    out["rolling_low"] = (
        out["low"]
        .rolling(20)
        .min()
    )

    out["range_width"] = (

        out["rolling_high"]

        - out["rolling_low"]
    )

    out["price_position"] = (

        (
            out["close"]

            - out["rolling_low"]
        )

        / (
            out["range_width"]
            + 1e-9
        )
    )

    out["breakout_pressure"] = (

        out["price_position"]

        * out["trend_strength"]
    )

    # ==================================================
    # COMPRESSION
    # ==================================================

    out["compression_score"] = (

        1

        / (
            out["range_width"]
            + 1e-9
        )
    )

    # ==================================================
    # HIGHER LOW STRENGTH
    # ==================================================

    out["higher_low_strength"] = (

        out["low"]

        .diff()

        .rolling(5)

        .mean()
    )

    # ==================================================
    # ATR
    # ==================================================

    tr1 = (
        out["high"]
        - out["low"]
    )

    tr2 = abs(
        out["high"]
        - out["close"].shift(1)
    )

    tr3 = abs(
        out["low"]
        - out["close"].shift(1)
    )

    out["TR"] = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    out["ATR"] = (
        out["TR"]
        .rolling(14)
        .mean()
    )

    # ==================================================
    # CLEAN
    # ==================================================

    out = out.dropna()

    return out


# ======================================================
# PROCESS FILE
# ======================================================

def process_file(path):

    print(
        f"\nProcessing: {path.name}"
    )

    df = load_parquet_safe(path)

    if df is None:

        return

    if "datetime" not in df.columns:

        print(
            "[SKIP] Missing datetime"
        )

        return

    df_4h = resample_to_4h(df)

    features = build_features(df_4h)

    output_path = (
        OUTPUT_DIR
        / path.name
    )

    features.to_parquet(
        output_path
    )

    print(
        f"[OK] Saved: {output_path}"
    )

    print(
        f"Rows: {len(features)}"
    )


# ======================================================
# MAIN
# ======================================================

def main():

    parquet_files = sorted(
        INPUT_DIR.glob("*.parquet")
    )

    print(
        f"\nFiles found:"
        f" {len(parquet_files)}"
    )

    for path in parquet_files:

        process_file(path)

    print(
        "\n=== COMPLETE ==="
    )


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    main()
