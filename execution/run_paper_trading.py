import os

import pandas as pd
import torch

from execution.paper_trader import PaperTrader
from execution.trade_filter import TradeFilter

from utils.stock_ranker import StockRanker
from utils.state_builder import build_state

from rl.dqn_model import DQN


# ====================================
# SETTINGS
# ====================================

DATA_FOLDER = "historical_data_indicators"

TOP_STOCKS = 20


# ====================================
# LOAD STOCK RANKER
# ====================================

ranker = StockRanker(

    data_folder=DATA_FOLDER
)

ranked_df = ranker.rank_stocks()

top_stocks = ranked_df.head(

    TOP_STOCKS
)

print("\nTop Stocks Selected")


# ====================================
# LOAD SAMPLE FILE
# ====================================

sample_file = os.path.join(

    DATA_FOLDER,

    os.listdir(DATA_FOLDER)[0]
)

sample_df = pd.read_parquet(

    sample_file
)

sample_state = build_state(

    sample_df
)

state_size = len(sample_state)


# ====================================
# LOAD RL MODEL
# ====================================

model = DQN(

    state_size=state_size,

    action_size=3
)

model.load_state_dict(

    torch.load(
        "sequential_rl_model.pth"
    )
)

model.eval()

print("\nRL Model Loaded")


# ====================================
# ACTION MAP
# ====================================

ACTION_MAP = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# STORE RESULTS
# ====================================

results = []


# ====================================
# RUN RL ENGINE
# ====================================

for _, row in top_stocks.iterrows():

    symbol = row["symbol"]

    market_score = row["score"]

    try:

        # ====================================
        # FIND MATCHING FILE
        # ====================================

        matching_files = [

            f for f in os.listdir(DATA_FOLDER)

            if f.startswith(symbol)
        ]

        if len(matching_files) == 0:

            print(f"\nNo file found for {symbol}")

            continue

        file_path = os.path.join(

            DATA_FOLDER,

            matching_files[0]
        )

        # ====================================
        # LOAD DATA
        # ====================================

        df = pd.read_parquet(

            file_path
        )

        latest_price = df.iloc[-1]["close"]

        # ====================================
        # BUILD STATE
        # ====================================

        state = build_state(df)

        state_tensor = torch.FloatTensor(

            state

        ).unsqueeze(0)

        # ====================================
        # RL INFERENCE
        # ====================================

        with torch.no_grad():

            q_values = model(

                state_tensor
            )

        q_values = q_values.numpy()[0]

        best_action = q_values.argmax()

        confidence = float(

            q_values[best_action]
        )

        signal = ACTION_MAP[best_action]

        # ====================================
        # SAVE RESULT
        # ====================================

        results.append({

            "symbol": symbol,

            "signal": signal,

            "confidence": confidence,

            "market_score": market_score,

            "price": latest_price,

            "hold_q": float(q_values[0]),

            "buy_q": float(q_values[1]),

            "sell_q": float(q_values[2])
        })

        print(

            f"{symbol} | "

            f"{signal} | "

            f"Confidence: {confidence:.4f}"
        )

    except Exception as e:

        print(f"\nFAILED: {symbol}")

        print(e)


# ====================================
# CREATE RESULTS DF
# ====================================

results_df = pd.DataFrame(results)


# ====================================
# FILTER TRADES
# ====================================

trade_filter = TradeFilter(

    min_confidence=0.10,

    min_market_score=3,

    min_q_gap=0.01)

filtered_df = trade_filter.filter_trades(

    results_df
)

print("\n========== FILTERED AI PICKS ==========")

print(filtered_df)


# ====================================
# CREATE PAPER TRADER
# ====================================

paper_trader = PaperTrader(

    initial_balance=100000,

    risk_per_trade=0.1
)

print("\nPaper Trader Initialized")


# ====================================
# EXECUTE TRADES
# ====================================

for _, trade in filtered_df.iterrows():

    paper_trader.open_position(

        symbol=trade["symbol"],

        signal=trade["signal"],

        price=trade["price"],

        confidence=trade["confidence"]
    )


# ====================================
# SIMULATE EXITS
# ====================================

for symbol in list(

    paper_trader.positions.keys()
):

    position = paper_trader.positions[symbol]

    entry_price = position["entry_price"]

    # ====================================
    # SIMPLE EXIT SIMULATION
    # ====================================

    simulated_exit = (

        entry_price * 1.01
    )

    paper_trader.close_position(

        symbol,

        simulated_exit
    )


# ====================================
# METRICS
# ====================================

metrics = paper_trader.get_metrics()

print("\n========== PAPER TRADING RESULTS ==========")

print(f"Balance: {metrics['balance']:.2f}")

print(f"PnL: {metrics['total_pnl']:.2f}")

print(f"Trades: {metrics['total_trades']}")

print(f"Win Rate: {metrics['win_rate']:.2f}%")


# ====================================
# SAVE HISTORY
# ====================================

paper_trader.save_history()