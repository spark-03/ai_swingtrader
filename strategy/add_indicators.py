import pandas as pd

import numpy as np


def add_indicators(df):

    df = df.copy()

    # ====================================
    # EMA
    # ====================================

    df["EMA20"] = (

        df["close"]

        .ewm(
            span=20,
            adjust=False
        )

        .mean()
    )

    df["EMA50"] = (

        df["close"]

        .ewm(
            span=50,
            adjust=False
        )

        .mean()
    )

    # ====================================
    # RSI
    # ====================================

    delta = df["close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    df["RSI"] = (

        100

        -

        (
            100
            /
            (1 + rs)
        )
    )

    # ====================================
    # MACD
    # ====================================

    ema12 = df["close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df["close"].ewm(
        span=26,
        adjust=False
    ).mean()

    df["MACD"] = (
        ema12 - ema26
    )

    df["MACD_SIGNAL"] = (

        df["MACD"]

        .ewm(
            span=9,
            adjust=False
        )

        .mean()
    )

    df["MACD_DIFF"] = (

        df["MACD"]

        -

        df["MACD_SIGNAL"]
    )

    # ====================================
    # ATR
    # ====================================

    high_low = (
        df["high"] - df["low"]
    )

    high_close = (

        (
            df["high"]
            -
            df["close"].shift()
        )

        .abs()
    )

    low_close = (

        (
            df["low"]
            -
            df["close"].shift()
        )

        .abs()
    )

    true_range = pd.concat([

        high_low,

        high_close,

        low_close

    ], axis=1).max(axis=1)

    df["ATR"] = (
        true_range
        .rolling(14)
        .mean()
    )

    # ====================================
    # VWAP
    # ====================================

    typical_price = (

        df["high"]

        +

        df["low"]

        +

        df["close"]

    ) / 3

    cumulative_tpv = (
        typical_price * df["volume"]
    ).cumsum()

    cumulative_volume = (
        df["volume"]
    ).cumsum()

    df["VWAP"] = (

        cumulative_tpv

        /

        (
            cumulative_volume
            + 1e-9
        )
    )

    # ====================================
    # BOLLINGER BANDS
    # ====================================

    bb_mid = (
        df["close"]
        .rolling(20)
        .mean()
    )

    bb_std = (
        df["close"]
        .rolling(20)
        .std()
    )

    df["BB_MID"] = bb_mid

    df["BB_HIGH"] = (
        bb_mid + 2 * bb_std
    )

    df["BB_LOW"] = (
        bb_mid - 2 * bb_std
    )

    # ====================================
    # RETURNS
    # ====================================

    df["RETURN_1"] = (
        df["close"].pct_change(1)
    )

    df["RETURN_5"] = (
        df["close"].pct_change(5)
    )

    df["RETURN_10"] = (
        df["close"].pct_change(10)
    )

    # ====================================
    # VOLATILITY
    # ====================================

    df["VOLATILITY_10"] = (

        df["RETURN_1"]

        .rolling(10)

        .std()
    )

    # ====================================
    # MOMENTUM
    # ====================================

    df["MOMENTUM_10"] = (

        df["close"]

        /

        (
            df["close"]
            .shift(10)
            + 1e-9
        )
    )

    return df