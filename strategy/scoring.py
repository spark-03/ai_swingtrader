def calculate_score(df):

    latest = df.iloc[-1]

    bullish_score = 0
    bearish_score = 0

    breakdown = {}

    # RSI
    if latest["RSI"] > 60:
        bullish_score += 25
        breakdown["RSI"] = "BULLISH"

    elif latest["RSI"] < 40:
        bearish_score += 25
        breakdown["RSI"] = "BEARISH"

    else:
        breakdown["RSI"] = "NEUTRAL"

    # EMA Trend
    if latest["EMA_9"] > latest["EMA_21"]:
        bullish_score += 35
        breakdown["EMA"] = "BULLISH"

    elif latest["EMA_9"] < latest["EMA_21"]:
        bearish_score += 35
        breakdown["EMA"] = "BEARISH"

    else:
        breakdown["EMA"] = "NEUTRAL"

    # VWAP
    if latest["close"] > latest["VWAP"]:
        bullish_score += 25
        breakdown["VWAP"] = "BULLISH"

    elif latest["close"] < latest["VWAP"]:
        bearish_score += 25
        breakdown["VWAP"] = "BEARISH"

    else:
        breakdown["VWAP"] = "NEUTRAL"

    # Momentum
    if latest["close"] > latest["EMA_9"]:
        bullish_score += 15
        breakdown["Momentum"] = "BULLISH"

    elif latest["close"] < latest["EMA_9"]:
        bearish_score += 15
        breakdown["Momentum"] = "BEARISH"

    else:
        breakdown["Momentum"] = "NEUTRAL"

    final_score = max(bullish_score, bearish_score)

    direction = (
        "BULLISH"
        if bullish_score > bearish_score
        else "BEARISH"
    )

    return final_score, direction, breakdown