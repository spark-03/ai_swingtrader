class PositionSizer:

    def __init__(

        self,

        min_size=0.05,

        max_size=0.30
    ):

        self.min_size = min_size

        self.max_size = max_size

    # ====================================
    # CALCULATE POSITION SIZE
    # ====================================

    def calculate(

        self,

        market_quality_score,

        volatility_ratio,

        bullish_alignment
    ):

        # ====================================
        # BASE SIZE
        # ====================================

        size = 0.10

        # ====================================
        # MARKET QUALITY BOOST
        # ====================================

        if market_quality_score > 25:

            size += 0.10

        elif market_quality_score > 18:

            size += 0.05

        # ====================================
        # BULLISH ALIGNMENT BOOST
        # ====================================

        if bullish_alignment:

            size += 0.05

        # ====================================
        # HIGH VOLATILITY REDUCTION
        # ====================================

        if volatility_ratio > 0.03:

            size -= 0.05

        if volatility_ratio > 0.05:

            size -= 0.10

        # ====================================
        # CLAMP
        # ====================================

        size = max(

            self.min_size,

            size
        )

        size = min(

            self.max_size,

            size
        )

        return size