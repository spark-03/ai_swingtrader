def calculate_drawdown(equity_curve):

    peak_balance = equity_curve[0]["balance"]

    max_drawdown = 0

    for point in equity_curve:

        balance = point["balance"]

        # Update peak
        if balance > peak_balance:

            peak_balance = balance

        # Calculate drawdown
        drawdown = (
            (peak_balance - balance)
            / peak_balance
        ) * 100

        # Update max drawdown
        if drawdown > max_drawdown:

            max_drawdown = drawdown

    return round(max_drawdown, 2)