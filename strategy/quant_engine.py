from data.candle_fetcher import fetch_candles
from strategy.indicators import add_indicators
from strategy.signal_engine import generate_signal
from strategy.scoring import calculate_score


def analyze_stock(symbol, token):

    df = fetch_candles(token)

    if df.empty:
        return None

    df = add_indicators(df)

    signal_data = generate_signal(df)

    score, direction, breakdown = calculate_score(df)
    

    latest = df.iloc[-1]

    return {
        
        "token": token,
        "symbol": symbol,
        "price": latest["close"],
        "RSI": round(latest["RSI"], 2),
        "EMA_9": round(latest["EMA_9"], 2),
        "EMA_21": round(latest["EMA_21"], 2),
        "VWAP": round(latest["VWAP"], 2),
        "signal": signal_data["signal"],
        "trend": signal_data["trend"],
        "strength": signal_data["strength"],
        "score_breakdown": breakdown,
        "market_bias": direction,
        "ATR": round(latest["ATR"], 2),
        "score": score

    }