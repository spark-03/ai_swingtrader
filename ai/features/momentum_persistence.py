import pandas as pd

import numpy as np


class MomentumPersistence:

    def __init__(

        self,

        lookback=10
    ):

        self.lookback = lookback

    # ====================================
    # CALCULATE MOMENTUM PERSISTENCE
    # ====================================

    def calculate(

        self,

        df
    ):

        df = df.copy()

        # ====================================
        # PRICE CHANGE
        # ====================================

        df["price_change"] = (

            df["close"]

            .pct_change()
        )

        # ====================================
        # DIRECTION
        # ====================================

        df["direction"] = np.where(

            df["price_change"] > 0,

            1,

            -1
        )

        # ====================================
        # PERSISTENCE SCORE
        # ====================================

        persistence_scores = []

        for i in range(len(df)):

            if i < self.lookback:

                persistence_scores.append(0)

                continue

            window = df[
                "direction"
            ].iloc[

                i - self.lookback:i
            ]

            positive_moves = (
                (window == 1).sum()
            )

            negative_moves = (
                (window == -1).sum()
            )

            dominance = abs(

                positive_moves

                -

                negative_moves
            )

            persistence = (

                dominance

                / self.lookback
            )

            persistence_scores.append(
                persistence
            )

        df[
            "momentum_persistence"
        ] = persistence_scores

        # ====================================
        # TREND STRENGTH
        # ====================================

        df["trend_strength"] = (

            df["close"]

            .pct_change(self.lookback)

            .abs()
        )

        # ====================================
        # COMBINED SCORE
        # ====================================

        df["momentum_score"] = (

            df[
                "momentum_persistence"
            ]

            *

            df[
                "trend_strength"
            ]
        )

        df["momentum_score"] = (

            df["momentum_score"]

            .fillna(0)

            .clip(0, 1)
        )

        return df