import os
import torch
import pandas as pd
import numpy as np

from rl.dqn_model import DQN
from utils.multi_timeframe_state_builder import (
    build_multi_timeframe_state
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
# STOCK TO BACKTEST
# ====================================

SYMBOL = "ADANIGREEN-EQ"


# ====================================
# LOAD DATA
# ====================================

daily_df = pd.read_parquet(

    f"data/features/daily/{SYMBOL}.parquet"
)

hourly_df = pd.read_parquet(

    f"data/features/hourly/{SYMBOL}.parquet"
)

five_df = pd.read_parquet(

    f"data/features/5min/{SYMBOL}.parquet"
)

print("\nData Loaded")


# ====================================
# STATE SIZE
# ====================================

portfolio_features = np.array([

    1.0,
    0.0,
    1.0
])

sample_state = build_multi_timeframe_state(

    daily_df.iloc[:100],

    hourly_df.iloc[:100],

    five_df.iloc[:100],

    portfolio_features
)

state_size = len(sample_state)

action_size = 3

print(f"\nState Size: {state_size}")


# ====================================
# LOAD MODEL
# ====================================

model = DQN(

    state_size,

    action_size
).to(device)

model.load_state_dict(

    torch.load(

        "portfolio_rl_model.pth",

        map_location=device
    )
)

model.eval()

print("\nRL Model Loaded")


# ====================================
# PORTFOLIO
# ====================================

initial_balance = 100000

balance = initial_balance

position = None

trade_history = []

portfolio_values = []


# ====================================
# BACKTEST LOOP
# ====================================

START_STEP = 100

END_STEP = min(

    len(five_df),

    3000
)

for step in range(

    START_STEP,

    END_STEP
):

    # ====================================
    # ALIGN TIMEFRAMES
    # ====================================

    daily_index = min(

        len(daily_df) - 1,

        max(50, step // 75)
    )

    hourly_index = min(

        len(hourly_df) - 1,

        max(50, step // 12)
    )

    five_index = step

    # ====================================
    # WINDOWS
    # ====================================

    daily_window = daily_df.iloc[

        :daily_index
    ]

    hourly_window = hourly_df.iloc[

        :hourly_index
    ]

    five_window = five_df.iloc[

        :five_index
    ]

    # ====================================
    # PORTFOLIO FEATURES
    # ====================================

    current_value = balance

    if position is not None:

        current_price = five_df.iloc[

            step
        ]["close"]

        current_value += (

            position["shares"]

            *

            current_price
        )

    portfolio_features = np.array([

        balance / initial_balance,

        0 if position is None else 1,

        current_value / initial_balance
    ])

    # ====================================
    # BUILD STATE
    # ====================================

    state = build_multi_timeframe_state(

        daily_window,

        hourly_window,

        five_window,

        portfolio_features
    )

    state_tensor = torch.FloatTensor(

        state
    ).unsqueeze(0).to(device)

    # ====================================
    # PREDICT ACTION
    # ====================================

    with torch.no_grad():

        q_values = model(

            state_tensor
        )

        action = torch.argmax(

            q_values
        ).item()

    current_price = five_df.iloc[

        step
    ]["close"]

    # ====================================
    # BUY
    # ====================================

    if action == 1 and position is None:

        allocation = balance * 0.20

        shares = allocation / current_price

        balance -= allocation

        position = {

            "entry_price": current_price,

            "shares": shares,

            "entry_step": step
        }

        trade_history.append({

            "type": "BUY",

            "price": current_price,

            "step": step
        })

    # ====================================
    # SELL
    # ====================================

    elif action == 2 and position is not None:

        holding_period = (

            step

            -

            position["entry_step"]
        )

        if holding_period >= 20:

            sell_value = (

                position["shares"]

                *

                current_price
            )

            pnl = sell_value - (

                position["shares"]

                *

                position["entry_price"]
            )

            balance += sell_value

            trade_history.append({

                "type": "SELL",

                "price": current_price,

                "step": step,

                "pnl": pnl,

                "holding_period": holding_period
            })

            position = None

    # ====================================
    # PORTFOLIO VALUE
    # ====================================

    portfolio_value = balance

    if position is not None:

        portfolio_value += (

            position["shares"]

            *

            current_price
        )

    portfolio_values.append(

        portfolio_value
    )


# ====================================
# RESULTS
# ====================================

final_value = portfolio_values[-1]

total_return = (

    (

        final_value

        -

        initial_balance
    )

    /

    initial_balance
) * 100

sell_trades = [

    t for t in trade_history

    if t["type"] == "SELL"
]

wins = [

    t for t in sell_trades

    if t["pnl"] > 0
]

win_rate = 0

if len(sell_trades) > 0:

    win_rate = (

        len(wins)

        /

        len(sell_trades)
    ) * 100


# ====================================
# PRINT RESULTS
# ====================================

print("\n========== RL BACKTEST RESULTS ==========")

print(f"\nSymbol: {SYMBOL}")

print(f"Final Portfolio Value: {final_value:.2f}")

print(f"Total Return: {total_return:.2f}%")

print(f"Total Trades: {len(sell_trades)}")

print(f"Win Rate: {win_rate:.2f}%")

print(f"Ending Balance: {balance:.2f}")


# ====================================
# SAVE TRADES
# ====================================

trades_df = pd.DataFrame(

    trade_history
)

trades_df.to_csv(

    "rl_backtest_trades.csv",

    index=False
)

print("\nSaved: rl_backtest_trades.csv")