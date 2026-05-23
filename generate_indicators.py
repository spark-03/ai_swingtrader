import pandas as pd

from strategy.add_indicators import add_indicators


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

print("\nIndicator generation completed successfully.")