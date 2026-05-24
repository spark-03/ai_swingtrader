import pandas as pd

import os


class TradeLogger:

    def __init__(

        self,

        log_file="rl_trade_log.csv"
    ):

        self.log_file = log_file

        # ====================================
        # CREATE FILE
        # ====================================

        if not os.path.exists(

            self.log_file
        ):

            df = pd.DataFrame(columns=[

                "symbol",

                "entry_price",

                "exit_price",

                "pnl",

                "reward",

                "confidence",

                "regime",

                "holding_steps",

                "exit_reason",

                "market_quality",

                "volatility_ratio",

                "profitable"
            ])

            df.to_csv(

                self.log_file,

                index=False
            )

    # ====================================
    # LOG TRADE
    # ====================================

    def log_trade(

        self,

        symbol,

        entry_price,

        exit_price,

        pnl,

        reward,

        confidence,

        regime,

        holding_steps,

        exit_reason,

        market_quality,

        volatility_ratio
    ):

        row = {

            "symbol":
            symbol,

            "entry_price":
            entry_price,

            "exit_price":
            exit_price,

            "pnl":
            pnl,

            "reward":
            reward,

            "confidence":
            confidence,

            "regime":
            regime,

            "holding_steps":
            holding_steps,

            "exit_reason":
            exit_reason,

            "market_quality":
            market_quality,

            "volatility_ratio":
            volatility_ratio,

            "profitable":
            pnl > 0
        }

        df = pd.DataFrame([row])

        df.to_csv(

            self.log_file,

            mode="a",

            header=False,

            index=False
        )