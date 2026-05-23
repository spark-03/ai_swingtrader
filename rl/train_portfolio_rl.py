import os
import random

import torch
import torch.nn as nn
import torch.optim as optim

import numpy as np
import pandas as pd

from rl.dqn_model import DQN

from rl.portfolio_environment import (
    PortfolioEnvironment
)

from rl.prioritized_replay_buffer import (
    PrioritizedReplayBuffer
)

# ====================================
# DEVICE
# ====================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print(f"\nUsing Device: {device}")

# ====================================
# CONFIG
# ====================================

EPISODES = 1000

BATCH_SIZE = 32

GAMMA = 0.99

LR = 0.0001

EPSILON = 1.0

EPSILON_MIN = 0.05

EPSILON_DECAY = 0.998

TARGET_UPDATE = 5

MAX_MEMORY = 20000

MAX_STEPS = 600

TRAIN_EVERY = 10

# ====================================
# DATA FOLDERS
# ====================================

DAILY_FOLDER = "data/features/daily"

HOURLY_FOLDER = "data/features/hourly"

FIVE_FOLDER = "data/features/5min"

# ====================================
# LOAD DATA
# ====================================

daily_data = {}

hourly_data = {}

five_data = {}

print("\nLoading Multi-Timeframe Data...")

# ====================================
# LOAD DAILY
# ====================================

for file_name in os.listdir(DAILY_FOLDER):

    if file_name.endswith(".parquet"):

        try:

            symbol = file_name.replace(
                ".parquet",
                ""
            )

            df = pd.read_parquet(
                os.path.join(
                    DAILY_FOLDER,
                    file_name
                )
            )

            if len(df) > 200:

                daily_data[symbol] = df

        except Exception as e:

            print(f"\nFAILED DAILY: {file_name}")

            print(e)

# ====================================
# LOAD HOURLY
# ====================================

for file_name in os.listdir(HOURLY_FOLDER):

    if file_name.endswith(".parquet"):

        try:

            symbol = file_name.replace(
                ".parquet",
                ""
            )

            df = pd.read_parquet(
                os.path.join(
                    HOURLY_FOLDER,
                    file_name
                )
            )

            if len(df) > 500:

                hourly_data[symbol] = df

        except Exception as e:

            print(f"\nFAILED HOURLY: {file_name}")

            print(e)

# ====================================
# LOAD 5MIN
# ====================================

for file_name in os.listdir(FIVE_FOLDER):

    if file_name.endswith(".parquet"):

        try:

            symbol = file_name.replace(
                ".parquet",
                ""
            )

            df = pd.read_parquet(
                os.path.join(
                    FIVE_FOLDER,
                    file_name
                )
            )

            if len(df) > 1000:

                five_data[symbol] = df

        except Exception as e:

            print(f"\nFAILED 5MIN: {file_name}")

            print(e)

# ====================================
# COMMON SYMBOLS
# ====================================

common_symbols = list(

    set(daily_data.keys())

    &

    set(hourly_data.keys())

    &

    set(five_data.keys())
)

print(f"\nCommon Symbols: {len(common_symbols)}")

# ====================================
# FILTER
# ====================================

daily_data = {

    s: daily_data[s]

    for s in common_symbols
}

hourly_data = {

    s: hourly_data[s]

    for s in common_symbols
}

five_data = {

    s: five_data[s]

    for s in common_symbols
}

# ====================================
# ENVIRONMENT
# ====================================

env = PortfolioEnvironment(

    daily_data=daily_data,

    hourly_data=hourly_data,

    five_data=five_data,

    initial_balance=100000,

    max_positions=5,

    brokerage_per_trade=40,

    slippage_percent=0.001,

    position_size_percent=0.20
)

print("\nMulti-Timeframe Environment Created")

# ====================================
# SAMPLE STATE
# ====================================

sample_state = env.reset()

state_size = len(sample_state)

action_size = 5

print(f"\nState Size: {state_size}")

# ====================================
# MODELS
# ====================================

policy_net = DQN(

    state_size,

    action_size

).to(device)

target_net = DQN(

    state_size,

    action_size

).to(device)

target_net.load_state_dict(

    policy_net.state_dict()
)

target_net.eval()

print("\nDQN Created")

# ====================================
# OPTIMIZER
# ====================================

optimizer = optim.Adam(

    policy_net.parameters(),

    lr=LR
)

loss_fn = nn.MSELoss()

# ====================================
# MEMORY
# ====================================

memory = PrioritizedReplayBuffer(

    MAX_MEMORY
)

# ====================================
# CHECKPOINT LOADING
# ====================================

start_episode = 1

epsilon = EPSILON

if os.path.exists(

    "portfolio_rl_model.pth"
):

    checkpoint = torch.load(

        "portfolio_rl_model.pth",

        map_location=device
    )

    policy_net.load_state_dict(

        checkpoint["model_state_dict"]
    )

    target_net.load_state_dict(

        policy_net.state_dict()
    )

    optimizer.load_state_dict(

        checkpoint["optimizer_state_dict"]
    )

    epsilon = checkpoint["epsilon"]

    start_episode = checkpoint["episode"] + 1

    print(

        f"\nResuming From Episode {start_episode}"
    )

# ====================================
# TRAIN STEP
# ====================================

