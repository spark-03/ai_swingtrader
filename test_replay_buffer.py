import pandas as pd

from rl.dataset_generator import (
    RLDatasetGenerator
)

from rl.replay_buffer import ReplayBuffer


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

print(dataset.shape)


# ====================================
# CREATE REPLAY BUFFER
# ====================================

buffer = ReplayBuffer()

print("\nReplay Buffer Created")


# ====================================
# STORE EXPERIENCES
# ====================================

for _, row in dataset.iterrows():

    buffer.store(

        row["state"],

        row["action"],

        row["reward"],

        row["next_state"],

        row["done"]
    )

print("\nExperiences Stored")


# ====================================
# BUFFER SIZE
# ====================================

print("\nBuffer Size:")

print(buffer.size())


# ====================================
# SAMPLE MINI-BATCH
# ====================================

sample = buffer.sample(5)

print("\nMini Batch Sample:\n")

for item in sample:

    print(item)