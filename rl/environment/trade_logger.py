import logging
import csv
import os
from datetime import datetime

class TradeLogger:
    """Central logger for trade actions and system events.

    Writes human‑readable logs to a file and optionally appends structured trade
    records to a CSV for later analysis.
    """

    def __init__(self, log_dir: str = "logs", log_file: str = "trading.log", csv_file: str = "trade_history.csv"):
        # Ensure log directory exists
        self.log_path = os.path.join(log_dir, log_file)
        self.csv_path = os.path.join(log_dir, csv_file)
        os.makedirs(log_dir, exist_ok=True)

        # Configure standard logger
        self.logger = logging.getLogger("TradeLogger")
        self.logger.setLevel(logging.INFO)
        # Avoid duplicate handlers if re‑instantiated
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_path)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Initialise CSV with header if not present
        if not os.path.isfile(self.csv_path):
            with open(self.csv_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "symbol",
                    "side",
                    "quantity",
                    "price",
                    "pnl",
                    "reward",
                    "confidence",
                    "regime",
                    "holding_steps",
                    "exit_reason",
                    "market_quality",
                    "volatility_ratio",
                ])

    def log_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        entry_price: float = 0.0,
        exit_price: float = 0.0,
        pnl: float = 0.0,
        reward: float = 0.0,
        confidence: float = 0.0,
        regime: str = "",
        holding_steps: int = 0,
        exit_reason: str = "",
        market_quality: float = 0.0,
        volatility_ratio: float = 0.0,
    ) -> None:
        """Log a trade event both to the text log and CSV.

        Parameters are deliberately explicit so callers can pass the exact
        information required for later performance analytics.
        """
        msg = (
            f"TRADE {side.upper()}: {quantity:.2f} of {symbol} at {price:.2f} | "
            f"PnL={pnl:.4f} Reward={reward:.4f} Confidence={confidence:.2f} "
            f"Regime={regime} Holding={holding_steps} Reason={exit_reason} "
            f"Quality={market_quality:.2f} VolRatio={volatility_ratio:.4f}"
        )
        self.logger.info(msg)
        # Append structured row to CSV
        timestamp = datetime.utcnow().isoformat()
        with open(self.csv_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                symbol,
                side,
                quantity,
                price,
                entry_price,
                exit_price,
                pnl,
                reward,
                confidence,
                regime,
                holding_steps,
                exit_reason,
                market_quality,
                volatility_ratio,
            ])

    def log_error(self, error_message: str) -> None:
        """Record an error message with severity ERROR."""
        self.logger.error(error_message)
