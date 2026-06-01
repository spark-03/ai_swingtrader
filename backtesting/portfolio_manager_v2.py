import pandas as pd
import numpy as np

INITIAL_CAPITAL = 1_000_000

WEIGHTS = [
    0.50,
    0.30,
    0.20
]

print("Loading TQS trades...")

df = pd.read_csv(
    "logs/tqs_live_v1_ranked.csv"
)

df["entry_date"] = pd.to_datetime(
    df["entry_date"]
)

# ======================================
# SORT BY DATE + TQS
# ======================================

df = df.sort_values(
    ["entry_date", "tqs_live"],
    ascending=[True, False]
)

# ======================================
# TOP 3 TRADES PER DATE
# ======================================

selected = []

for dt, group in df.groupby("entry_date"):

    top = group.head(3).copy()

    top["rank"] = range(
        1,
        len(top) + 1
    )

    selected.append(top)

selected = pd.concat(
    selected,
    ignore_index=True
)

print(
    f"\nSelected Trades: "
    f"{len(selected)}"
)

# ======================================
# PORTFOLIO
# ======================================

equity = INITIAL_CAPITAL

trade_log = []

equity_curve = []

for _, row in selected.iterrows():

    rank = int(
        row["rank"]
    )

    weight = WEIGHTS[
        min(
            rank - 1,
            len(WEIGHTS) - 1
        )
    ]

    capital = (
        equity * weight
    )

    trade_return = (
        row["final_return_80"]
        / 100.0
    )

    pnl = (
        capital
        * trade_return
    )

    equity += pnl

    trade_log.append({

        "trade_id":
            row["trade_id"],

        "symbol":
            row["symbol"],

        "entry_date":
            row["entry_date"],

        "tqs_live":
            row["tqs_live"],

        "rank":
            rank,

        "weight":
            weight,

        "capital":
            capital,

        "return_pct":
            row["final_return_80"],

        "pnl":
            pnl,

        "equity_after":
            equity

    })

    equity_curve.append({

        "entry_date":
            row["entry_date"],

        "equity":
            equity

    })

trades = pd.DataFrame(
    trade_log
)

curve = pd.DataFrame(
    equity_curve
)

# ======================================
# METRICS
# ======================================

wins = trades[
    trades["return_pct"] > 0
]

losses = trades[
    trades["return_pct"] < 0
]

if len(losses):

    profit_factor = (

        wins["pnl"].sum()

        /

        abs(
            losses["pnl"].sum()
        )

    )

else:

    profit_factor = np.inf

running_max = (
    curve["equity"]
    .cummax()
)

drawdown = (

    curve["equity"]
    -
    running_max

) / running_max

max_dd = (
    drawdown.min()
    * 100
)

print("\n=== PORTFOLIO V2 ===\n")

print(
    f"Initial Capital: "
    f"{INITIAL_CAPITAL:,.2f}"
)

print(
    f"Final Equity: "
    f"{equity:,.2f}"
)

print(
    f"Total Return %: "
    f"{((equity/INITIAL_CAPITAL)-1)*100:.2f}"
)

print(
    f"Trades: "
    f"{len(trades)}"
)

print(
    f"Win Rate: "
    f"{(trades['return_pct']>0).mean()*100:.2f}"
)

print(
    f"Average Trade Return: "
    f"{trades['return_pct'].mean():.2f}"
)

print(
    f"Median Trade Return: "
    f"{trades['return_pct'].median():.2f}"
)

print(
    f"Profit Factor: "
    f"{profit_factor:.4f}"
)

print(
    f"Max Drawdown %: "
    f"{max_dd:.2f}"
)

trades.to_csv(
    "logs/portfolio_manager_v2_trades.csv",
    index=False
)

curve.to_csv(
    "logs/portfolio_manager_v2_equity.csv",
    index=False
)

print("\nSaved:")
print(
    "logs/portfolio_manager_v2_trades.csv"
)
print(
    "logs/portfolio_manager_v2_equity.csv"
)