class RiskManager:

    def __init__(

        self,

        stop_loss_percent=0.02,

        take_profit_percent=0.05,

        trailing_stop_percent=0.01,

        max_hold_steps=200
    ):

        self.stop_loss_percent = (

            stop_loss_percent
        )

        self.take_profit_percent = (

            take_profit_percent
        )

        self.trailing_stop_percent = (

            trailing_stop_percent
        )

        self.max_hold_steps = (

            max_hold_steps
        )

    # ====================================
    # CHECK EXIT CONDITIONS
    # ====================================

    def check_exit(

        self,

        position,

        current_price,

        current_step
    ):

        entry_price = position["entry_price"]

        highest_price = position.get(

            "highest_price",

            entry_price
        )

        holding_period = (

            current_step

            -

            position["entry_step"]
        )

        # ====================================
        # UPDATE HIGHEST PRICE
        # ====================================

        if current_price > highest_price:

            highest_price = current_price

            position["highest_price"] = (

                highest_price
            )

        # ====================================
        # CURRENT RETURN
        # ====================================

        current_return = (

            current_price

            -

            entry_price
        ) / entry_price

        # ====================================
        # TRAILING RETURN
        # ====================================

        trailing_return = (

            current_price

            -

            highest_price
        ) / highest_price

        # ====================================
        # STOP LOSS
        # ====================================

        if current_return <= (

            -self.stop_loss_percent
        ):

            return "STOP_LOSS"

        # ====================================
        # TAKE PROFIT
        # ====================================

        if current_return >= (

            self.take_profit_percent
        ):

            return "TAKE_PROFIT"

        # ====================================
        # TRAILING STOP
        # ====================================

        if trailing_return <= (

            -self.trailing_stop_percent
        ):

            return "TRAILING_STOP"

        # ====================================
        # MAX HOLD
        # ====================================

        if holding_period >= (

            self.max_hold_steps
        ):

            return "MAX_HOLD_EXIT"

        # ====================================
        # HOLD
        # ====================================

        return None

# PARTIAL EXIT SUPPORT
