class MetricsManager:

    def __init__(self):

        pass

    # ====================================
    # METRICS
    # ====================================

    def calculate_metrics(

        self,

        portfolio_value,

        initial_balance,

        balance,

        trade_history,

        positions
    ):

        total_pnl = (

            portfolio_value

            -

            initial_balance
        )

        wins = [

            t for t in trade_history

            if t["pnl"] > 0
        ]

        win_rate = 0

        if len(trade_history) > 0:

            win_rate = (

                len(wins)

                /

                len(trade_history)
            ) * 100

        return {

            "portfolio_value":
            portfolio_value,

            "balance":
            balance,

            "pnl":
            total_pnl,

            "trades":
            len(trade_history),

            "win_rate":
            win_rate,

            "open_positions":
            len(positions)
        }