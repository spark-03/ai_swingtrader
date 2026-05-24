import argparse

# Argument parser for optional data folder and symbol name
parser = argparse.ArgumentParser(description='Train DQN on multi‑stock data')
parser.add_argument('--data', type=str, default='data/features/5min', help='Path to folder containing parquet files for training')
parser.add_argument('--symbol', type=str, default='generic', help='Symbol name for checkpoint naming')
args = parser.parse_args()

# Load dataset: concatenate all parquet files in the data folder
if os.path.isdir(args.data):
    parquet_files = [os.path.join(args.data, f) for f in os.listdir(args.data) if f.endswith('.parquet')]
    if not parquet_files:
        raise FileNotFoundError(f'No parquet files found in {args.data}')
    df_list = [pd.read_parquet(p) for p in parquet_files]
    df = pd.concat(df_list, ignore_index=True)
else:
    # Fallback to single parquet file path if a file is provided
    df = pd.read_parquet(args.data)

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

os.makedirs("models", exist_ok=True)
os.makedirs('models', exist_ok=True)
model_path = os.path.join('models', f"{args.symbol}_dqn.pth")

torch.save(

    model.state_dict(),

    model_path
)

print("\n========== TRAINING COMPLETE ==========")

print(f"Model Saved: {model_path}")