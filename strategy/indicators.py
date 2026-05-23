import pandas as pd

from ta.momentum import RSIIndicator

from ta.trend import EMAIndicator
from ta.trend import ADXIndicator

from ta.volatility import AverageTrueRange

from ta.volume import VolumeWeightedAveragePrice


def add_indicators(df):

    # RSI
    rsi = RSIIndicator(
        close=df["close"],
        window=14
    )

    df["RSI"] = rsi.rsi()

    # EMA 9
    ema_9 = EMAIndicator(
        close=df["close"],
        window=9
    )

    df["EMA_9"] = ema_9.ema_indicator()

    # EMA 21
    ema_21 = EMAIndicator(
        close=df["close"],
        window=21
    )

    df["EMA_21"] = ema_21.ema_indicator()

    # VWAP
    vwap = VolumeWeightedAveragePrice(

        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"]
    )

    df["VWAP"] = vwap.volume_weighted_average_price()

    # ATR
    atr = AverageTrueRange(

        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["ATR"] = atr.average_true_range()

    # ADX
    adx = ADXIndicator(

        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["ADX"] = adx.adx()

    return df