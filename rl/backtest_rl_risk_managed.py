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

CONFIDENCE_THRESHOLD = 0.12

COOLDOWN_CANDLES = 5

MIN_HOLD_CANDLES = 3

MAX_HOLD_CANDLES = 20

STOP_LOSS = 0.015

TAKE_PROFIT = 0.03

TRAILING_STOP = 0.01


# ====================================
# ACTION MAP
# ====================================

ACTION_MAP = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# LOAD MODEL
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
# STOCK FILES
# ====================================

files = [

    f for f in os.listdir(DATA_FOLDER)

    if f.endswith(".parquet")
]


# ====================================
# BACKTEST LOOP
# ====================================

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

        highest_price = 0

        trades = []

        cooldown = 0

        hold_candles = 0

        skipped_signals = 0

        # ====================================
        # MAIN LOOP
        # ====================================

        for i in range(30, len(df) - 1):

            if cooldown > 0:

                cooldown -= 1

            current_df = df.iloc[:i+1]

            state = build_state(current_df)

            state_tensor = torch.FloatTensor(

                state

            ).unsqueeze(0)

            # ====================================
            # RL PREDICTION
            # ====================================

            with torch.no_grad():

                q_values = model(state_tensor)

            q_values = q_values.numpy()[0]

            action = np.argmax(q_values)

            confidence = q_values[action]

            signal = ACTION_MAP[action]

            current_price = df.iloc[i]["close"]

            next_price = df.iloc[i + 1]["close"]

            # ====================================
            # CONFIDENCE FILTER
            # ====================================

            if confidence < CONFIDENCE_THRESHOLD:

                skipped_signals += 1

                continue

            # ====================================
            # BUY LOGIC
            # ====================================

            if (

                signal == "BUY"

                and position is None

                and cooldown == 0
            ):

                position = "LONG"

                entry_price = current_price

                highest_price = current_price

                hold_candles = 0

            # ====================================
            # TRACK POSITION
            # ====================================

            if position == "LONG":

                hold_candles += 1

                highest_price = max(

                    highest_price,

                    current_price
                )

                pnl_pct = (

                    current_price -

                    entry_price

                ) / entry_price

                trailing_drawdown = (

                    highest_price -

                    current_price

                ) / highest_price

                # ====================================
                # STOP LOSS
                # ====================================

                stop_loss_hit = pnl_pct <= -STOP_LOSS

                # ====================================
                # TAKE PROFIT
                # ====================================

                take_profit_hit = pnl_pct >= TAKE_PROFIT

                # ====================================
                # TRAILING STOP
                # ====================================

                trailing_stop_hit = (

                    pnl_pct > 0

                    and trailing_drawdown >= TRAILING_STOP
                )

                # ====================================
                # RL EXIT
                # ====================================

                rl_exit = (

                    signal == "SELL"

                    and hold_candles >= MIN_HOLD_CANDLES
                )

                # ====================================
                # MAX HOLD EXIT
                # ====================================

                max_hold_exit = (

                    hold_candles >= MAX_HOLD_CANDLES
                )

                # ====================================
                # FINAL EXIT
                # ====================================

                if (

                    stop_loss_hit

                    or take_profit_hit

                    or trailing_stop_hit

                    or rl_exit

                    or max_hold_exit
                ):

                    pnl = TRADE_SIZE * pnl_pct

                    balance += pnl

                    trades.append(pnl)

                    position = None

                    cooldown = COOLDOWN_CANDLES

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

        max_win = max(trades) if trades else 0

        max_loss = min(trades) if trades else 0

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

            "avg_trade": round(avg_trade, 2),

            "max_win": round(max_win, 2),

            "max_loss": round(max_loss, 2),

            "skipped_signals": skipped_signals
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

print("\n========== RL RISK MANAGED RESULTS ==========")

print(results_df.head(20))


# ====================================
# SAVE RESULTS
# ====================================

results_df.to_csv(

    "rl_risk_managed_results.csv",

    index=False
)

print("\nSaved: rl_risk_managed_results.csv")