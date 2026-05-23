import random

import torch
import pandas as pd

from rl.environment import TradingEnvironment
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
# CREATE ENVIRONMENT
# ====================================

env = TradingEnvironment(df)

print("Environment Created")


# ====================================
# STATE + ACTION SIZE
# ====================================

initial_state = env.reset()

state_size = len(initial_state)

action_size = 3

print("State Size:", state_size)

print("Action Size:", action_size)


# ====================================
# CREATE MODEL
# ====================================

model = DQN(

    state_size=state_size,

    action_size=action_size
)

print("DQN Model Created")


# ====================================
# REPLAY BUFFER
# ====================================

buffer = ReplayBuffer()

print("Replay Buffer Created")


# ====================================
# TRAINER
# ====================================

trainer = DQNTrainer(

    model=model,

    replay_buffer=buffer
)

print("DQN Trainer Created")


# ====================================
# RL PARAMETERS
# ====================================

episodes = 3

batch_size = 32

epsilon = 1.0

epsilon_decay = 0.995

epsilon_min = 0.01


# ====================================
# TRAINING LOOP
# ====================================

for episode in range(episodes):

    print(f"\n========== Episode {episode + 1} ==========")

    state = env.reset()

    total_reward = 0

    done = False

    step_count = 0

    max_steps = 500

    while not done and step_count < max_steps:

        print("Step:", step_count)

        # ====================================
        # EPSILON GREEDY ACTION
        # ====================================

        if random.random() < epsilon:

            action = random.randint(0, 2)

        else:

            state_tensor = torch.FloatTensor(
                state
            ).unsqueeze(0)

            q_values = model(state_tensor)

            action = torch.argmax(
                q_values
            ).item()

        # ====================================
        # ENVIRONMENT STEP
        # ====================================

        next_state, reward, done = env.step(action)

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
        # TRAIN MODEL
        # ====================================

        loss = trainer.train_step(batch_size)

        # ====================================
        # UPDATE STATE
        # ====================================

        state = next_state

        total_reward += reward

        step_count += 1

    # ====================================
    # EPSILON DECAY
    # ====================================

    epsilon = max(

        epsilon_min,

        epsilon * epsilon_decay
    )

    # ====================================
    # EPISODE RESULTS
    # ====================================

    print("\nEpisode Complete")

    print(f"Steps: {step_count}")

    print(f"Total Reward: {total_reward:.6f}")

    print(f"Epsilon: {epsilon:.4f}")

    if loss is not None:

        print(f"Loss: {loss:.6f}")


# ====================================
# FINAL PORTFOLIO
# ====================================

print("\n========== FINAL PORTFOLIO ==========")

print(env.get_portfolio_metrics())