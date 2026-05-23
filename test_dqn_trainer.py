import pandas as pd

from rl.dataset_generator import (
    RLDatasetGenerator
)

from rl.replay_buffer import ReplayBuffer

from rl.dqn_model import DQN

from rl.dqn_trainer import DQNTrainer


# ====================================
# LOAD DATA
# ====================================

df = pd.read_csv(
    "historical_data/ICICIBANK_indicators.csv"
)

print("Data Loaded")


# ====================================
# GENERATE RL DATASET
# ====================================

generator = RLDatasetGenerator(df)

dataset = generator.generate()

print("\nRL Dataset Generated")


# ====================================
# CREATE REPLAY BUFFER
# ====================================

buffer = ReplayBuffer()

for _, row in dataset.iterrows():

    buffer.store(

        row["state"],

        row["action"],

        row["reward"],

        row["next_state"],

        row["done"]
    )

print("\nReplay Buffer Filled")


# ====================================
# CREATE DQN MODEL
# ====================================

state_size = len(dataset.iloc[0]["state"])

action_size = 3

model = DQN(

    state_size=state_size,

    action_size=action_size
)

print("\nDQN Model Created")


# ====================================
# CREATE TRAINER
# ====================================

trainer = DQNTrainer(

    model=model,

    replay_buffer=buffer
)

print("\nDQN Trainer Created")


# ====================================
# TRAINING STEP
# ====================================

loss = trainer.train_step(batch_size=32)

print("\nTraining Loss:")

print(loss)