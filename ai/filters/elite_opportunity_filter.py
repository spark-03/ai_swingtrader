class EliteOpportunityFilter:

    def __init__(

        self,

        compression_threshold=0.5,

        breakout_threshold=0.5,

        momentum_threshold=0.0,

        volume_threshold=1.0
    ):

        self.compression_threshold = (
            compression_threshold
        )

        self.breakout_threshold = (
            breakout_threshold
        )

        self.momentum_threshold = (
            momentum_threshold
        )

        self.volume_threshold = (
            volume_threshold
        )

    # ====================================
    # CHECK ELITE SETUP
    # ====================================

    def is_valid_setup(

        self,

        row,

        relative_volume
    ):

        # ====================================
        # VOLATILITY COMPRESSION
        # ====================================

        compression_valid = (

            row["compression_score"]

            >=

            self.compression_threshold
        )

        # ====================================
        # BREAKOUT PRESSURE
        # ====================================

        breakout_valid = (

            row["breakout_pressure"]

            >=

            self.breakout_threshold
        )

        # ====================================
        # MOMENTUM QUALITY
        # ====================================

        momentum_valid = (

            row["momentum_score"]

            >=

            self.momentum_threshold
        )

        # ====================================
        # TREND FILTER
        # ====================================

        trend_valid = (

            row["EMA20"]

            >

            row["EMA50"]
        )

        # ====================================
        # VOLUME FILTER
        # ====================================

        volume_valid = (

            relative_volume

            >=

            self.volume_threshold
        )

        # ====================================
        # FINAL DECISION
        # ====================================

        return (

            compression_valid

            and

            breakout_valid

            and

            momentum_valid

            and

            trend_valid

            and

            volume_valid
        )