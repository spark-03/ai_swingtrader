import os
import pandas as pd
import tempfile
from datetime import datetime


def list_parquet_files(base_folder: str) -> list:
    """Return a sorted list of parquet file paths under *base_folder*.
    Files are assumed to be named <SYMBOL>_EQ_5m.parquet.
    """
    files = [os.path.join(base_folder, f) for f in os.listdir(base_folder) if f.endswith('.parquet')]
    files.sort()
    return files


def load_symbol_data(parquet_path: str) -> pd.DataFrame:
    """Load a parquet file for a single symbol and ensure a datetime column exists.
    The function attempts to locate a column named 'datetime', 'timestamp', or 'date'.
    It returns the DataFrame sorted chronologically.
    """
    df = pd.read_parquet(parquet_path)
    # Identify datetime column
    for col in ['datetime', 'timestamp', 'date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            df = df.sort_values(col).reset_index(drop=True)
            return df
    raise ValueError(f"No datetime column found in {parquet_path}")


def split_time_series(df: pd.DataFrame, train_months: int = 6, test_months: int = 3) -> tuple:
    """Split a DataFrame into train and test windows based on months.
    The split starts at the earliest date in *df*.
    Returns (train_df, test_df).
    """
    # Determine the start date
    time_col = [c for c in df.columns if c in ['datetime', 'timestamp', 'date']][0]
    start_date = df[time_col].iloc[0]
    train_end = start_date + pd.DateOffset(months=train_months)
    test_end = train_end + pd.DateOffset(months=test_months)
    train_df = df[(df[time_col] >= start_date) & (df[time_col] < train_end)]
    test_df = df[(df[time_col] >= train_end) & (df[time_col] < test_end)]
    return train_df, test_df


def temp_dir_from_df(df: pd.DataFrame) -> str:
    """Write *df* to a temporary directory as a single parquet file and return the directory path.
    The caller can pass this directory to scripts expecting a data folder.
    """
    tmp_dir = tempfile.mkdtemp()
    parquet_path = os.path.join(tmp_dir, 'data.parquet')
    df.to_parquet(parquet_path, index=False)
    return tmp_dir
