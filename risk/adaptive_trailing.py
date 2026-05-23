class AdaptiveTrailingEngine:

    def __init__(self):

        pass

    # ====================================
    # CALCULATE TRAILING STOP
    # ====================================

    def calculate(

        self,

        entry_price,

        current_price,

        atr,

        confidence,

        market_quality
    ):

        profit_percent = (

            current_price

            -

            entry_price

        ) / entry_price

        # ====================================
        # BASE ATR MULTIPLIER
        # ====================================

        atr_multiplier = 1.5

        # ====================================
        # HIGH CONFIDENCE
        # ====================================

        if confidence > 0.7:

            atr_multiplier += 1.0

        elif confidence > 0.5:

            atr_multiplier += 0.5

        # ====================================
        # STRONG MARKET QUALITY
        # ====================================

        if market_quality > 25:

            atr_multiplier += 0.5

        # ====================================
        # LOCK PROFITS
        # ====================================

        if profit_percent > 0.05:

            atr_multiplier -= 0.5

        if profit_percent > 0.10:

            atr_multiplier -= 0.5

        trailing_stop = (

            current_price

            -

            atr * atr_multiplier
        )

        return trailing_stop
