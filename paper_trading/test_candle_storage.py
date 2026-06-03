import pandas as pd

from paper_trading.candle_storage import CandleStorage

df = pd.DataFrame(
    [
        {
            "datetime": "2026-06-03 09:15:00",
            "open": 100,
            "high": 110,
            "low": 95,
            "close": 108,
            "volume": 10000,
        }
    ]
)

storage = CandleStorage()

storage.save_symbol_candles(
    "RELIANCE-EQ",
    df,
)

print("done")
