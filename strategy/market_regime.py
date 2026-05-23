def detect_market_regime(df):

    latest = df.iloc[-1]

    ema_9 = latest["EMA_9"]
    ema_21 = latest["EMA_21"]

    atr = latest["ATR"]

    # EMA Difference
    ema_diff = abs(ema_9 - ema_21)

    # TRENDING MARKET
    if ema_diff > 0.5 and atr > 0.5:

        return "TRENDING"

    # VOLATILE MARKET
    elif atr > 3:

        return "VOLATILE"

    # SIDEWAYS MARKET
    else:

        return "SIDEWAYS"