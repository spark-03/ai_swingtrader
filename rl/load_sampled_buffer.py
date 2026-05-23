import pandas as pd

from rl.replay_buffer import ReplayBuffer


# ====================================
# SETTINGS
# ====================================

SAMPLE_SIZE = 100000


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
# RANDOM SAMPLE
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
# CREATE BUFFER
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