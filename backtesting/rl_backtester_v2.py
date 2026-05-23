import torch
import pandas as pd
import numpy as np

from rl.dqn_model import DQN
from risk.risk_manager import RiskManager

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
# CONFIG
# ====================================

SYMBOL = "ADANIGREEN-EQ"

INITIAL_BALANCE = 100000

POSITION_SIZE_PERCENT = 0.20

BROKERAGE = 40

SLIPPAGE = 0.001

MIN_HOLD_STEPS = 20

COOLDOWN_STEPS = 10


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
# BUILD SAMPLE STATE
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


# ====================================
# RISK MANAGER
# ====================================

risk_manager = RiskManager(

    stop_loss_percent=0.02,

    take_profit_percent=0.05,

    trailing_stop_percent=0.01,

    max_hold_steps=200
)


# ====================================
# PORTFOLIO
# ====================================

balance = INITIAL_BALANCE

position = None

trade_history = []

portfolio_values = []

last_sell_step = -9999


# ====================================
# BACKTEST LOOP
# ====================================

START_STEP = 100

END_STEP = min(

    len(five_df),

    5000
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
    # DATA WINDOWS
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
    # CURRENT PRICE
    # ====================================

    current_price = five_df.iloc[

        step
    ]["close"]

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

    # ====================================
    # PORTFOLIO FEATURES
    # ====================================

    portfolio_features = np.array([

        balance / INITIAL_BALANCE,

        0 if position is None else 1,

        portfolio_value / INITIAL_BALANCE
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
    # MODEL ACTION
    # ====================================

    with torch.no_grad():

        q_values = model(

            state_tensor
        )

        action = torch.argmax(

            q_values
        ).item()

            # ====================================
    # AUTOMATIC RISK MANAGEMENT
    # ====================================

    if position is not None:

        risk_exit = risk_manager.check_exit(

            position,

            current_price,

            step
        )

        if risk_exit is not None:

            sell_value = (

                position["shares"]

                *

                current_price
            )

            sell_value -= BROKERAGE

            sell_value *= (

                1 - SLIPPAGE
            )

            pnl = sell_value - (

                position["shares"]

                *

                position["entry_price"]
            )

            pnl_percent = (

                pnl

                /

                (

                    position["shares"]

                    *

                    position["entry_price"]
                )
            ) * 100

            balance += sell_value

            trade_history.append({

                "type": "RISK_EXIT",

                "price": current_price,

                "step": step,

                "pnl": pnl,

                "pnl_percent": pnl_percent,

                "holding_period": (

                    step

                    -

                    position["entry_step"]
                ),

                "exit_reason": risk_exit
            })

            position = None

            last_sell_step = step

            continue

    # ====================================
    # BUY
    # ====================================

    if (

        action == 1

        and

        position is None

        and

        (step - last_sell_step)

        >= COOLDOWN_STEPS
    ):

        allocation = (

            balance

            *

            POSITION_SIZE_PERCENT
        )

        if allocation > 1000:

            shares = allocation / current_price

            buy_cost = (

                allocation

                +

                BROKERAGE
            )

            buy_cost *= (

                1 + SLIPPAGE
            )

            if buy_cost <= balance:

                balance -= buy_cost

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

        if holding_period >= MIN_HOLD_STEPS:

            sell_value = (

                position["shares"]

                *

                current_price
            )

            sell_value -= BROKERAGE

            sell_value *= (

                1 - SLIPPAGE
            )

            pnl = sell_value - (

                position["shares"]

                *

                position["entry_price"]
            )

            pnl_percent = (

                pnl

                /

                (

                    position["shares"]

                    *

                    position["entry_price"]
                )
            ) * 100

            balance += sell_value

            trade_history.append({

                "type": "SELL",

                "price": current_price,

                "step": step,

                "pnl": pnl,

                "pnl_percent": pnl_percent,

                "holding_period": holding_period
            })

            position = None

            last_sell_step = step

    # ====================================
    # TRACK PORTFOLIO
    # ====================================

    current_value = balance

    if position is not None:

        current_value += (

            position["shares"]

            *

            current_price
        )

    portfolio_values.append(

        current_value
    )


# ====================================
# FINAL PORTFOLIO VALUE
# ====================================

final_value = portfolio_values[-1]

total_return = (

    (

        final_value

        -

        INITIAL_BALANCE
    )

    /

    INITIAL_BALANCE
) * 100


# ====================================
# TRADE ANALYSIS
# ====================================

sell_trades = [

    t for t in trade_history

    if t["type"] == "SELL"
]

wins = [

    t for t in sell_trades

    if t["pnl"] > 0
]

losses = [

    t for t in sell_trades

    if t["pnl"] <= 0
]

win_rate = 0

if len(sell_trades) > 0:

    win_rate = (

        len(wins)

        /

        len(sell_trades)
    ) * 100


# ====================================
# PROFIT FACTOR
# ====================================

gross_profit = sum(

    t["pnl"]

    for t in wins
)

gross_loss = abs(sum(

    t["pnl"]

    for t in losses
))

profit_factor = 0

if gross_loss > 0:

    profit_factor = (

        gross_profit

        /

        gross_loss
    )


# ====================================
# MAX DRAWDOWN
# ====================================

equity_series = pd.Series(

    portfolio_values
)

rolling_max = equity_series.cummax()

drawdown = (

    equity_series

    -

    rolling_max
) / rolling_max

max_drawdown = (

    drawdown.min()
) * 100


# ====================================
# AVERAGE HOLD
# ====================================

avg_hold = 0

if len(sell_trades) > 0:

    avg_hold = np.mean([

        t["holding_period"]

        for t in sell_trades
    ])


# ====================================
# RESULTS
# ====================================

print("\n========== RL BACKTEST V2 RESULTS ==========")

print(f"\nSymbol: {SYMBOL}")

print(f"Final Portfolio Value: {final_value:.2f}")

print(f"Total Return: {total_return:.2f}%")

print(f"Total Trades: {len(sell_trades)}")

print(f"Win Rate: {win_rate:.2f}%")

print(f"Profit Factor: {profit_factor:.2f}")

print(f"Max Drawdown: {max_drawdown:.2f}%")

print(f"Average Hold: {avg_hold:.2f} candles")

print(f"Ending Balance: {balance:.2f}")


# ====================================
# SAVE TRADES
# ====================================

trades_df = pd.DataFrame(

    trade_history
)

trades_df.to_csv(

    "rl_backtest_v2_trades.csv",

    index=False
)

print("\nSaved: rl_backtest_v2_trades.csv")