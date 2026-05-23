from strategy.scanner import scan_market
from utils.trade_logger import log_trade


results = scan_market()

print("\nSCAN RESULTS:\n")

for stock in results:

    print(stock)

# Pick top stock
if len(results) > 0:

    top_stock = results[0]

    print("\nTOP STOCK:\n")
    print(top_stock)

    # Create trade log
    trade_log = {

        "symbol": top_stock["symbol"],
        "signal": top_stock["signal"],
        "trend": top_stock["trend"],
        "score": top_stock["score"],
        "price": top_stock["price"]
    }

    # Save log
    log_trade(trade_log)

else:

    print("\nNo strong stocks found.")