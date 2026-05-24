class TradeManager:

    def __init__(

        self,

        trade_validator,

        position_sizer
    ):

        self.trade_validator = (
            trade_validator
        )

        self.position_sizer = (
            position_sizer
        )

    # ====================================
    # BUY EXECUTION
    # ====================================

    def execute_buy(

        self,

        symbol,

        positions,

        balance,

        max_positions,

        current_price,

        current_step,

        confidence,

        analysis,

        volatility_ratio,

        bullish_alignment,

        daily_df,

        hourly_df,

        five_df,

        brokerage_per_trade,

        slippage_percent
    ):

        reward = 0

        valid_trade = (

            self.trade_validator
            .validate_buy(

                daily_df,

                hourly_df,

                five_df
            )
        )

        if (

            valid_trade

            and

            confidence > 0.40

            and

            symbol not in positions

            and

            len(positions)
            < max_positions
        ):

            dynamic_position_size = (

                self.position_sizer
                .calculate(

                    analysis[
                        "quality_score"
                    ],

                    volatility_ratio,

                    bullish_alignment
                )
            )

            dynamic_position_size *= (
                0.5 + confidence
            )

            allocation = (

                balance

                *

                dynamic_position_size
            )

            if allocation > 1000:

                shares = (
                    allocation
                    / current_price
                )

                buy_cost = (

                    allocation

                    +

                    brokerage_per_trade
                )

                buy_cost *= (
                    1 + slippage_percent
                )

                if buy_cost <= balance:

                    balance -= buy_cost

                    positions[symbol] = {

                        "entry_price":
                        current_price,

                        "shares":
                        shares,

                        "remaining_shares":
                        shares,

                        "entry_step":
                        current_step,

                        "highest_price":
                        current_price,

                        "partial_exit_done":
                        False
                    }

                    reward -= 0.02

        return (

            balance,

            reward
        )

    # ====================================
    # SELL EXECUTION
    # ====================================

    def execute_sell(

        self,

        symbol,

        positions,

        current_step,

        minimum_holding_steps
    ):

        if symbol not in positions:

            return False, 0

        position = positions[symbol]

        holding_period = (

            current_step

            -

            position["entry_step"]
        )

        if (

            holding_period

            >=

            minimum_holding_steps
        ):

            return (

                True,

                holding_period
            )

        return False, holding_period