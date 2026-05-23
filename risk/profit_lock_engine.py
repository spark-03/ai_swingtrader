class ProfitLockEngine:

    def __init__(self):

        pass

    # ====================================
    # CALCULATE LOCKED STOP
    # ====================================

    def calculate(

        self,

        entry_price,

        current_price
    ):

        profit_percent = (

            current_price

            -

            entry_price

        ) / entry_price

        # ====================================
        # DEFAULT RISK
        # ====================================

        locked_profit = -0.02

        # ====================================
        # BREAKEVEN
        # ====================================

        if profit_percent > 0.02:

            locked_profit = 0.00

        # ====================================
        # SMALL PROFIT LOCK
        # ====================================

        if profit_percent > 0.04:

            locked_profit = 0.015

        # ====================================
        # MEDIUM PROFIT LOCK
        # ====================================

        if profit_percent > 0.07:

            locked_profit = 0.035

        # ====================================
        # LARGE PROFIT LOCK
        # ====================================

        if profit_percent > 0.10:

            locked_profit = 0.06

        # ====================================
        # HUGE PROFIT LOCK
        # ====================================

        if profit_percent > 0.15:

            locked_profit = 0.10

        locked_stop = (

            entry_price

            *

            (1 + locked_profit)
        )

        return locked_stop