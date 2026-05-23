import os

import torch
import pandas as pd
import numpy as np

from rl.dqn_model import DQN
from utils.state_builder import build_state


# ====================================
# SETTINGS
# ====================================

DATA_FOLDER = "historical_data_indicators"

INITIAL_BALANCE = 100000

TRADE_SIZE = 50000


# ====================================
# ACTION MAP
# ====================================

ACTION_MAP = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# LOAD SAMPLE FILE
# ====================================

sample_file = os.listdir(DATA_FOLDER)[0]

sample_df = pd.read_parquet(

    os.path.join(

        DATA_FOLDER,

        sample_file
    )
)

sample_state = build_state(sample_df)

state_size = len(sample_state)


# ====================================
# LOAD MODEL
# ====================================

model = DQN(

    state_size=state_size,

    action_size=3
)

model.load_state_dict(

    torch.load(

        "multi_stock_dqn.pth"
    )
)

model.eval()

print("\nRL Model Loaded")


# ====================================
# RESULTS
# ====================================

results = []


# ====================================
# BACKTEST ALL STOCKS
# ====================================

files = [

    f for f in os.listdir(DATA_FOLDER)

    if f.endswith(".parquet")
]


for file_name in files:

    try:

        print(f"\nBacktesting {file_name}...")

        file_path = os.path.join(

            DATA_FOLDER,

            file_name
        )

        df = pd.read_parquet(file_path)

        df = df.reset_index(drop=True)

        balance = INITIAL_BALANCE

        position = None

        entry_price = 0

        trades = []

        # ====================================
        # LOOP THROUGH CANDLES
        # ====================================

        for i in range(30, len(df) - 1):

            current_df = df.iloc[:i+1]

            state = build_state(current_df)

            state_tensor = torch.FloatTensor(

                state

            ).unsqueeze(0)

            # ====================================
            # MODEL PREDICTION
            # ====================================

            with torch.no_grad():

                q_values = model(state_tensor)

            action = torch.argmax(

                q_values

            ).item()

            signal = ACTION_MAP[action]

            current_price = df.iloc[i]["close"]

            next_price = df.iloc[i + 1]["close"]

            # ====================================
            # BUY LOGIC
            # ====================================

            if signal == "BUY" and position is None:

                position = "LONG"

                entry_price = current_price

            # ====================================
            # SELL LOGIC
            # ====================================

            elif signal == "SELL" and position == "LONG":

                pnl_pct = (

                    next_price -

                    entry_price

                ) / entry_price

                pnl = TRADE_SIZE * pnl_pct

                balance += pnl

                trades.append(pnl)

                position = None

        # ====================================
        # METRICS
        # ====================================

        total_pnl = balance - INITIAL_BALANCE

        trade_count = len(trades)

        wins = len([t for t in trades if t > 0])

        losses = len([t for t in trades if t <= 0])

        win_rate = (

            wins / trade_count * 100

            if trade_count > 0 else 0
        )

        avg_trade = (

            np.mean(trades)

            if trade_count > 0 else 0
        )

        # ====================================
        # SAVE RESULTS
        # ====================================

        results.append({

            "symbol": file_name,

            "total_pnl": round(total_pnl, 2),

            "trade_count": trade_count,

            "wins": wins,

            "losses": losses,

            "win_rate": round(win_rate, 2),

            "avg_trade": round(avg_trade, 2)
        })

        print(

            f"PnL: {total_pnl:.2f} | "

            f"Trades: {trade_count} | "

            f"Win Rate: {win_rate:.2f}%"
        )

    except Exception as e:

        print(f"\nFAILED: {file_name}")

        print(e)


# ====================================
# FINAL RESULTS
# ====================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(

    by="total_pnl",

    ascending=False
)

print("\n========== FINAL RL BACKTEST ==========")

print(results_df.head(20))


# ====================================
# SAVE RESULTS
# ====================================

results_df.to_csv(

    "rl_backtest_results.csv",

    index=False
)

print("\nSaved: rl_backtest_results.csv")