import pandas as pd
import os


def log_trade(trade_data):

    file_path = "logs/trades.csv"

    # Convert dictionary to dataframe
    df = pd.DataFrame([trade_data])

    # If file already exists
    if os.path.exists(file_path):

        df.to_csv(
            file_path,
            mode='a',
            header=False,
            index=False
        )

    # First time file creation
    else:

        df.to_csv(
            file_path,
            index=False
        )

    print("Trade Logged Successfully")