def train_step():

    if len(memory) < BATCH_SIZE:

        return 0

    batch, indices, weights = memory.sample(

        BATCH_SIZE
    )

    states = []

    targets = []

    td_errors = []

    for state, action, reward, next_state, done in batch:

        state_tensor = torch.FloatTensor(
            state
        ).unsqueeze(0).to(device)

        next_tensor = torch.FloatTensor(
            next_state
        ).unsqueeze(0).to(device)

        current_q_values = policy_net(
            state_tensor
        )

        current_q = current_q_values.detach() \
            .cpu() \
            .numpy()[0]

        target_q = current_q.copy()

        if done:

            target_value = reward

        else:

            next_action = torch.argmax(

                policy_net(next_tensor)

            ).item()

            next_q = target_net(

                next_tensor

            )[0][next_action].item()

            target_value = (

                reward

                +

                GAMMA * next_q
            )

        td_error = abs(

            target_value

            -

            current_q[action]
        )

        td_errors.append(td_error)

        target_q[action] = target_value

        states.append(state)

        targets.append(target_q)

    states_tensor = torch.FloatTensor(

        np.array(states)

    ).to(device)

    targets_tensor = torch.FloatTensor(

        np.array(targets)

    ).to(device)

    predictions = policy_net(

        states_tensor
    )

    loss = loss_fn(

        predictions,

        targets_tensor
    )

    optimizer.zero_grad()

    loss.backward()

    optimizer.step()

    memory.update_priorities(

        indices,

        td_errors
    )

    return loss.item()

# ====================================
# TRAIN LOOP
# ====================================

best_pnl = -999999

for episode in range(

    start_episode,

    EPISODES + 1
):

    state = env.reset()

    total_reward = 0

    losses = []

    print(

        f"\n========== Episode "
        f"{episode} =========="
    )

    print(

        f"Stock: "
        f"{env.current_symbol}"
    )

    for step in range(MAX_STEPS):

        # ====================================
        # ACTION
        # ====================================

        if random.random() < epsilon:

            action = random.randint(

                0,

                action_size - 1
            )

        else:

            with torch.no_grad():

                state_tensor = torch.FloatTensor(
                    state
                ).unsqueeze(0).to(device)

                q_values = policy_net(
                    state_tensor
                )

                action = torch.argmax(
                    q_values
                ).item()

        # ====================================
        # ENV STEP
        # ====================================

        next_state, reward, done, _ = env.step(
            action
        )

        # ====================================
        # MEMORY
        # ====================================

        memory.push(

            state,

            action,

            reward,

            next_state,

            done
        )

        state = next_state

        total_reward += reward

        # ====================================
        # TRAIN
        # ====================================

        if step % TRAIN_EVERY == 0:

            loss = train_step()

            if loss > 0:

                losses.append(loss)

        # ====================================
        # LOGGING
        # ====================================

        if step % 300 == 0:

            print(

                f"Steps: {step} | "
                f"Reward: {total_reward:.4f}"
            )

        if done:

            break

    # ====================================
    # TARGET UPDATE
    # ====================================

    if episode % TARGET_UPDATE == 0:

        target_net.load_state_dict(

            policy_net.state_dict()
        )

        print("\nTarget Network Updated")

    # ====================================
    # EPSILON DECAY
    # ====================================

    if epsilon > EPSILON_MIN:

        epsilon *= EPSILON_DECAY

        epsilon = max(

            epsilon,

            EPSILON_MIN
        )

    # ====================================
    # METRICS
    # ====================================

    metrics = env.get_metrics()

    avg_loss = 0

    if len(losses) > 0:

        avg_loss = np.mean(losses)

    print("\n========== EPISODE COMPLETE ==========")

    print(f"Steps: {step}")

    print(f"Total Reward: {total_reward:.6f}")

    print(f"Average Loss: {avg_loss:.6f}")

    print(f"Epsilon: {epsilon:.4f}")

    print(f"Portfolio Value: {metrics['portfolio_value']:.2f}")

    print(f"PnL: {metrics['pnl']:.2f}")

    print(f"Trades: {metrics['trades']}")

    print(f"Win Rate: {metrics['win_rate']:.2f}%")

    print(f"Open Positions: {metrics['open_positions']}")

    # ====================================
    # SAVE BEST MODEL
    # ====================================

    if metrics["pnl"] > best_pnl:

        best_pnl = metrics["pnl"]

        checkpoint = {

            "episode": episode,

            "model_state_dict": policy_net.state_dict(),

            "optimizer_state_dict": optimizer.state_dict(),

            "epsilon": epsilon
        }

        torch.save(

            checkpoint,

            "portfolio_rl_model.pth"
        )

        print("\nBest Model Saved")

# ====================================
# TRAINING COMPLETE
# ====================================

print("\n========== TRAINING COMPLETE ==========")

print(

    f"\nBest PnL Achieved: "
    f"{best_pnl:.2f}"
)

checkpoint = {

    "episode": episode,

    "model_state_dict": policy_net.state_dict(),

    "optimizer_state_dict": optimizer.state_dict(),

    "epsilon": epsilon
}

torch.save(

    checkpoint,

    "portfolio_rl_model_final.pth"
)

print("\nFinal Model Saved")