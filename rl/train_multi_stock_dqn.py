import numpy as np
import pandas as pd
import torch

from rl.replay_buffer import ReplayBuffer
from rl.dqn_model import DQN
from rl.dqn_trainer import DQNTrainer


# ====================================
# SETTINGS
# ====================================

SAMPLE_SIZE = 5000

BATCH_SIZE = 16

EPISODES = 3

TRAINING_STEPS = 50


# ====================================
# LOAD DATASET
# ====================================

dataset_path = "multi_stock_rl_dataset.parquet"

df = pd.read_parquet(
    dataset_path
)

print("Dataset Loaded")

print(f"Total Rows: {len(df)}")


# ====================================
# SAMPLE DATA
# ====================================

df = df.sample(
    n=SAMPLE_SIZE,
    random_state=42
)

df.reset_index(
    drop=True,
    inplace=True
)

print(f"\nSampled Rows: {len(df)}")


# ====================================
# CREATE REPLAY BUFFER
# ====================================

buffer = ReplayBuffer()

print("\nReplay Buffer Created")


# ====================================
# LOAD EXPERIENCES
# ====================================

for _, row in df.iterrows():

    buffer.store(

        row["state"],

        row["action"],

        row["reward"],

        row["next_state"],

        row["done"]
    )

print("\nExperiences Loaded")

print(f"Buffer Size: {buffer.size()}")


# ====================================
# STATE SIZE
# ====================================

sample_state = df.iloc[0]["state"]

state_size = len(sample_state)

print(f"\nState Size: {state_size}")


# ====================================
# CREATE MODEL
# ====================================

model = DQN(

    state_size=state_size,

    action_size=3
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
# TRAINING LOOP
# ====================================

for episode in range(EPISODES):

    print(f"\n========== Episode {episode + 1} ==========")

    losses = []

    steps = 0

    while steps < TRAINING_STEPS:

        print(f"\nStep: {steps}")

        try:

            loss = trainer.train_step(
                BATCH_SIZE
            )

            print(f"Loss: {loss}")

            if loss is None:

                print("Loss is None")

                break

            if np.isnan(loss):

                print("NaN LOSS DETECTED")

                break

            losses.append(loss)

            steps += 1

        except Exception as e:

            print("\nTRAINING ERROR")

            print(e)

            break

    if len(losses) > 0:

        avg_loss = np.mean(losses)

        print(f"\nAverage Loss: {avg_loss:.6f}")

    else:

        print("\nNo Valid Losses")

# ====================================
# SAVE MODEL
# ====================================

model_path = "multi_stock_dqn.pth"

torch.save(

    model.state_dict(),

    model_path
)

print("\n========== TRAINING COMPLETE ==========")

print(f"Model Saved: {model_path}")