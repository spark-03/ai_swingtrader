import enum

class ExitReason(enum.Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    HOLD_ON_TREND = "HOLD_ON_TREND"
    NONE = "NONE"

class ExitManager:
    """Encapsulates asymmetric exit logic.

    - Fast stop‑loss cut (default 2%).
    - Slow take‑profit (default 5%).
    - Adaptive trailing stop (default 1% below highest price).
    - Optional hold‑on‑trend where positions are kept if price stays above a moving average.
    """

    def __init__(self, stop_loss_percent: float = 0.02, take_profit_percent: float = 0.05, trailing_stop_percent: float = 0.01):
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.trailing_stop_percent = trailing_stop_percent

    def evaluate(self, position: dict, current_price: float, atr: float, confidence: float, analysis: dict) -> ExitReason:
        """Determine whether the position should be exited.

        Returns an ``ExitReason`` enum value. ``NONE`` means keep the position.
        """
        entry_price = position["entry_price"]
        # Stop‑loss check (fast cut)
        if current_price <= entry_price * (1 - self.stop_loss_percent):
            return ExitReason.STOP_LOSS
        # Take‑profit check (slow capture)
        if current_price >= entry_price * (1 + self.take_profit_percent):
            return ExitReason.TAKE_PROFIT
        # Adaptive trailing stop (based on highest price seen)
        highest_price = position.get("highest_price", entry_price)
        trailing_target = highest_price * (1 - self.trailing_stop_percent)
        if current_price <= trailing_target:
            return ExitReason.TRAILING_STOP
        # Hold on trend – if analysis reports a strong bullish alignment keep position
        if analysis.get("bullish_alignment", False):
            return ExitReason.HOLD_ON_TREND
        return ExitReason.NONE
