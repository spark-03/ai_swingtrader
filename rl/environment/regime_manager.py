class RegimeManager:

    def __init__(

        self,

        market_regime_detector,

        trade_confidence_engine
    ):

        self.market_regime_detector = (
            market_regime_detector
        )

        self.trade_confidence_engine = (
            trade_confidence_engine
        )

    # ====================================
    # ANALYZE REGIME
    # ====================================

    def analyze(

        self,

        analysis,

        rsi,

        bullish_alignment,

        volatility_ratio,

        current_price,

        ema20,

        ema50
    ):

        confidence = (

            self.trade_confidence_engine
            .calculate(

                analysis["quality_score"],

                rsi,

                bullish_alignment,

                volatility_ratio
            )
        )

        regime = (

            self.market_regime_detector
            .detect(

                current_price,

                ema20,

                ema50,

                volatility_ratio
            )
        )

        # ====================================
        # REGIME FILTERS
        # ====================================

        if regime == "trending":

            confidence += 0.10

        elif regime == "volatile":

            confidence -= 0.10

        elif regime == "choppy":

            confidence -= 0.15

        return (

            confidence,

            regime
        )