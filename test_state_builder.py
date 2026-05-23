import pandas as pd

from rl.state_builder import StateBuilder


# =========================
# LOAD ENRICHED DATA
# =========================

df = pd.read_csv(
    "historical_data/ICICIBANK_indicators.csv"
)

print("Columns:\n")

print(df.columns)


# =========================
# BUILD RL STATE
# =========================

builder = StateBuilder()

row = df.iloc[-1]

state = builder.build_state(row)

print("\nGenerated State:\n")

print(state)

print("\nState Shape:")

print(state.shape)