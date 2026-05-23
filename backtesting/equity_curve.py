def build_equity_curve(
    trades,
    starting_balance=100000
):

    balance = starting_balance

    equity_curve = []

    for trade in trades:

        pnl = trade["pnl"]

        capital = trade["capital"]

        # Position return %
        trade_return = pnl / trade["entry_price"]

        # Actual money gained/lost
        actual_pnl = capital * trade_return

        balance += actual_pnl

        equity_curve.append({

            "balance": round(balance, 2),

            "actual_pnl": round(actual_pnl, 2),

            "signal": trade["signal"],

            "market_regime": trade["market_regime"]
        })

    return equity_curve