import os
import pandas as pd
import glob
import subprocess
from datetime import datetime
from utils.walk_forward_loader import load_symbol_data

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__FILE__), '..'))

DATA_ROOT = os.path.join(PROJECT_ROOT, 'data', 'features', '5min')
RESULTS_CSV = os.path.join(PROJECT_ROOT, 'rl', 'walk_forward_results.csv')

def get_parquet_files():
    """Return a sorted list of parquet file paths for Indian stocks."""
    pattern = os.path.join(DATA_ROOT, '*.parquet')
    files = glob.glob(pattern)
    files.sort()
    return files

def generate_walkforward_folds(df, train_months=6, test_months=3):
    """Create rolling train/test windows.
    Returns a list of (train_df, test_df) tuples.
    """
    time_col = [c for c in df.columns if c in ['datetime', 'timestamp', 'date']][0]
    df = df.sort_values(time_col).reset_index(drop=True)
    folds = []
    start_idx = 0
    total_len = len(df)
    while True:
        train_end_date = df[time_col].iloc[start_idx] + pd.DateOffset(months=train_months)
        test_end_date = train_end_date + pd.DateOffset(months=test_months)
        train_mask = (df[time_col] >= df[time_col].iloc[start_idx]) & (df[time_col] < train_end_date)
        test_mask = (df[time_col] >= train_end_date) & (df[time_col] < test_end_date)
        train_df = df[train_mask]
        test_df = df[test_mask]
        if len(train_df) == 0 or len(test_df) == 0:
            break
        folds.append((train_df, test_df))
        # advance start index to the first row of test period for next fold
        start_idx = df[time_col].searchsorted(train_end_date)
        if start_idx >= total_len:
            break
    return folds

def run_training(train_df, symbol):
    """Train DQN on a training DataFrame and save checkpoint.
    Uses utils/temp_dir_from_df to create a temporary parquet folder.
    """
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    # write training data to parquet
    train_path = os.path.join(tmpdir, 'train.parquet')
    train_df.to_parquet(train_path, index=False)
    # invoke training script with data folder and symbol name
    cmd = [
        "python",
        os.path.join(PROJECT_ROOT, 'rl', 'train_multi_stock_dqn.py'),
        "--data", tmpdir,
        "--symbol", symbol,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Training failed for {symbol}: {result.stderr}")
    # checkpoint path expected under models/<symbol>_dqn.ckpt
    checkpoint_path = os.path.join(PROJECT_ROOT, 'models', f"{symbol}_dqn.ckpt")
    return checkpoint_path

def run_backtest(test_df, checkpoint_path, symbol):
    """Run backtest on test DataFrame using provided checkpoint.
    Uses temporary folder to feed parquet data.
    """
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    test_path = os.path.join(tmpdir, 'test.parquet')
    test_df.to_parquet(test_path, index=False)
    cmd = [
        "python",
        os.path.join(PROJECT_ROOT, 'rl', 'backtest_rl_risk_managed.py'),
        "--data", tmpdir,
        "--checkpoint", checkpoint_path,
        "--symbol", symbol,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Backtest failed for {symbol}: {result.stderr}")
    backtest_csv = os.path.join(PROJECT_ROOT, 'rl', 'rl_risk_managed_results.csv')
    df = pd.read_csv(backtest_csv)
    row = df[df['symbol'] == symbol]
    return row

def main():
    all_files = get_parquet_files()
    if not all_files:
        print('No parquet files found in', DATA_ROOT)
        return
    # Group files by symbol (assuming filename starts with SYMBOL)
    symbol_to_files = {}
    for f in all_files:
        basename = os.path.basename(f)
        symbol = basename.split('_')[0]
        symbol_to_files.setdefault(symbol, []).append(f)

    results = []
    for symbol, files in symbol_to_files.items():
        print(f'Processing symbol {symbol} ({len(files)} files)')
        # Load full DataFrame for symbol
        parquet_path = files[0]  # assuming one file per symbol
        df = load_symbol_data(parquet_path)
        folds = generate_walkforward_folds(df, train_months=6, test_months=3)
        if not folds:
            print(f'Skipping {symbol}: insufficient data for any fold')
            continue
        for idx, (train_df, test_df) in enumerate(folds, start=1):
            print(f'  Fold {idx}: train {len(train_df)} rows, test {len(test_df)} rows')
            try:
                checkpoint = run_training(train_df, f"{symbol}_fold{idx}")
                row = run_backtest(test_df, checkpoint, symbol)
                if not row.empty:
                    # add fold identifier to results
                    row = row.copy()
                    row['fold'] = idx
                    results.append(row)
            except Exception as e:
                print('Error for', symbol, 'fold', idx, ':', e)
    if results:
        final_df = pd.concat(results, ignore_index=True)
        final_df.to_csv(RESULTS_CSV, index=False)
        print('Walk‑forward results saved to', RESULTS_CSV)
    else:
        print('No results generated.')


