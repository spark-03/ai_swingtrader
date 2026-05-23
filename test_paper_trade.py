from strategy.scanner import scan_market
from execution.paper_trader import execute_paper_trade


results = scan_market()

print("\nSCAN RESULTS:\n")

for stock in results:

    print(stock)

# Take top stock
if len(results) > 0:

    top_stock = results[0]

    print("\nEXECUTING PAPER TRADE...\n")

    trade = execute_paper_trade(top_stock)

    print(trade)

else:

    print("\nNo strong stocks found.")