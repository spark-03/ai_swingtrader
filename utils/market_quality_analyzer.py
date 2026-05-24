import numpy as np


class MarketQualityAnalyzer:

    def __init__(self):

        pass

    # ====================================
    # ANALYZE MARKET QUALITY
    # ====================================

    def analyze(

        self,

        daily_df,

        hourly_df,

        five_df
    ):

        # Guard against empty dataframes – if any timeframe lacks data, return a neutral score.
        if daily_df.empty or hourly_df.empty or five_df.empty:
            return {"quality_score": 0.0, "tradable": False}
        daily = daily_df.iloc[-1]

        hourly = hourly_df.iloc[-1]

        five = five_df.iloc[-1]

        # ====================================
        # TREND STRENGTH
        # ====================================

        daily_trend = abs(

            daily["EMA20"]

            -

            daily["EMA50"]

        ) / daily["close"]

        hourly_trend = abs(

            hourly["EMA20"]

            -

            hourly["EMA50"]

        ) / hourly["close"]

        # ====================================
        # MOMENTUM
        # ====================================

        momentum_strength = abs(

            five["RSI"]

            -

            50

        ) / 50

        # ====================================
        # VOLATILITY QUALITY
        # ====================================

        atr_ratio = (

            five["ATR"]

            /

            five["close"]
        )

        # ====================================
        # TREND ALIGNMENT
        # ====================================

        aligned = (

            (

                daily["EMA20"]

                >

                daily["EMA50"]
            )

            ==

            (

                hourly["EMA20"]

                >

                hourly["EMA50"]
            )
        )

        alignment_score = 1 if aligned else 0

        # ====================================
        # VOLATILITY SCORE
        # ====================================

        volatility_score = 1

        if atr_ratio > 0.04:

            volatility_score = 0

        # ====================================
        # FINAL SCORE
        # ====================================

        quality_score = (

            daily_trend * 30

            +

            hourly_trend * 30

            +

            momentum_strength * 20

            +

            alignment_score * 10

            +

            volatility_score * 10
        )

        return {

            "quality_score":
            quality_score,

            "tradable":
            quality_score > 15
        }