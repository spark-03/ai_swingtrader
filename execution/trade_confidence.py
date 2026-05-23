class TradeConfidenceEngine:

    def __init__(self):

        pass

    # ====================================
    # CALCULATE CONFIDENCE
    # ====================================

    def calculate(

        self,

        market_quality_score,

        rsi,

        bullish_alignment,

        volatility_ratio
    ):

        confidence = 0.0

        # ====================================
        # MARKET QUALITY
        # ====================================

        if market_quality_score > 25:

            confidence += 0.35

        elif market_quality_score > 18:

            confidence += 0.20

        # ====================================
        # RSI MOMENTUM
        # ====================================

        if rsi > 70:

            confidence += 0.25

        elif rsi > 60:

            confidence += 0.15

        elif rsi > 55:

            confidence += 0.10

        # ====================================
        # TREND ALIGNMENT
        # ====================================

        if bullish_alignment:

            confidence += 0.25

        # ====================================
        # VOLATILITY PENALTY
        # ====================================

        if volatility_ratio > 0.05:

            confidence -= 0.25

        elif volatility_ratio > 0.03:

            confidence -= 0.10

        # ====================================
        # CLAMP
        # ====================================

        confidence = max(0.0, confidence)

        confidence = min(1.0, confidence)

        return confidence