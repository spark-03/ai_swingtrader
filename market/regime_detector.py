class MarketRegimeDetector:

    def __init__(self):

        pass

    # ====================================
    # DETECT REGIME
    # ====================================

    def detect(

        self,

        price,

        ema_fast,

        ema_slow,

        atr_percent
    ):

        # ====================================
        # TRENDING MARKET
        # ====================================

        if (

            ema_fast > ema_slow

            and

            atr_percent < 0.03
        ):

            return "trending"

        # ====================================
        # VOLATILE MARKET
        # ====================================

        if atr_percent > 0.05:

            return "volatile"

        # ====================================
        # CHOPPY MARKET
        # ====================================

        if abs(

            ema_fast - ema_slow

        ) / price < 0.002:

            return "choppy"

        # ====================================
        # DEFAULT
        # ====================================

        return "neutral"
