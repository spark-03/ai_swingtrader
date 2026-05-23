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

MAX_STEPS = 3000


# ====================================
# ACTION MAP
# ====================================

ACTION_MAP = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# LOAD FILES
# ====================================

files = [

    f for f in os.listdir(DATA_FOLDER)

    if f.endswith(".parquet")
]

print(f"\nStocks Loaded: {len(files)}")


# ====================================
# SAMPLE STATE
# ====================================

sample_df = pd.read_parquet(

    os.path.join(
        DATA_FOLDER,
        files[0]
    )
)

sample_state = build_state(

    sample_df
)

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
        "sequential_rl_model.pth"
    )
)

model.eval()

print("\nRL Model Loaded")


# ====================================
# METRICS STORAGE
# ====================================

results = []


# ====================================
# EVALUATE EACH STOCK
# ====================================

for file_name in files:

    try:

        file_path = os.path.join(

            DATA_FOLDER,

            file_name
        )

        df = pd.read_parquet(

            file_path
        )

        position = None

        entry_price = 0

        total_pnl = 0

        buy_actions = 0

        sell_actions = 0

        hold_actions = 0

        profitable_trades = 0

        losing_trades = 0

        trades = 0

        holding_times = []

        hold_steps = 0

        confidence_scores = []

        # ====================================
        # WALK FORWARD
        # ====================================

        for step in range(

            120,

            min(len(df)-2, MAX_STEPS)
        ):

            current_df = df.iloc[:step+1]

            state = build_state(

                current_df
            )

            state_tensor = torch.FloatTensor(

                state

            ).unsqueeze(0)

            with torch.no_grad():

                q_values = model(

                    state_tensor
                )

            q_values = q_values.numpy()[0]

            best_action = q_values.argmax()

            confidence = float(

                q_values[best_action]
            )

            confidence_scores.append(

                confidence
            )

            action = ACTION_MAP[best_action]

            current_price = df.iloc[step]["close"]

            # ====================================
            # HOLD
            # ====================================

            if action == "HOLD":

                hold_actions += 1

                if position == "LONG":

                    hold_steps += 1

            # ====================================
            # BUY
            # ====================================

            elif action == "BUY":

                buy_actions += 1

                if position is None:

                    position = "LONG"

                    entry_price = current_price

                    hold_steps = 0

            # ====================================
            # SELL
            # ====================================

            elif action == "SELL":

                sell_actions += 1

                if position == "LONG":

                    pnl_pct = (

                        current_price -

                        entry_price

                    ) / entry_price

                    pnl = 50000 * pnl_pct

                    total_pnl += pnl

                    trades += 1

                    holding_times.append(

                        hold_steps
                    )

                    if pnl > 0:

                        profitable_trades += 1

                    else:

                        losing_trades += 1

                    position = None

                    entry_price = 0

                    hold_steps = 0

        # ====================================
        # METRICS
        # ====================================

        win_rate = 0

        if trades > 0:

            win_rate = (

                profitable_trades /

                trades
            ) * 100

        avg_holding = 0

        if len(holding_times) > 0:

            avg_holding = np.mean(

                holding_times
            )

        avg_confidence = np.mean(

            confidence_scores
        )

        results.append({

            "symbol": file_name,

            "pnl": total_pnl,

            "trades": trades,

            "win_rate": win_rate,

            "buy_actions": buy_actions,

            "sell_actions": sell_actions,

            "hold_actions": hold_actions,

            "avg_holding_steps": avg_holding,

            "avg_confidence": avg_confidence
        })

        print(

            f"{file_name} | "

            f"PnL: {total_pnl:.2f} | "

            f"Trades: {trades} | "

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

    by="pnl",

    ascending=False
)

print("\n========== FINAL RL EVALUATION ==========")

print(results_df.head(20))


# ====================================
# GLOBAL METRICS
# ====================================

print("\n========== GLOBAL METRICS ==========")

print(

    f"Total PnL: "

    f"{results_df['pnl'].sum():.2f}"
)

print(

    f"Average Win Rate: "

    f"{results_df['win_rate'].mean():.2f}%"
)

print(

    f"Average Trades: "

    f"{results_df['trades'].mean():.2f}"
)

print(

    f"Average Confidence: "

    f"{results_df['avg_confidence'].mean():.4f}"
)

print(

    f"Average Holding Time: "

    f"{results_df['avg_holding_steps'].mean():.2f}"
)


# ====================================
# SAVE RESULTS
# ====================================

results_df.to_csv(

    "rl_policy_evaluation.csv",

    index=False
)

print("\nSaved: rl_policy_evaluation.csv")