import os

import torch
import pandas as pd

from rl.dqn_model import DQN
from utils.state_builder import build_state
from utils.stock_ranker import StockRanker
from execution.trade_filter import TradeFilter


# ====================================
# SETTINGS
# ====================================

DATA_FOLDER = "historical_data_indicators"

TOP_STOCKS = 20

MIN_CONFIDENCE = 0.05


# ====================================
# ACTION MAP
# ====================================

ACTION_MAP = {

    0: "HOLD",

    1: "BUY",

    2: "SELL"
}


# ====================================
# LOAD STOCK RANKER
# ====================================

ranker = StockRanker(

    data_folder=DATA_FOLDER
)

print("\nStock Ranker Loaded")


# ====================================
# RANK STOCKS
# ====================================

ranked_df = ranker.rank_stocks()

print("\n========== TOP RANKED STOCKS ==========")

print(

    ranked_df.head(10)
)


# ====================================
# SELECT TOP STOCKS
# ====================================

top_stocks = ranked_df.head(

    TOP_STOCKS
)


# ====================================
# LOAD SAMPLE STATE
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

print(f"\nState Size: {state_size}")


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

print("\nDDQN Model Loaded")


# ====================================
# STORE RESULTS
# ====================================

results = []


# ====================================
# RUN RL INFERENCE
# ====================================

for _, row in top_stocks.iterrows():

    symbol = row["symbol"]

    score = row["score"]

    file_name = f"{symbol}-EQ_5m.parquet"

    file_path = os.path.join(

        DATA_FOLDER,

        file_name
    )

    try:

        df = pd.read_parquet(

            file_path
        )

        state = build_state(df)

        state_tensor = torch.FloatTensor(

            state

        ).unsqueeze(0)

        # ====================================
        # RL PREDICTION
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
        # FILTER WEAK SIGNALS
        # ====================================

        if confidence < MIN_CONFIDENCE:

            continue

        # ====================================
        # SAVE RESULT
        # ====================================

        results.append({

            "symbol": symbol,

            "signal": signal,

            "confidence": confidence,

            "market_score": float(score),

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
# FINAL RESULTS
# ====================================

results_df = pd.DataFrame(results)
# ====================================
# FILTER TRADES
# ====================================

trade_filter = TradeFilter()

results_df = trade_filter.filter_trades(

    results_df
)

results_df = results_df.sort_values(

    by=[

        "confidence",

        "market_score"

    ],

    ascending=False
)

print("\n========== FINAL AI TRADE PICKS ==========")

print(results_df.head(20))


# ====================================
# SAVE PICKS
# ====================================

results_df.to_csv(

    "ai_trade_picks.csv",

    index=False
)

print("\nSaved: ai_trade_picks.csv")