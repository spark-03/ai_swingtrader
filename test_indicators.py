from data.candle_fetcher import fetch_candles
from data.nifty100_tokens import TOKENS
from strategy.indicators import add_indicators


TOKEN = TOKENS["RELIANCE-EQ"]

df = fetch_candles(TOKEN)

if df is not None:

    df = add_indicators(df)

    print(
        df[
            [
                "datetime",
                "close",
                "RSI",
                "EMA_9",
                "EMA_21",
                "VWAP"
            ]
        ].tail()
    )