class PortfolioTracker:

    def __init__(self, starting_balance=100000):

        # ====================================
        # CAPITAL
        # ====================================

        self.starting_balance = float(starting_balance)

        self.balance = float(starting_balance)

        self.equity = float(starting_balance)

        # ====================================
        # PERFORMANCE
        # ====================================

        self.total_pnl = 0.0

        self.trade_count = 0

        self.win_count = 0

        self.loss_count = 0

    # ====================================
    # UPDATE PORTFOLIO
    # ====================================

    def update(self, pnl):

        pnl = float(pnl)

        self.total_pnl += pnl

        self.balance += pnl

        self.equity = self.balance

        self.trade_count += 1

        if pnl > 0:

            self.win_count += 1

        elif pnl < 0:

            self.loss_count += 1

    # ====================================
    # GET METRICS
    # ====================================

    def get_metrics(self):

        win_rate = 0.0

        if self.trade_count > 0:

            win_rate = (
                self.win_count /
                self.trade_count
            ) * 100

        return {

            "starting_balance": self.starting_balance,

            "balance": self.balance,

            "equity": self.equity,

            "total_pnl": self.total_pnl,

            "trade_count": self.trade_count,

            "win_count": self.win_count,

            "loss_count": self.loss_count,

            "win_rate": win_rate
        }