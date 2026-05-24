class PositionSizer:

    def __init__(self):

        pass

    # ====================================
    # POSITION SIZE
    # ====================================

    def calculate(

        self,

        market_quality,

        volatility_ratio,

        bullish_alignment
    ):

        # ====================================
        # BASE SIZE
        # ====================================

        size = 0.08

        # ====================================
        # MARKET QUALITY
        # ====================================

        if market_quality > 35:

            size += 0.16

        elif market_quality > 25:

            size += 0.011

        elif market_quality > 15:

            size += 0.06

        # ====================================
        # BULLISH ALIGNMENT
        # ====================================

        if bullish_alignment:

            size += 0.04

        # ====================================
        # VOLATILITY REDUCTION
        # ====================================

        if volatility_ratio > 0.05:

            size *= 0.50

        elif volatility_ratio > 0.04:

            size *= 0.70

        elif volatility_ratio > 0.03:

            size *= 0.85

        # ====================================
        # HARD LIMITS
        # ====================================

        size = max(size, 0.03)

        size = min(size, 0.25)

        return size


def calculate_position_size(regime):
    """
    Backward-compatible helper used by backtesting pipeline.
    Maps regime labels to conservative position fractions.
    """
    regime_key = str(regime).upper()
    if regime_key in ("TRENDING", "TRENDING_BULL", "TRENDING_BEAR"):
        return 0.15
    if regime_key == "VOLATILE":
        return 0.07
    if regime_key == "LOW_VOLUME":
        return 0.05
    return 0.08
