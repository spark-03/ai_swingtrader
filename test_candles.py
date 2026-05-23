from data.candle_fetcher import fetch_candles
from data.nifty100_tokens import TOKENS


TOKEN = TOKENS["RELIANCE-EQ"]

print("TOKEN:", TOKEN)

df = fetch_candles(TOKEN)

if df is not None:
    print(df.head())
else:
    print("No candle data found.")