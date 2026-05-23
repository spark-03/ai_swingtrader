def calculate_confidence(df):

    latest = df.iloc[-1]

    score = 0

    # EMA Trend Strength
    ema_9 = latest["EMA_9"]
    ema_21 = latest["EMA_21"]

    ema_diff = abs(ema_9 - ema_21)

    if ema_diff > 1:

        score += 30

    elif ema_diff > 0.5:

        score += 20

    # RSI Strength
    rsi = latest["RSI"]

    # Bullish momentum
    if rsi > 60:

        score += 25

    # Bearish momentum
    elif rsi < 40:

        score += 25

    # VWAP Confirmation
    close = latest["close"]
    vwap = latest["VWAP"]

    if abs(close - vwap) > 1:

        score += 25

    # ATR Volatility
    
    atr = latest["ATR"]

    if atr > 1:

        score += 20
        

  # ADX Trend Strength
    adx = latest["ADX"]

    if adx > 25:

     score += 30

    elif adx > 20:

     score += 15  
    return score