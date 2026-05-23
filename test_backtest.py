from data.load_historical_data import load_historical_data
from backtesting.backtester import run_backtest
from backtesting.performance_tracker import analyze_performance
from backtesting.trade_dataset import save_trades
from backtesting.equity_curve import build_equity_curve
from backtesting.drawdown import calculate_drawdown


# Load local CSV data
df = load_historical_data(
    "historical_data/ICICIBANK.csv"
)

# Run backtest
trades = run_backtest(df)

print("\nBACKTEST RESULTS:\n")

for trade in trades[:10]:

    print(trade)

# Analyze performance
performance = analyze_performance(trades)

print("\nPERFORMANCE SUMMARY:\n")

print(performance)

# Build equity curve
equity_curve = build_equity_curve(trades)

print("\nEQUITY CURVE:\n")

for point in equity_curve[:10]:

    print(point)

# Calculate drawdown
max_drawdown = calculate_drawdown(
    equity_curve
)

print("\nMAX DRAWDOWN:\n")

print(f"{max_drawdown}%")

# Save trades
save_trades(trades)