import pandas as pd

import numpy as np


class VolatilityCompression:

    def __init__(

        self,

        lookback=20
    ):

        self.lookback = lookback

    # ====================================
    # CALCULATE COMPRESSION
    # ====================================

    def calculate(

        self,

        df
    ):

        df = df.copy()

        # ====================================
        # TRUE RANGE
        # ====================================

        df["range"] = (

            df["high"]

            -

            df["low"]
        )

        # ====================================
        # ATR NORMALIZATION
        # ====================================

        df["atr_ratio"] = (

            df["ATR"]

            /

            df["close"]
        )

        # ====================================
        # ROLLING VOLATILITY
        # ====================================

        df["rolling_volatility"] = (

            df["range"]

            .rolling(self.lookback)

            .std()
        )

        # ====================================
        # NORMALIZED VOLATILITY
        # ====================================

        df["volatility_score"] = (

            df["rolling_volatility"]

            /

            df["close"]
        )

        # ====================================
        # COMPRESSION SCORE
        # ====================================

        rolling_mean = (

            df["volatility_score"]

            .rolling(self.lookback)

            .mean()
        )

        compression_score = (

            1

            -

            (

                df["volatility_score"]

                /

                rolling_mean
            )
        )

        compression_score = (

            compression_score

            .clip(0, 1)

            .fillna(0)
        )

        df["compression_score"] = (
            compression_score
        )

        return df