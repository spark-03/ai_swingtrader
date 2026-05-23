import torch
import pandas as pd

from rl.dqn_model import DQN
from utils.state_builder import build_state


# ====================================
# LOAD LATEST DATA
# ====================================

file_path = "historical_data_indicators/RELIANCE_5m.parquet"

df = pd.read_parquet(file_path)

print("Data Loaded")


# ====================================
# BUILD CURRENT STATE
# ====================================

state = build_state(df)

print("\nCurrent State:")

print(state)


# ====================================
# STATE SIZE
# ====================================

state_size = len(state)


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

print("\nModel Loaded")


# ====================================
# CONVERT STATE TO TENSOR
# ====================================

state_tensor = torch.FloatTensor(

    state
).unsqueeze(0)


# ====================================
# PREDICT Q VALUES
# ====================================

with torch.no_grad():

    q_values = model(state_tensor)

print("\nQ Values:")

print(q_values)


# ====================================
# GET BEST ACTION
# ====================================

action = torch.argmax(

    q_values

).item()


# ====================================
# ACTION MAP
# ====================================

action_map = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# FINAL SIGNAL
# ====================================

signal = action_map[action]

print("\n========== RL SIGNAL ==========")

print(f"Action: {signal}")