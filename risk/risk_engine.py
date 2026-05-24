class RiskEngine:
    """Encapsulates risk‑management checks for a single position.

    It evaluates stop‑loss, take‑profit and trailing‑stop conditions based on the
    current profit‑and‑loss percentage (``pnl_pct``), the trailing draw‑down
    (``trailing_drawdown``) and the number of candles the position has been held
    (``hold_candles``). The thresholds are supplied at construction time and match
    the constants used in the back‑test script.
    """

    def __init__(self, stop_loss: float = 0.015, take_profit: float = 0.03, trailing_stop: float = 0.01):
        self.stop_loss = -abs(stop_loss)          # negative value for loss
        self.take_profit = abs(take_profit)
        self.trailing_stop = abs(trailing_stop)

    def evaluate(self, pnl_pct: float, trailing_drawdown: float, hold_candles: int) -> tuple[bool, bool, bool]:
        """Return three booleans: ``stop_loss_hit``, ``take_profit_hit``, ``trailing_stop_hit``.

        Parameters
        ----------
        pnl_pct: float
            Profit‑and‑loss as a fraction of entry price (e.g. 0.02 for +2%).
        trailing_drawdown: float
            Relative draw‑down from the highest price while the position is open.
        hold_candles: int
            Number of candles the position has been open – currently unused but kept
            for possible future extensions.
        """
        stop_loss_hit = pnl_pct <= self.stop_loss
        take_profit_hit = pnl_pct >= self.take_profit
        trailing_stop_hit = pnl_pct > 0 and trailing_drawdown >= self.trailing_stop
        return stop_loss_hit, take_profit_hit, trailing_stop_hit
