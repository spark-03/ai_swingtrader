import pandas as pd

from rl.dataset_generator import (
    RLDatasetGenerator
)


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

print(dataset.head())

print("\nDataset Shape:")

print(dataset.shape)