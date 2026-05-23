import os

import torch
import numpy as np
import pandas as pd

from rl.dqn_model import DQN
from rl.multi_stock_environment import MultiStockEnvironment


# ====================================
# STOCK FILES
# ====================================

stock_files = {

    "BEL": "historical_data_indicators/BEL-EQ_5m.parquet",

    "SAIL": "historical_data_indicators/SAIL-EQ_5m.parquet",

    "TATASTEEL": "historical_data_indicators/TATASTEEL-EQ_5m.parquet",

    "SBIN": "historical_data_indicators/SBIN_5m.parquet",

    "NMDC": "historical_data_indicators/NMDC-EQ_5m.parquet"
}


# ====================================
# CREATE ENVIRONMENT
# ====================================

env = MultiStockEnvironment(

    stock_files=stock_files
)

print("\nEnvironment Created")


# ====================================
# STATE SIZE
# ====================================

sample_state = env.reset()

state_size = len(sample_state)

print(f"\nState Size: {state_size}")


# ====================================
# LOAD MODEL
# ====================================

model = DQN(

    state_size=state_size,

    action_size=3
)

model.load_state_dict(

    torch.load(
        "sequential_rl_model.pth"
    )
)

model.eval()

print("\nDDQN Model Loaded")


# ====================================
# ACTION MAP
# ====================================

action_map = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# RESULTS
# ====================================

results = []


# ====================================
# EVALUATE EACH STOCK
# ====================================

for symbol in stock_files.keys():

    print(f"\n========== Evaluating {symbol} ==========")

    # ====================================
    # FORCE STOCK
    # ====================================

    env.current_symbol = symbol

    env.df = env.data[symbol]

    env.current_step = 30

    env.balance = env.initial_balance

    env.position = None

    env.entry_price = 0

    env.hold_steps = 0

    env.done = False

    state = env._get_state()

    total_reward = 0

    trades = []

    buy_count = 0

    sell_count = 0

    hold_count = 0

    # ====================================
    # MAIN LOOP
    # ====================================

    while not env.done:

        state_tensor = torch.FloatTensor(

            state

        ).unsqueeze(0)

        # ====================================
        # PURE INFERENCE
        # ====================================

        with torch.no_grad():

            q_values = model(state_tensor)

        action = torch.argmax(

            q_values

        ).item()

        # ====================================
        # ACTION COUNTS
        # ====================================

        if action == 0:

            hold_count += 1

        elif action == 1:

            buy_count += 1

        elif action == 2:

            sell_count += 1

        # ====================================
        # STEP
        # ====================================

        next_state, reward, done = env.step(

            action
        )

        total_reward += reward

        state = next_state

    # ====================================
    # METRICS
    # ====================================

    metrics = env.get_metrics()

    pnl = metrics["total_pnl"]

    balance = metrics["balance"]

    # ====================================
    # SAVE RESULTS
    # ====================================

    results.append({

        "symbol": symbol,

        "pnl": round(pnl, 2),

        "balance": round(balance, 2),

        "total_reward": round(total_reward, 4),

        "buy_actions": buy_count,

        "sell_actions": sell_count,

        "hold_actions": hold_count
    })

    print(f"PnL: {pnl:.2f}")

    print(f"Reward: {total_reward:.4f}")

    print(f"BUY Actions: {buy_count}")

    print(f"SELL Actions: {sell_count}")

    print(f"HOLD Actions: {hold_count}")


# ====================================
# FINAL RESULTS
# ====================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(

    by="pnl",

    ascending=False
)

print("\n========== FINAL DDQN EVALUATION ==========")

print(results_df)


# ====================================
# SAVE CSV
# ====================================

results_df.to_csv(

    "ddqn_evaluation_results.csv",

    index=False
)

print("\nSaved: ddqn_evaluation_results.csv")