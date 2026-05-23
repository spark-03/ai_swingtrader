import pandas as pd

from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice


def add_indicators(df):

    # =========================
    # EMA
    # =========================

    df["EMA_9"] = EMAIndicator(
        close=df["close"],
        window=9
    ).ema_indicator()

    df["EMA_21"] = EMAIndicator(
        close=df["close"],
        window=21
    ).ema_indicator()

    # =========================
    # RSI
    # =========================

    df["RSI"] = RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    # =========================
    # VWAP
    # =========================

    df["VWAP"] = VolumeWeightedAveragePrice(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"]
    ).volume_weighted_average_price()

    # =========================
    # ATR
    # =========================

    df["ATR"] = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    ).average_true_range()

    # =========================
    # ADX
    # =========================

    df["ADX"] = ADXIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    ).adx()

    # =========================
    # REMOVE NaN ROWS
    # =========================

    df.dropna(inplace=True)

    return df