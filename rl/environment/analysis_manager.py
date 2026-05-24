class AnalysisManager:

    def __init__(

        self,

        market_quality_analyzer,

        regime_manager
    ):

        self.market_quality_analyzer = (
            market_quality_analyzer
        )

        self.regime_manager = (
            regime_manager
        )

    # ====================================
    # ANALYZE MARKET
    # ====================================

    def analyze(

        self,

        env,

        current_row
    ):

        current_price = current_row[
            "close"
        ]

        atr = current_row["ATR"]

        rsi = current_row["RSI"]

        # ====================================
        # MARKET ANALYSIS
        # ====================================

        analysis = (

            self.market_quality_analyzer
            .analyze(

                env.daily_df.iloc[
                    :max(
                        50,
                        env.current_step // 75
                    )
                ],

                env.hourly_df.iloc[
                    :max(
                        50,
                        env.current_step // 12
                    )
                ],

                env.five_df.iloc[
                    :env.current_step
                ]
            )
        )

        # ====================================
        # BULLISH ALIGNMENT
        # ====================================

        bullish_alignment = (

            env.daily_df.iloc[
                max(
                    0,
                    env.current_step // 75
                )
            ]["EMA20"]

            >

            env.daily_df.iloc[
                max(
                    0,
                    env.current_step // 75
                )
            ]["EMA50"]
        )

        # ====================================
        # VOLATILITY
        # ====================================

        volatility_ratio = (
            atr / current_price
        )

        # ====================================
        # REGIME ANALYSIS
        # ====================================

        confidence, regime = (

            self.regime_manager
            .analyze(

                analysis,

                rsi,

                bullish_alignment,

                volatility_ratio,

                current_price,

                current_row["EMA20"],

                current_row["EMA50"]
            )
        )

        return {

            "analysis":
            analysis,

            "confidence":
            confidence,

            "regime":
            regime,

            "bullish_alignment":
            bullish_alignment,

            "volatility_ratio":
            volatility_ratio,

            "current_price":
            current_price,

            "atr":
            atr,

            "rsi":
            rsi
        }