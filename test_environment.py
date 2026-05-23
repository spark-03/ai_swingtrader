import pandas as pd

from rl.environment import TradingEnvironment


# ====================================
# LOAD DATA
# ====================================

df = pd.read_csv(
    "historical_data/ICICIBANK_indicators.csv"
)

print("Data Loaded")


# ====================================
# CREATE ENVIRONMENT
# ====================================

env = TradingEnvironment(df)

print("Environment Created")


# ====================================
# RESET ENVIRONMENT
# ====================================

state = env.reset()

print("\nInitial State:")

print(state)


# ====================================
# TEST BUY ACTION
# ====================================

print("\n========== BUY ACTION ==========")

next_state, reward, done = env.step(1)

print("Reward:", reward)

print("Done:", done)

print("Next State:")

print(next_state)


# ====================================
# TEST HOLD ACTION
# ====================================

print("\n========== HOLD ACTION ==========")

next_state, reward, done = env.step(0)

print("Reward:", reward)

print("Done:", done)

print("Next State:")

print(next_state)


# ====================================
# TEST SELL ACTION
# ====================================

print("\n========== SELL ACTION ==========")

next_state, reward, done = env.step(2)

print("Reward:", reward)

print("Done:", done)

print("Next State:")

print(next_state)


# ====================================
# TRADE HISTORY
# ====================================

print("\n========== TRADE HISTORY ==========")

print(env.get_trade_history())

print("\n========== PORTFOLIO METRICS ==========")

print(env.get_portfolio_metrics())