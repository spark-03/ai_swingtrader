import os
import random

import pandas as pd

from rl.environment import TradingEnvironment


# ====================================
# INPUT FOLDER
# ====================================

input_folder = "historical_data_indicators"


# ====================================
# GET ALL STOCK FILES
# ====================================

files = [

    f for f in os.listdir(input_folder)

    if f.endswith(".parquet")
]

print(f"\nFound {len(files)} stocks")


# ====================================
# MASTER DATASET
# ====================================

all_experiences = []


# ====================================
# PROCESS EACH STOCK
# ====================================

for file_name in files:

    print(f"\n========== {file_name} ==========")

    try:

        # ====================================
        # LOAD STOCK DATA
        # ====================================

        file_path = os.path.join(

            input_folder,

            file_name
        )

        df = pd.read_parquet(file_path)

        print("Data Loaded")

        print(f"Rows: {len(df)}")


        # ====================================
        # CREATE ENVIRONMENT
        # ====================================

        env = TradingEnvironment(df)

        state = env.reset()

        done = False

        step_count = 0


        # ====================================
        # EPISODE LOOP
        # ====================================

        while not done:

            # ====================================
            # RANDOM ACTION
            # ====================================

            action = random.randint(0, 2)

            # ====================================
            # ENVIRONMENT STEP
            # ====================================

            next_state, reward, done = env.step(action)

            # ====================================
            # STORE EXPERIENCE
            # ====================================

            all_experiences.append({

                "symbol": file_name,

                "state": state.tolist(),

                "action": action,

                "reward": reward,

                "next_state": next_state.tolist(),

                "done": done
            })

            # ====================================
            # UPDATE STATE
            # ====================================

            state = next_state

            step_count += 1

        print(f"Experiences Generated: {step_count}")

    except Exception as e:

        print("FAILED")

        print(e)


# ====================================
# CREATE FINAL DATAFRAME
# ====================================

dataset_df = pd.DataFrame(

    all_experiences
)

print("\n========== FINAL DATASET ==========")

print(dataset_df.head())

print(f"\nTotal Experiences: {len(dataset_df)}")


# ====================================
# SAVE DATASET
# ====================================

output_path = "multi_stock_rl_dataset.parquet"

dataset_df.to_parquet(

    output_path,

    index=False
)

print(f"\nSaved Dataset: {output_path}")