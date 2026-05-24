import os

import pandas as pd

import numpy as np

# ====================================
# DATA FOLDER
# ====================================

DATA_FOLDER = "data/historical/5min"

# ====================================
# RESULTS
# ====================================

results = []

# ====================================
# PROCESS FILES
# ====================================

for file_name in os.listdir(DATA_FOLDER):

    if not file_name.endswith(".parquet"):

        continue

    try:

        symbol = file_name.replace(
            ".parquet",
            ""
        )

        df = pd.read_parquet(

            os.path.join(
                DATA_FOLDER,
                file_name
            )
        )

        # ====================================
        # BASIC VALIDATION
        # ====================================

        required_columns = [

            "open",

            "high",

            "low",

            "close",

            "volume"
        ]

        missing = [

            col for col in required_columns

            if col not in df.columns
        ]

        if len(missing) > 0:

            print(

                f"SKIPPED {symbol}: "
                f"missing {missing}"
            )

            continue

        if len(df) < 500:

            continue

        # ====================================
        # CLEAN
        # ====================================

        df = df.dropna()

        # ====================================
        # EMA
        # ====================================

        df["EMA20"] = (

            df["close"]
            .ewm(span=20)
            .mean()
        )

        df["EMA50"] = (

            df["close"]
            .ewm(span=50)
            .mean()
        )

        # ====================================
        # ATR
        # ====================================

        high_low = (

            df["high"]

            -

            df["low"]
        )

        high_close = abs(

            df["high"]

            -

            df["close"].shift()
        )

        low_close = abs(

            df["low"]

            -

            df["close"].shift()
        )

        ranges = pd.concat([

            high_low,

            high_close,

            low_close

        ], axis=1)

        true_range = ranges.max(axis=1)

        df["ATR"] = (

            true_range
            .rolling(14)
            .mean()
        )

        df = df.dropna()

        if len(df) < 300:

            continue

        # ====================================
        # ATR %
        # ====================================

        atr_percent = (

            df["ATR"].mean()

            /

            df["close"].mean()
        ) * 100

        # ====================================
        # TREND ALIGNMENT
        # ====================================

        trend_alignment = (

            df["EMA20"]

            >

            df["EMA50"]

        ).mean()

        # ====================================
        # MOMENTUM QUALITY
        # ====================================

        returns = (
            df["close"]
            .pct_change()
        )

        momentum_quality = (

            returns.abs().mean()

            /

            returns.std()
        )

        # ====================================
        # VOLUME QUALITY
        # ====================================

        volume_quality = np.log(

            df["volume"].mean() + 1
        )

        # ====================================
        # NOISE SCORE
        # ====================================

        candle_noise = (

            abs(

                df["close"]

                -

                df["open"]
            ).mean()

            /

            (

                df["high"]

                -

                df["low"]
            ).mean()
        )

        # ====================================
        # FINAL SCORE
        # ====================================

        score = 0

        # ATR
        if 1.5 <= atr_percent <= 4:

            score += 25

        elif 1 <= atr_percent <= 5:

            score += 15

        # TREND
        score += trend_alignment * 25

        # MOMENTUM
        score += min(
            momentum_quality * 20,
            20
        )

        # VOLUME
        score += min(
            volume_quality,
            15
        )

        # LOW NOISE
        score += max(
            15 - (candle_noise * 10),
            0
        )

        results.append({

            "symbol": symbol,

            "score": round(score, 2),

            "atr_percent":
            round(atr_percent, 2),

            "trend_alignment":
            round(
                trend_alignment,
                2
            ),

            "momentum_quality":
            round(
                momentum_quality,
                2
            ),

            "volume_quality":
            round(
                volume_quality,
                2
            ),

            "noise":
            round(
                candle_noise,
                2
            )
        })

    except Exception as e:

        print(

            f"FAILED: {file_name}"
        )

        print(e)

# ====================================
# DATAFRAME
# ====================================

results_df = pd.DataFrame(results)

# ====================================
# EMPTY CHECK
# ====================================

if len(results_df) == 0:

    print("\nNO VALID STOCKS FOUND")

else:

    results_df = results_df.sort_values(

        by="score",

        ascending=False
    )

    results_df.to_csv(

        "top_rl_stocks.csv",

        index=False
    )

    print(
        "\n========== TOP RL STOCKS ==========\n"
    )

    print(
        results_df.head(30)
    )

    print(
        "\nSaved: top_rl_stocks.csv"
    )