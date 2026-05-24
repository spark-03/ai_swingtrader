class PortfolioManager:

    def __init__(

        self,

        initial_balance,

        brokerage_per_trade,

        slippage_percent
    ):

        self.initial_balance = (
            initial_balance
        )

        self.brokerage_per_trade = (
            brokerage_per_trade
        )

        self.slippage_percent = (
            slippage_percent
        )

    # ====================================
    # CLOSE POSITION
    # ====================================

    def close_position(

        self,

        positions,

        trade_history,

        balance,

        symbol,

        current_price,

        current_step,

        exit_reason
    ):

        position = positions[symbol]

        shares = position[
            "remaining_shares"
        ]

        sell_value = (

            shares

            *

            current_price
        )

        sell_value -= (
            self.brokerage_per_trade
        )

        sell_value *= (
            1 - self.slippage_percent
        )

        pnl = sell_value - (

            shares

            *

            position["entry_price"]
        )

        balance += sell_value

        trade_history.append({

            "symbol": symbol,

            "entry_price":
            position["entry_price"],

            "exit_price":
            current_price,

            "pnl": pnl,

            "holding_period": (

                current_step

                -

                position["entry_step"]
            ),

            "exit_reason":
            exit_reason
        })

        del positions[symbol]

        return (

            pnl,

            balance
        )

    # ====================================
    # PORTFOLIO VALUE
    # ====================================

    def calculate_portfolio_value(

        self,

        balance,

        positions,

        five_data,

        current_step
    ):

        positions_value = 0

        for symbol, position in positions.items():

            latest_price = five_data[
                symbol
            ].iloc[
                min(

                    current_step,

                    len(
                        five_data[symbol]
                    ) - 1
                )
            ]["close"]

            positions_value += (

                position["remaining_shares"]

                *

                latest_price
            )

        return (

            balance

            +

            positions_value
        )