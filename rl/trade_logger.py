class TradeLogger:

    def __init__(self):

        self.trades = []

    # ====================================
    # LOG TRADE
    # ====================================

    def log_trade(

        self,

        direction,

        entry_price,

        exit_price,

        pnl,

        holding_time

    ):

        trade = {

            "direction": str(direction),

            "entry_price": float(entry_price),

            "exit_price": float(exit_price),

            "pnl": float(pnl),

            "holding_time": int(holding_time)
        }

        self.trades.append(trade)

    # ====================================
    # GET TRADES
    # ====================================

    def get_trades(self):

        return self.trades