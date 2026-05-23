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

        atr_multiplier = 2.0

        # ====================================
        # HIGH CONFIDENCE
        # ====================================

        if confidence > 0.75:

            atr_multiplier += 1.2

        elif confidence > 0.60:

            atr_multiplier += 0.8

        elif confidence > 0.45:

            atr_multiplier += 0.4

        # ====================================
        # MARKET QUALITY
        # ====================================

        if market_quality > 30:

            atr_multiplier += 0.8

        elif market_quality > 20:

            atr_multiplier += 0.4

        # ====================================
        # EARLY PROFIT LOCKING
        # ====================================

        if profit_percent > 0.02:

            atr_multiplier -= 0.4

        if profit_percent > 0.04:

            atr_multiplier -= 0.5

        if profit_percent > 0.06:

            atr_multiplier -= 0.6

        if profit_percent > 0.10:

            atr_multiplier -= 0.8

        # ====================================
        # MINIMUM TRAIL LIMIT
        # ====================================

        atr_multiplier = max(

            atr_multiplier,

            0.8
        )

        trailing_stop = (

            current_price

            -

            atr * atr_multiplier
        )

        # ====================================
        # BREAKEVEN PROTECTION
        # ====================================

        if profit_percent > 0.03:

            trailing_stop = max(

                trailing_stop,

                entry_price
            )

        return trailing_stop