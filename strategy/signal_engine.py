def generate_signal(df):

    latest = df.iloc[-1]

    bullish = (
        latest["RSI"] > 55 and
        latest["EMA_9"] > latest["EMA_21"] and
        latest["close"] > latest["VWAP"]
    )

    bearish = (
        latest["RSI"] < 45 and
        latest["EMA_9"] < latest["EMA_21"] and
        latest["close"] < latest["VWAP"]
    )

    if bullish:
        return {
            "signal": "BUY",
            "trend": "BULLISH",
            "strength": "STRONG"
        }

    elif bearish:
        return {
            "signal": "SELL",
            "trend": "BEARISH",
            "strength": "STRONG"
        }

    return {
        "signal": "HOLD",
        "trend": "SIDEWAYS",
        "strength": "WEAK"
    }