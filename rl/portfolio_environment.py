import random
from typing import Any, Dict, Tuple

# ----------------------------------------------------------------------
# Engine / component imports
# ----------------------------------------------------------------------
from execution.trade_validator import TradeValidator
from ai.filters.elite_opportunity_filter import EliteOpportunityFilter
from ai.elite_scoring import EliteScoring
from data.stock_universe import get_allowed_symbols
from risk.position_sizer import PositionSizer
from risk.risk_manager import RiskManager
from utils.market_quality_analyzer import MarketQualityAnalyzer
from risk.adaptive_trailing import AdaptiveTrailingEngine
from risk.profit_lock_engine import ProfitLockEngine
from market.regime_detector import MarketRegimeDetector
from execution.trade_confidence import TradeConfidenceEngine
from rl.environment.reward_engine import RewardEngine
from rl.environment.portfolio_manager import PortfolioManager
from rl.environment.state_manager import StateManager
from rl.environment.metrics_manager import MetricsManager
from rl.environment.regime_manager import RegimeManager
from rl.environment.execution_manager import ExecutionManager
from rl.environment.analysis_manager import AnalysisManager


class PortfolioEnvironment:
    """
    Reinforcement‑learning environment that simulates a multi‑asset portfolio.
    It wires together a collection of interchangeable "engine" components
    (risk, execution, market analysis, etc.) and provides the classic
    OpenAI‑Gym style API: ``reset()``, ``step(action)`` and ``get_metrics()``.
    """

    # ------------------------------------------------------------------
    # Construction / configuration
    # ------------------------------------------------------------------
    def __init__(
        self,
        daily_data: Dict[str, Any],
        hourly_data: Dict[str, Any],
        five_data: Dict[str, Any],
        initial_balance: float = 100_000,
        max_positions: int = 5,
        brokerage_per_trade: float = 40,
        slippage_percent: float = 0.001,
        position_size_percent: float = 0.20,
    ) -> None:
        """Initialise the environment.

        Parameters
        ----------
        daily_data, hourly_data, five_data
            Mapping ``symbol -> pandas.DataFrame`` for the three time‑frames.
        initial_balance
            Starting cash balance.
        max_positions
            Maximum concurrent open positions.
        brokerage_per_trade
            Fixed cost charged on every executed trade.
        slippage_percent
            Fractional slippage applied to each trade price.
        position_size_percent
            Fraction of equity to allocate to a single position.
        """
        # --------------------------------------------------------------
        # DATA
        # --------------------------------------------------------------
        self.daily_data = daily_data
        self.hourly_data = hourly_data
        self.five_data = five_data
        # Keep only symbols that actually have data for the 5‑minute frame
        self.stock_symbols = []  # will be populated with validated symbols
        self.elite_filter = EliteOpportunityFilter()
        self.elite_scoring = EliteScoring()

        # Validate symbols – all three timeframes must contain at least one row
        whitelist = set(get_allowed_symbols())
        # Include any symbol that has complete data across all timeframes
        for sym, df5 in five_data.items():
            # Ensure dataframes are non-empty
            if df5.empty:
                continue
            df_daily = daily_data.get(sym)
            df_hourly = hourly_data.get(sym)
            if df_daily is None or df_daily.empty:
                continue
            if df_hourly is None or df_hourly.empty:
                continue
            self.stock_symbols.append(sym)
        if not self.stock_symbols:
            raise ValueError("No symbols have complete data and are in the whitelist.")

        # --------------------------------------------------------------
        # CONFIG
        # --------------------------------------------------------------
        self.initial_balance = initial_balance
        self.max_positions = max_positions
        self.brokerage_per_trade = brokerage_per_trade
        self.slippage_percent = slippage_percent
        self.position_size_percent = position_size_percent
        self.minimum_holding_steps = 20

        # --------------------------------------------------------------
        # CORE ENGINES
        # --------------------------------------------------------------
        self.trade_validator = TradeValidator()
        self.position_sizer = PositionSizer()
        self.trade_confidence_engine = TradeConfidenceEngine()
        self.market_quality_analyzer = MarketQualityAnalyzer()
        self.risk_manager = RiskManager(
            stop_loss_percent=0.02,
            take_profit_percent=0.05,
            trailing_stop_percent=0.01,
            max_hold_steps=200,
        )
        self.adaptive_trailing_engine = AdaptiveTrailingEngine()
        self.profit_lock_engine = ProfitLockEngine()
        self.market_regime_detector = MarketRegimeDetector()

        # --------------------------------------------------------------
        # RL ENGINES
        # --------------------------------------------------------------
        self.reward_engine = RewardEngine()
        self.portfolio_manager = PortfolioManager(
            initial_balance,
            brokerage_per_trade,
            slippage_percent,
        )
        self.state_manager = StateManager()
        self.metrics_manager = MetricsManager()
        self.regime_manager = RegimeManager(
            self.market_regime_detector,
            self.trade_confidence_engine,
        )
        self.execution_manager = ExecutionManager(
            self.trade_validator,
            self.position_sizer,
            self.adaptive_trailing_engine,
            self.profit_lock_engine,
            self.risk_manager,
            self.reward_engine,
            self.portfolio_manager,
        )
        self.analysis_manager = AnalysisManager(
            self.market_quality_analyzer,
            self.regime_manager,
        )

        # Initialise the environment state
        self.reset()

    # ------------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------------
    def reset(self) -> Tuple[Any, ...]:
        """Reset the episode to a fresh start and return the initial state."""
        self.balance = self.initial_balance
        self.portfolio_value = self.initial_balance
        self.positions: Dict[str, Any] = {}
        self.trade_history = []
        self.total_reward = 0.0
        # Start from the first index – the state builder expects at least one row
        self.current_step = 0
        self.done = False

        # --------------------------------------------------------------
        # RANDOM SYMBOL (guaranteed to have data)
        # --------------------------------------------------------------
        # Choose a symbol that satisfies elite scoring; retry a few times
        max_tries = 10
        for _ in range(max_tries):
            candidate = random.choice(self.stock_symbols)
            df5 = self.five_data[candidate]
            # Compute recent relative volume (simple proxy)
            recent_vol = df5["volume"].iloc[-20:].mean() if len(df5) >= 20 else df5["volume"].mean()
            rel_vol = df5["volume"].iloc[-1] / (recent_vol + 1e-9)
            # Use the most recent row for scoring
            row = df5.iloc[-1]
            if self.elite_scoring.is_elite(row, rel_vol):
                self.current_symbol = candidate
                break
        else:
            # Fallback to random if no elite found
            self.current_symbol = random.choice(self.stock_symbols)

        # Grab the pre‑validated DataFrames (they are guaranteed non‑empty)
        self.daily_df = self.daily_data[self.current_symbol].reset_index(drop=True)
        self.hourly_df = self.hourly_data[self.current_symbol].reset_index(drop=True)
        self.five_df = self.five_data[self.current_symbol].reset_index(drop=True)

        # Defensive sanity check (should never trigger because of validation above)
        if self.five_df.empty or self.daily_df.empty or self.hourly_df.empty:
            raise ValueError(
                f"One of the data frames for symbol {self.current_symbol} is empty after validation."
            )

        return self._get_state()

    # ------------------------------------------------------------------
    # STATE BUILDING
    # ------------------------------------------------------------------
    def _get_state(self) -> Tuple[Any, ...]:
        """Delegate to the StateManager to construct the observation."""
        return self.state_manager.build_state(
            self.daily_df,
            self.hourly_df,
            self.five_df,
            self.current_step,
            self.balance,
            self.initial_balance,
            self.positions,
            self.max_positions,
            self.portfolio_value,
        )

    # ------------------------------------------------------------------
    # STEP
    # ------------------------------------------------------------------
    def step(self, action: int) -> Tuple[Tuple[Any, ...], float, bool, Dict]:
        """Execute one environment step.

        Parameters
        ----------
        action : int
            0 = Hold, 1 = Buy, 2 = Sell

        Returns
        -------
        next_state, reward, done, info
        """
        reward = 0.0
        symbol = self.current_symbol
        current_row = self.five_df.iloc[self.current_step]

        # --------------------------------------------------------------
        # MARKET ANALYSIS
        # --------------------------------------------------------------
        analysis_data = self.analysis_manager.analyze(self, current_row)

        analysis = analysis_data["analysis"]
        confidence = analysis_data["confidence"]
        regime = analysis_data["regime"]
        bullish_alignment = analysis_data["bullish_alignment"]
        volatility_ratio = analysis_data["volatility_ratio"]
        current_price = analysis_data["current_price"]
        atr = analysis_data["atr"]

        # --------------------------------------------------------------
        # AUTO‑EXIT (e.g., stop‑loss, take‑profit)
        # --------------------------------------------------------------
        reward += self.execution_manager.handle_auto_exit(
            self,
            symbol,
            current_price,
            atr,
            confidence,
            analysis,
        )

        # --------------------------------------------------------------
        # ELITE OPPORTUNITY FILTER
        # --------------------------------------------------------------
        recent_volume_mean = (
            self.five_df["volume"]
            .iloc[max(0, self.current_step - 20) : self.current_step]
            .mean()
        )
        relative_volume = current_row["volume"] / (recent_volume_mean + 1e-9)

        elite_setup = self.elite_filter.is_valid_setup(
            current_row,
            relative_volume,
        )
        # if not elite_setup:
        #     action = 0  # force HOLD if the setup is not elite
        # (Removed forced HOLD to allow trading actions)

        # --------------------------------------------------------------
        # BUY
        # --------------------------------------------------------------
        if action == 1:
                        reward += self.execution_manager.execute_buy(
                self,
                symbol,
                current_price,
                confidence,
                analysis,
                volatility_ratio,
                bullish_alignment,
                regime,
            )

        # --------------------------------------------------------------
        # SELL
        # --------------------------------------------------------------
        elif action == 2:
            reward += self.execution_manager.execute_sell(
                self,
                symbol,
                current_price,
                analysis,
            )

        # --------------------------------------------------------------
        # UPDATE PORTFOLIO
        # --------------------------------------------------------------
        self._update_portfolio_value()

        # --------------------------------------------------------------
        # DRAWDOWN PENALTIES
        # --------------------------------------------------------------
        portfolio_drawdown = (
            self.initial_balance - self.portfolio_value
        ) / self.initial_balance
        if portfolio_drawdown > 0.05:
            reward -= 1
        if portfolio_drawdown > 0.10:
            reward -= 3
        if portfolio_drawdown > 0.15:
            reward -= 8
        if portfolio_drawdown > 0.20:
            reward -= 15

        # --------------------------------------------------------------
        # NEXT STEP / TERMINATION
        # --------------------------------------------------------------
        self.current_step += 1
        if self.current_step >= len(self.five_df) - 1:
            self.done = True

        self.total_reward += reward
        next_state = self._get_state()

        return next_state, reward, self.done, {}

    # ------------------------------------------------------------------
    # PORTFOLIO VALUE CALCULATION
    # ------------------------------------------------------------------
    def _update_portfolio_value(self) -> None:
        """Re‑calculate the total equity based on current holdings."""
        self.portfolio_value = self.portfolio_manager.calculate_portfolio_value(
            self.balance,
            self.positions,
            self.five_data,
            self.current_step,
        )

    # ------------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------------
    def get_metrics(self) -> Tuple[Any, ...]:
        """Return a tuple of performance metrics for the episode."""
        return self.metrics_manager.calculate_metrics(
            self.portfolio_value,
            self.initial_balance,
            self.balance,
            self.trade_history,
            self.positions,
        )