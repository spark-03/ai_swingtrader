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
        # DEFAULT
        # ====================================

        locked_profit = -0.02

        # ====================================
        # SMALL PROFITS
        # ====================================

        if profit_percent > 0.04:

            locked_profit = -0.005

        # ====================================
        # MEDIUM PROFITS
        # ====================================

        if profit_percent > 0.12:

            locked_profit = 0.015

        # ====================================
        # LARGE PROFITS
        # ====================================

        if profit_percent > 0.12:

            locked_profit = 0.04

        # ====================================
        # HUGE PROFITS
        # ====================================

        if profit_percent > 0.12:

            locked_profit = 0.08

        locked_stop = (

            entry_price

            *

            (1 + locked_profit)
        )

        return locked_stop

