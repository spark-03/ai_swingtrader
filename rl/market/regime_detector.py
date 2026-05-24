class MarketRegimeDetector:
    """Detects market regime based on technical indicators.

    The detector uses simple heuristic rules:
    * ``trending`` – fast EMA above slow EMA and low ATR.
    * ``volatile`` – high ATR.
    * ``choppy`` – EMAs very close relative to price.
    * ``neutral`` – fallback when none of the above apply.
    """
    def __init__(self):
        pass

    def detect(self, price: float, ema_fast: float, ema_slow: float, atr_percent: float) -> str:
        """Return a regime string.

        Parameters
        ----------
        price: float
            Current price.
        ema_fast: float
            Fast EMA value.
        ema_slow: float
            Slow EMA value.
        atr_percent: float
            ATR expressed as a fraction of price (e.g., 0.02 for 2%).
        """
        # Trending market: fast EMA > slow EMA and low volatility
        if ema_fast > ema_slow and atr_percent < 0.03:
            return "trending"
        # Volatile market: high ATR
        if atr_percent > 0.05:
            return "volatile"
        # Choppy market: EMAs very close relative to price
        if abs(ema_fast - ema_slow) / price < 0.002:
            return "choppy"
        # Default fallback
        return "neutral"