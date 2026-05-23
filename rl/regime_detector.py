import numpy as np


# ====================================
# DETECT MARKET REGIME
# ====================================

def detect_market_regime(df):

    latest = df.iloc[-1]

    close = latest["close"]

    ema20 = latest["EMA20"]

    ema50 = latest["EMA50"]

    atr = latest["ATR"]

    volatility = latest["VOLATILITY_10"]

    momentum = latest["MOMENTUM_10"]


    # ====================================
    # TREND
    # ====================================

    bullish = 0

    bearish = 0

    sideways = 0

    volatile = 0


    # ====================================
    # BULLISH
    # ====================================

    if (

        close > ema20

        and

        ema20 > ema50

        and

        momentum > 1.02
    ):

        bullish = 1


    # ====================================
    # BEARISH
    # ====================================

    elif (

        close < ema20

        and

        ema20 < ema50

        and

        momentum < 0.98
    ):

        bearish = 1


    # ====================================
    # VOLATILE
    # ====================================

    if (

        atr / close > 0.03

        or

        volatility > 0.03
    ):

        volatile = 1


    # ====================================
    # SIDEWAYS
    # ====================================

    if bullish == 0 and bearish == 0:

        sideways = 1


    # ====================================
    # REGIME VECTOR
    # ====================================

    regime = np.array([

        bullish,

        bearish,

        sideways,

        volatile
    ])

    return regime.astype(np.float32)