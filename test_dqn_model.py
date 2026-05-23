import torch
import pandas as pd

from rl.state_builder import StateBuilder
from rl.dqn_model import DQN


# ====================================
# LOAD DATA
# ====================================

df = pd.read_csv(
    "historical_data/ICICIBANK_indicators.csv"
)

print("Data Loaded")


# ====================================
# BUILD STATE
# ====================================

builder = StateBuilder()

row = df.iloc[-1]

state = builder.build_state(row)

print("\nState Shape:")

print(state.shape)


# ====================================
# CREATE MODEL
# ====================================

state_size = len(state)

action_size = 3

model = DQN(

    state_size=state_size,

    action_size=action_size
)

print("\nDQN Model Created")


# ====================================
# CONVERT STATE TO TENSOR
# ====================================

state_tensor = torch.FloatTensor(state)

state_tensor = state_tensor.unsqueeze(0)

print("\nTensor Shape:")

print(state_tensor.shape)


# ====================================
# PREDICT Q VALUES
# ====================================

q_values = model(state_tensor)

print("\nQ Values:")

print(q_values)


# ====================================
# BEST ACTION
# ====================================

best_action = torch.argmax(q_values).item()

print("\nBest Action:")

print(best_action)