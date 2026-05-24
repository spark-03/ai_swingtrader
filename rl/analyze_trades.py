import pandas as pd

# ====================================
# LOAD LOGS
# ====================================

df = pd.read_csv(

    "rl_trade_log.csv"
)

# ====================================
# BASIC CHECK
# ====================================

if len(df) == 0:

    print("\nNo trades found.")

    exit()

# ====================================
# SUMMARY
# ====================================

print("\n========== RL ANALYTICS ==========\n")

print(

    f"Total Trades: {len(df)}"
)

print(

    f"Win Rate: "

    f"{round(df['profitable'].mean() * 100, 2)}%"
)

print(

    f"Average PnL: "

    f"{round(df['pnl'].mean(), 2)}"
)

print(

    f"Total PnL: "

    f"{round(df['pnl'].sum(), 2)}"
)

# ====================================
# BEST STOCKS
# ====================================

print("\n========== BEST STOCKS ==========\n")

stock_stats = (

    df.groupby("symbol")["pnl"]

    .agg([

        "count",

        "mean",

        "sum"
    ])

    .sort_values(

        by="sum",

        ascending=False
    )
)

print(stock_stats.head(10))

# ====================================
# WORST STOCKS
# ====================================

print("\n========== WORST STOCKS ==========\n")

print(stock_stats.tail(10))

# ====================================
# EXIT ANALYSIS
# ====================================

print("\n========== EXIT ANALYSIS ==========\n")

exit_stats = (

    df.groupby("exit_reason")["pnl"]

    .agg([

        "count",

        "mean",

        "sum"
    ])
)

print(exit_stats)

# ====================================
# HOLDING ANALYSIS
# ====================================

print("\n========== HOLDING ANALYSIS ==========\n")

print(

    df["holding_steps"]

    .describe()
)

# ====================================
# CONFIDENCE ANALYSIS
# ====================================

print("\n========== CONFIDENCE ==========\n")

print(

    df[

        ["confidence", "pnl"]
    ].corr()
)

# ====================================
# MARKET QUALITY
# ====================================

print("\n========== MARKET QUALITY ==========\n")

print(

    df[

        ["market_quality", "pnl"]
    ].corr()
)

# ====================================
# BEST TRADES
# ====================================

print("\n========== BEST TRADES ==========\n")

print(

    df.sort_values(

        by="pnl",

        ascending=False
    )

    .head(10)
)

# ====================================
# WORST TRADES
# ====================================

print("\n========== WORST TRADES ==========\n")

print(

    df.sort_values(

        by="pnl",

        ascending=True
    )

    .head(10)
)