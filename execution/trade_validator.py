class TradeValidator:

    def __init__(self):

        pass

    # ====================================
    # VALIDATE BUY
    # ====================================

    def validate_buy(

        self,

        daily_df,

        hourly_df,

        five_df
    ):

        daily = daily_df.iloc[-1]

        hourly = hourly_df.iloc[-1]

        five = five_df.iloc[-1]

        # ====================================
        # DAILY TREND
        # ====================================

        daily_bullish = (

            daily["EMA20"]

            >

            daily["EMA50"]
        )

        # ====================================
        # HOURLY TREND
        # ====================================

        hourly_bullish = (

            hourly["EMA20"]

            >

            hourly["EMA50"]
        )

        # ====================================
        # MOMENTUM
        # ====================================

        momentum_good = (

            five["RSI"]

            >

            55
        )

        # ====================================
        # VOLATILITY FILTER
        # ====================================

        volatility_ok = (

            five["ATR"]

            /

            five["close"]

            <

            0.03
        )

        # ====================================
        # PRICE STRUCTURE
        # ====================================

        structure_good = (

            five["close"]

            >

            five["EMA20"]
        )

        # ====================================
        # FINAL DECISION
        # ====================================

        valid = all([

            daily_bullish,

            hourly_bullish,

            momentum_good,

            volatility_ok,

            structure_good
        ])

        return valid