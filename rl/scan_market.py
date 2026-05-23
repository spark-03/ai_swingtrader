import os

import torch
import pandas as pd

from rl.dqn_model import DQN
from utils.state_builder import build_state


# ====================================
# DATA FOLDER
# ====================================

data_folder = "historical_data_indicators"


# ====================================
# GET STOCK FILES
# ====================================

files = [

    f for f in os.listdir(data_folder)

    if f.endswith(".parquet")
]

print(f"\nStocks Found: {len(files)}")


# ====================================
# LOAD SAMPLE FILE
# ====================================

sample_df = pd.read_parquet(

    os.path.join(
        data_folder,
        files[0]
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
        "sequential_rl_model.pth"
    )
)

model.eval()

print("\nRL Model Loaded")


# ====================================
# ACTION MAP
# ====================================

action_map = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# STORE RESULTS
# ====================================

results = []


# ====================================
# SCAN ALL STOCKS
# ====================================

for file_name in files:

    try:

        file_path = os.path.join(

            data_folder,

            file_name
        )

        df = pd.read_parquet(file_path)

        state = build_state(df)

        state_tensor = torch.FloatTensor(

            state

        ).unsqueeze(0)

        # ====================================
        # PREDICT
        # ====================================

        with torch.no_grad():

            q_values = model(state_tensor)

        q_values = q_values.numpy()[0]

        best_action = q_values.argmax()

        confidence = q_values[best_action]

        signal = action_map[best_action]

        # ====================================
        # SAVE RESULT
        # ====================================

        results.append({

            "symbol": file_name,

            "signal": signal,

            "confidence": float(confidence),

            "hold_q": float(q_values[0]),

            "buy_q": float(q_values[1]),

            "sell_q": float(q_values[2])
        })

        print(

            f"{file_name} | "

            f"{signal} | "

            f"Confidence: {confidence:.4f}"
        )

    except Exception as e:

        print(f"\nFAILED: {file_name}")

        print(e)


# ====================================
# FINAL RESULTS DATAFRAME
# ====================================

results_df = pd.DataFrame(results)


# ====================================
# SORT BY CONFIDENCE
# ====================================

results_df = results_df.sort_values(

    by="confidence",

    ascending=False
)


# ====================================
# TOP PICKS
# ====================================

print("\n========== TOP RL PICKS ==========")

print(results_df.head(20))


# ====================================
# SAVE RESULTS
# ====================================

results_df.to_csv(

    "rl_market_scan.csv",

    index=False
)

print("\nSaved: rl_market_scan.csv")