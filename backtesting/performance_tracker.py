def analyze_performance(trades):

    total_trades = len(trades)

    winning_trades = 0
    losing_trades = 0

    total_profit = 0
    total_loss = 0

    total_pnl = 0

    pnl_list = []

    for trade in trades:

        pnl = trade["pnl"]

        pnl_list.append(pnl)

        total_pnl += pnl

        if pnl > 0:

            winning_trades += 1

            total_profit += pnl

        elif pnl < 0:

            losing_trades += 1

            total_loss += abs(pnl)

    # Win Rate
    if total_trades > 0:

        win_rate = (
            winning_trades / total_trades
        ) * 100

    else:

        win_rate = 0

    # Average Profit
    if winning_trades > 0:

        average_profit = (
            total_profit / winning_trades
        )

    else:

        average_profit = 0

    # Average Loss
    if losing_trades > 0:

        average_loss = (
            total_loss / losing_trades
        )

    else:

        average_loss = 0

    # Profit Factor
    if total_loss > 0:

        profit_factor = (
            total_profit / total_loss
        )

    else:

        profit_factor = 0

    # Expectancy
    expectancy = (
        (win_rate / 100) * average_profit
        -
        ((100 - win_rate) / 100) * average_loss
    )

    results = results = {

    "total_trades": int(total_trades),

    "winning_trades": int(winning_trades),
    "losing_trades": int(losing_trades),

    "win_rate": float(round(win_rate, 2)),

    "total_pnl": float(round(total_pnl, 2)),

    "average_profit": float(round(average_profit, 2)),
    "average_loss": float(round(average_loss, 2)),

    "profit_factor": float(round(profit_factor, 2)),

    "expectancy": float(round(expectancy, 2))
}

    return results