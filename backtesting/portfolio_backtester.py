import os

from data.load_historical_data import (
    load_historical_data
)

from backtesting.backtester import (
    run_backtest
)


def run_portfolio_backtest():

    all_trades = []

    data_folder = "historical_data"

    files = os.listdir(data_folder)

    for file in files:

        # Only CSV files
        if file.endswith(".csv"):

            file_path = (
                f"{data_folder}/{file}"
            )

            print(f"\nBacktesting {file}...")

            # Load stock data
            df = load_historical_data(
                file_path
            )

            # Run stock backtest
            trades = run_backtest(df)

            # Add stock name
            stock_name = (
                file.replace(".csv", "")
            )

            for trade in trades:

                trade["stock"] = stock_name

            # Combine trades
            all_trades.extend(trades)

    return all_trades