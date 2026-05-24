import pandas as pd

import numpy as np


class BreakoutPressure:

    def __init__(

        self,

        lookback=20
    ):

        self.lookback = lookback

    # ====================================
    # CALCULATE BREAKOUT PRESSURE
    # ====================================

    def calculate(

        self,

        df
    ):

        df = df.copy()

        # ====================================
        # ROLLING HIGH/LOW
        # ====================================

        df["rolling_high"] = (

            df["high"]

            .rolling(self.lookback)

            .max()
        )

        df["rolling_low"] = (

            df["low"]

            .rolling(self.lookback)

            .min()
        )

        # ====================================
        # RANGE WIDTH
        # ====================================

        df["range_width"] = (

            df["rolling_high"]

            -

            df["rolling_low"]
        )

        # ====================================
        # PRICE POSITION
        # ====================================

        df["price_position"] = (

            (

                df["close"]

                -

                df["rolling_low"]
            )

            /

            (

                df["range_width"]

                + 1e-9
            )
        )

        # ====================================
        # HIGHER LOW STRENGTH
        # ====================================

        low_trend = (

            df["low"]

            .rolling(5)

            .mean()

            .diff()
        )

        df["higher_low_strength"] = (

            low_trend

            .clip(lower=0)

            .fillna(0)
        )

        # ====================================
        # COMPRESSION FACTOR
        # ====================================

        avg_range = (

            df["range_width"]

            .rolling(self.lookback)

            .mean()
        )

        compression_factor = (

            1

            -

            (

                df["range_width"]

                /

                (

                    avg_range

                    + 1e-9
                )
            )
        )

        compression_factor = (

            compression_factor

            .clip(0, 1)

            .fillna(0)
        )

        # ====================================
        # BREAKOUT PRESSURE SCORE
        # ====================================

        breakout_pressure = (

            (
                df["price_position"]
            )

            *

            (
                compression_factor
            )

            *

            (
                1
                +
                df[
                    "higher_low_strength"
                ]
            )
        )

        breakout_pressure = (

            breakout_pressure

            .clip(0, 1)

            .fillna(0)
        )

        df[
            "breakout_pressure"
        ] = breakout_pressure

        return df