from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from paper_trading.common import TradingConfig, ensure_parent


@dataclass
class PortfolioEngineConfig:
    candidates_file: Path = Path("logs/live_candidates.csv")
    portfolio_file: Path = Path("current_portfolio.csv")
    initial_capital: float = 1_000_000.0
    slots: tuple[float, float, float] = (500_000.0, 300_000.0, 200_000.0)
    max_positions: int = 3


class PortfolioEngine:
    def __init__(self, config: PortfolioEngineConfig | None = None) -> None:
        self.config = config or PortfolioEngineConfig()
        self.trading_config = TradingConfig(
            initial_capital=self.config.initial_capital,
            slots=self.config.slots,
            max_positions=self.config.max_positions,
        )

    def _load_existing(self) -> pd.DataFrame:
        if self.config.portfolio_file.exists():
            df = pd.read_csv(self.config.portfolio_file)
            if not df.empty and "entry_timestamp" in df.columns:
                df["entry_timestamp"] = pd.to_datetime(df["entry_timestamp"], errors="coerce")
            return df
        return pd.DataFrame()

    def _free_slots(self, open_positions: pd.DataFrame) -> list[tuple[int, float]]:
        used = set(open_positions["slot_id"].tolist()) if not open_positions.empty else set()
        free = []
        for i, capital in enumerate(self.trading_config.slots, start=1):
            if i not in used:
                free.append((i, float(capital)))
        free.sort(key=lambda x: x[1], reverse=True)
        return free

    def update_from_candidates(self, candidates: pd.DataFrame | None = None) -> pd.DataFrame:
        if candidates is None:
            candidates = pd.read_csv(self.config.candidates_file)
        if not candidates.empty and "timestamp" in candidates.columns:
            candidates["timestamp"] = pd.to_datetime(candidates["timestamp"], errors="coerce")

        portfolio = self._load_existing()
        if portfolio.empty:
            portfolio = pd.DataFrame(
                columns=[
                    "symbol",
                    "entry_timestamp",
                    "entry_price",
                    "quantity",
                    "slot_id",
                    "slot_capital",
                    "pqs",
                    "status",
                ]
            )

        open_positions = portfolio[portfolio["status"] == "OPEN"].copy()
        free_slots = self._free_slots(open_positions)
        if candidates.empty or not free_slots:
            ensure_parent(self.config.portfolio_file)
            portfolio.to_csv(self.config.portfolio_file, index=False)
            return portfolio

        open_symbols = set(open_positions["symbol"].tolist())
        ranked = candidates.sort_values("pqs", ascending=False)

        for _, row in ranked.iterrows():
            if not free_slots:
                break
            symbol = str(row["symbol"])
            if symbol in open_symbols:
                continue

            slot_id, slot_cap = free_slots.pop(0)
            price = float(row.get("last_price", 0.0))
            if price <= 0:
                continue
            qty = int(slot_cap // price)
            if qty <= 0:
                continue
            entry = {
                "symbol": symbol,
                "entry_timestamp": row["timestamp"],
                "entry_price": price,
                "quantity": qty,
                "slot_id": slot_id,
                "slot_capital": slot_cap,
                "pqs": float(row["pqs"]),
                "status": "OPEN",
            }
            portfolio = pd.concat([portfolio, pd.DataFrame([entry])], ignore_index=True)
            open_symbols.add(symbol)

            if len(portfolio[portfolio["status"] == "OPEN"]) >= self.trading_config.max_positions:
                break

        ensure_parent(self.config.portfolio_file)
        portfolio.to_csv(self.config.portfolio_file, index=False)
        return portfolio


def main() -> None:
    engine = PortfolioEngine()
    out = engine.update_from_candidates()
    print(f"Portfolio rows: {len(out)}")
    print("Saved: current_portfolio.csv")


if __name__ == "__main__":
    main()

