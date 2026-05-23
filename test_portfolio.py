from backtesting.portfolio_backtester import (
    run_portfolio_backtest
)

from backtesting.performance_tracker import (
    analyze_performance
)

from backtesting.equity_curve import (
    build_equity_curve
)

from backtesting.drawdown import (
    calculate_drawdown
)


# Run portfolio backtest
trades = run_portfolio_backtest()

print("\nPORTFOLIO RESULTS:\n")

for trade in trades[:20]:

    print(trade)

# Portfolio performance
performance = analyze_performance(
    trades
)

print("\nPORTFOLIO PERFORMANCE:\n")

print(performance)

# Portfolio equity curve
equity_curve = build_equity_curve(
    trades
)

# Portfolio drawdown
max_drawdown = calculate_drawdown(
    equity_curve
)

print("\nPORTFOLIO MAX DRAWDOWN:\n")

print(f"{max_drawdown}%")