from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

RL_OBSERVATION_FEATURES = [
    "bars_since_entry",
    "pnl_pct",
    "peak_pnl_so_far",
    "drawdown_from_peak",
    "momentum_score",
    "trend_strength",
    "volatility_score",
    "compression_score",
    "momentum_persistence",
    "higher_low_strength",
    "price_position",
    "ATR",
    "ema_spread",
    "delta_momentum_1",
    "delta_trend_1",
    "delta_ema_spread_1",
    "delta_price_position_1",
    "delta_momentum_3",
    "delta_trend_3",
    "delta_ema_spread_3",
]


@dataclass
class RLExitConfig:
    model_path: Path = Path("models/rl_trade_exit_agent_tqs25.zip")


class RLExitEngine:
    def __init__(self, config: RLExitConfig | None = None) -> None:
        self.config = config or RLExitConfig()
        self.model = self._load_model()
        self.expected_dim = len(RL_OBSERVATION_FEATURES)

        if self.model is not None and hasattr(self.model, "observation_space"):
            shape = getattr(self.model.observation_space, "shape", None)
            if shape and len(shape) == 1 and shape[0] is not None:
                self.expected_dim = int(shape[0])

        print(f"Expected RL shape: ({self.expected_dim},)")

    def _load_model(self) -> Any:
        try:
            from stable_baselines3 import DQN

            if self.config.model_path.exists():
                return DQN.load(str(self.config.model_path))

        except Exception:
            return None

        return None

    @staticmethod
    def _safe_float(v: Any) -> float:
        try:
            if pd.isna(v):
                return 0.0
            return float(v)
        except Exception:
            return 0.0

    def _build_state(
        self,
        row: pd.Series,
        bars_since_entry: int,
        pnl_pct: float,
    ) -> np.ndarray:

        momentum = self._safe_float(row.get("momentum_score", 0.0))
        trend = self._safe_float(row.get("trend_strength", 0.0))
        ema_spread = self._safe_float(row.get("ema_spread", 0.0))
        price_position = self._safe_float(row.get("price_position", 0.0))

        vals = [
            float(bars_since_entry),
            float(pnl_pct),
            max(float(pnl_pct), 0.0),
            min(float(pnl_pct), 0.0),
            momentum,
            trend,
            self._safe_float(row.get("volatility_score", 0.0)),
            self._safe_float(row.get("compression_score", 0.0)),
            self._safe_float(row.get("momentum_persistence", 0.0)),
            self._safe_float(row.get("higher_low_strength", 0.0)),
            price_position,
            self._safe_float(row.get("ATR", 0.0)),
            ema_spread,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

        return np.asarray(vals, dtype=np.float32)

    def decide(
        self,
        open_positions: pd.DataFrame,
        latest_candidates: pd.DataFrame,
    ) -> pd.DataFrame:

        if open_positions.empty:
            return pd.DataFrame(
                columns=["timestamp", "symbol", "decision", "reason"]
            )

        candidates_idx = (
            latest_candidates.set_index("symbol")
            if not latest_candidates.empty
            else pd.DataFrame()
        )

        decisions: list[dict] = []

        for _, pos in open_positions.iterrows():

            symbol = str(pos["symbol"])

            joined = {}

            if not candidates_idx.empty and symbol in candidates_idx.index:
                joined = candidates_idx.loc[symbol].to_dict()

            entry_price = float(pos.get("entry_price", 0.0))
            last_price = float(joined.get("last_price", entry_price))

            unreal = (
                ((last_price - entry_price) / entry_price) * 100.0
                if entry_price > 0
                else 0.0
            )

            entry_ts = pd.to_datetime(
                pos.get("entry_timestamp"),
                errors="coerce",
            )

            now_ts = pd.Timestamp.now(
                tz="Asia/Kolkata"
            )

            if pd.notna(entry_ts):

                if entry_ts.tzinfo is None:
                    entry_ts = entry_ts.tz_localize(
                        "Asia/Kolkata"
                    )
                else:
                    entry_ts = entry_ts.tz_convert(
                        "Asia/Kolkata"
                    )

                delta_hours = max(
                    (now_ts - entry_ts).total_seconds() / 3600.0,
                    0.0,
                )

                bars_since_entry = max(
                    1,
                    int(round(delta_hours / 2.0))
                )

            else:
                bars_since_entry = 1

            row = pd.Series(joined)

            if self.model is None:

                decision = (
                    "SELL"
                    if unreal < -3.0
                    else "HOLD"
                )

                reason = "heuristic_fallback"

            else:

                state = self._build_state(
                    row,
                    bars_since_entry=bars_since_entry,
                    pnl_pct=unreal,
                )

                print(f"Actual RL shape: {state.shape}")

                assert len(state) == self.expected_dim, (
                    f"Unexpected RL state length {len(state)}; "
                    f"expected {self.expected_dim}."
                )

                action, _ = self.model.predict(
                    state,
                    deterministic=True,
                )

                decision = (
                    "SELL"
                    if int(action) == 1
                    else "HOLD"
                )

                reason = "rl_model"

            decisions.append(
                {
                    "timestamp": pd.Timestamp.utcnow(),
                    "symbol": symbol,
                    "decision": decision,
                    "reason": reason,
                }
            )

        return pd.DataFrame(decisions)

    def candidate_entries(
        self,
        open_positions: pd.DataFrame,
        latest_candidates: pd.DataFrame,
        free_slots: int,
    ) -> pd.DataFrame:

        if free_slots <= 0 or latest_candidates.empty:
            return pd.DataFrame(
                columns=["timestamp", "symbol", "decision", "reason"]
            )

        open_symbols = (
            set(open_positions["symbol"].tolist())
            if not open_positions.empty
            else set()
        )

        buys = []

        for _, row in (
            latest_candidates
            .sort_values("pqs", ascending=False)
            .iterrows()
        ):

            if len(buys) >= free_slots:
                break

            symbol = str(row["symbol"])

            if symbol in open_symbols:
                continue

            buys.append(
                {
                    "timestamp": pd.Timestamp.utcnow(),
                    "symbol": symbol,
                    "decision": "BUY",
                    "reason": "ranked_candidate",
                }
            )

        return pd.DataFrame(buys)