import os
import random

import torch
import numpy as np

from rl.dqn_model import DQN
from rl.replay_buffer import ReplayBuffer
from rl.dqn_trainer import DQNTrainer
from rl.multi_stock_environment import MultiStockEnvironment


# ====================================
# LOAD ALL STOCK FILES
# ====================================

DATA_FOLDER = "historical_data_indicators"

stock_files = {}

for file_name in os.listdir(DATA_FOLDER):

    if file_name.endswith(".parquet"):

        symbol = file_name.split("-")[0]

        stock_files[symbol] = os.path.join(

            DATA_FOLDER,

            file_name
        )

print(f"\nTotal Stocks Loaded: {len(stock_files)}")


# ====================================
# SETTINGS
# ====================================

EPISODES = 500

BATCH_SIZE = 64

TRAIN_AFTER_EVERY = 5

MAX_STEPS = 3000

EPSILON_START = 1.0

EPSILON_MIN = 0.05

EPSILON_DECAY = 0.992


# ====================================
# CREATE ENVIRONMENT
# ====================================

env = MultiStockEnvironment(

    stock_files=stock_files
)

print("\nEnvironment Created")


# ====================================
# GET STATE SIZE
# ====================================

sample_state = env.reset()

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
# REPLAY BUFFER
# ====================================

buffer = ReplayBuffer(

    max_size=500000
)

print("\nReplay Buffer Created")


# ====================================
# TRAINER
# ====================================

trainer = DQNTrainer(

    model=model,

    replay_buffer=buffer
)

print("\nDDQN Trainer Created")


# ====================================
# EPSILON
# ====================================

epsilon = EPSILON_START


# ====================================
# TRACK BEST RESULT
# ====================================

best_pnl = -999999


# ====================================
# TRAINING LOOP
# ====================================

for episode in range(EPISODES):

    state = env.reset()

    done = False

    total_reward = 0

    steps = 0

    losses = []

    print(f"\n========== Episode {episode + 1} ==========")

    print(f"Stock: {env.current_symbol}")

    while not done and steps < MAX_STEPS:

        # ====================================
        # EPSILON GREEDY
        # ====================================

        if random.random() < epsilon:

            action = random.randint(0, 2)

        else:

            state_tensor = torch.FloatTensor(

                state

            ).unsqueeze(0)

            with torch.no_grad():

                q_values = model(state_tensor)

            action = torch.argmax(

                q_values

            ).item()

        # ====================================
        # STEP
        # ====================================

        next_state, reward, done = env.step(

            action
        )

        # ====================================
        # STORE EXPERIENCE
        # ====================================

        buffer.store(

            state,

            action,

            reward,

            next_state,

            done
        )

        # ====================================
        # TRAIN
        # ====================================

        if buffer.size() >= BATCH_SIZE:

            if steps % TRAIN_AFTER_EVERY == 0:

                loss = trainer.train_step(

                    BATCH_SIZE
                )

                if loss is not None:

                    losses.append(loss)

        # ====================================
        # UPDATE
        # ====================================

        state = next_state

        total_reward += reward

        steps += 1

        # ====================================
        # LOGGING
        # ====================================

        if steps % 500 == 0:

            print(

                f"Steps: {steps} | "

                f"Reward: {total_reward:.4f}"
            )

    # ====================================
    # EPSILON DECAY
    # ====================================

    epsilon = max(

        EPSILON_MIN,

        epsilon * EPSILON_DECAY
    )

    # ====================================
    # METRICS
    # ====================================

    metrics = env.get_metrics()

    avg_loss = (

        np.mean(losses)

        if len(losses) > 0 else 0
    )

    pnl = metrics["total_pnl"]

    print("\n========== EPISODE COMPLETE ==========")

    print(f"Steps: {steps}")

    print(f"Total Reward: {total_reward:.6f}")

    print(f"Average Loss: {avg_loss:.6f}")

    print(f"Epsilon: {epsilon:.4f}")

    print(f"Balance: {metrics['balance']:.2f}")

    print(f"PnL: {pnl:.2f}")

    print(f"Trades: {metrics['trades']}")

    # ====================================
    # SAVE BEST MODEL
    # ====================================

    if pnl > best_pnl:

        best_pnl = pnl

        torch.save(

            model.state_dict(),

            "best_sequential_rl_model.pth"
        )

        print("\nNEW BEST MODEL SAVED")

        print(f"Best PnL: {best_pnl:.2f}")


# ====================================
# SAVE FINAL MODEL
# ====================================

torch.save(

    model.state_dict(),

    "sequential_rl_model.pth"
)

print("\n========== TRAINING COMPLETE ==========")

print("Final Model Saved")

print(f"Best PnL Achieved: {best_pnl:.2f}")