import pandas as pd
import os


def save_trades(trades):

    file_path = "logs/backtest_trades.csv"

    df = pd.DataFrame(trades)

    # Append if file exists
    if os.path.exists(file_path):

        df.to_csv(
            file_path,
            mode='a',
            header=False,
            index=False
        )

    # Create new file
    else:

        df.to_csv(
            file_path,
            index=False
        )

    print("\nTrades Saved Successfully")