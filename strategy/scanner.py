from strategy.filter_engine import passes_filters
from strategy.quant_engine import analyze_stock
from data.watchlist import WATCHLIST


def scan_market():

    results = []

    for symbol, token in WATCHLIST.items():

        try:
            result = analyze_stock(symbol, token)

            if result:
                from strategy.filter_engine import passes_filters

            if passes_filters(result):

             print(f"{symbol} PASSED FILTERS")

             results.append(result)
            else:

             print(f"{symbol} FAILED FILTERS")

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results