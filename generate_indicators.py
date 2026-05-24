import pandas as pd

from strategy.add_indicators import (
    add_indicators
)
from ai.features.breakout_pressure import (
    BreakoutPressure
)

from ai.features.volatility_compression import (
    VolatilityCompression
)

# =========================
# LOAD RAW DATA
# =========================

df = pd.read_csv(
    "historical_data/ICICIBANK.csv"
)

print("Raw Data Loaded")

print(df.head())

# =========================
# ADD INDICATORS
# =========================

df = add_indicators(df)

print("\nIndicators Added")

print(df.head())

# =========================
# VOLATILITY COMPRESSION
# =========================

compression_engine = (

    VolatilityCompression()
)
# =========================
# BREAKOUT PRESSURE
# =========================

breakout_engine = (

    BreakoutPressure()
)

df = breakout_engine.calculate(
    df
)

print("\nBreakout Pressure Added")

print(

    df[
        [

            "close",

            "breakout_pressure"
        ]
    ].tail()
)
df = compression_engine.calculate(
    df
)

print("\nCompression Feature Added")

print(

    df[
        [

            "close",

            "ATR",

            "compression_score"
        ]
    ].tail()
)

# =========================
# SAVE NEW FILE
# =========================

output_path = (

    "historical_data/"
    "ICICIBANK_indicators.csv"
)

df.to_csv(

    output_path,

    index=False
)

print(f"\nSaved to: {output_path}")

print(

    "\nIndicator generation "
    "completed successfully."
)