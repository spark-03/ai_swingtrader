from strategy.scanner import scan_market

results = scan_market()

print("\nTop Ranked Stocks:\n")

for stock in results:

    print(
        f"{stock['symbol']} | "
        f"Signal: {stock['signal']} | "
        f"Trend: {stock['trend']} | "
        f"Score: {stock['score']}"
    )