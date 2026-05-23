import random
import numpy as np

from execution.trade_validator import TradeValidator

from risk.position_sizer import PositionSizer

from execution.trade_confidence import (
    TradeConfidenceEngine
)

from risk.risk_manager import RiskManager

from utils.market_quality_analyzer import (
    MarketQualityAnalyzer
)

from utils.multi_timeframe_state_builder import (
    build_multi_timeframe_state
)

from risk.adaptive_trailing import (
    AdaptiveTrailingEngine
)

from risk.profit_lock_engine import (
    ProfitLockEngine
)

from market.regime_detector import (
    MarketRegimeDetector
)


class PortfolioEnvironment:

    def __init__(

        self,

        daily_data,

        hourly_data,

        five_data,

        initial_balance=100000,

        max_positions=5,

        brokerage_per_trade=40,

        slippage_percent=0.001,

        position_size_percent=0.20
    ):

        # ====================================
        # DATA
        # ====================================

        self.daily_data = daily_data

        self.hourly_data = hourly_data

        self.five_data = five_data

        self.stock_symbols = list(
            five_data.keys()
        )

        # ====================================
        # CONFIG
        # ====================================

        self.initial_balance = (
            initial_balance
        )

        self.max_positions = (
            max_positions
        )

        self.brokerage_per_trade = (
            brokerage_per_trade
        )

        self.slippage_percent = (
            slippage_percent
        )

        self.position_size_percent = (
            position_size_percent
        )

        self.minimum_holding_steps = 20

        # ====================================
        # ENGINES
        # ====================================

        self.trade_validator = (
            TradeValidator()
        )

        self.position_sizer = (
            PositionSizer()
        )

        self.trade_confidence_engine = (
            TradeConfidenceEngine()
        )

        self.market_quality_analyzer = (
            MarketQualityAnalyzer()
        )

        self.risk_manager = RiskManager(

            stop_loss_percent=0.02,

            take_profit_percent=0.05,

            trailing_stop_percent=0.01,

            max_hold_steps=200
        )

        self.adaptive_trailing_engine = (
            AdaptiveTrailingEngine()
        )

        self.profit_lock_engine = (
            ProfitLockEngine()
        )

        self.market_regime_detector = (
            MarketRegimeDetector()
        )

        # ====================================
        # RESET
        # ====================================

        self.reset()

    # ====================================
    # RESET
    # ====================================

    def reset(self):

        self.balance = (
            self.initial_balance
        )

        self.portfolio_value = (
            self.initial_balance
        )

        self.positions = {}

        self.trade_history = []

        self.total_reward = 0

        self.current_step = 50

        self.done = False

        # ====================================
        # RANDOM STOCK
        # ====================================

        self.current_symbol = random.choice(

            self.stock_symbols
        )

        self.daily_df = self.daily_data[
            self.current_symbol
        ].reset_index(drop=True)

        self.hourly_df = self.hourly_data[
            self.current_symbol
        ].reset_index(drop=True)

        self.five_df = self.five_data[
            self.current_symbol
        ].reset_index(drop=True)

        return self._get_state()

    # ====================================
    # GET STATE
    # ====================================

    def _get_state(self):

        daily_index = min(

            len(self.daily_df) - 1,

            max(50, self.current_step // 75)
        )

        hourly_index = min(

            len(self.hourly_df) - 1,

            max(50, self.current_step // 12)
        )

        five_index = min(

            len(self.five_df) - 1,

            self.current_step
        )

        daily_window = self.daily_df.iloc[
            :daily_index
        ]

        hourly_window = self.hourly_df.iloc[
            :hourly_index
        ]

        five_window = self.five_df.iloc[
            :five_index
        ]

        portfolio_features = np.array([

            self.balance / self.initial_balance,

            len(self.positions)
            / self.max_positions,

            self.portfolio_value
            / self.initial_balance
        ])

        state = build_multi_timeframe_state(

            daily_window,

            hourly_window,

            five_window,

            portfolio_features
        )

        return state.astype(np.float32)

    # ====================================
    # STEP
    # ====================================

    def step(self, action):

        reward = 0

        symbol = self.current_symbol

        current_row = self.five_df.iloc[
            self.current_step
        ]

        current_price = current_row["close"]

        atr = current_row["ATR"]

        rsi = current_row["RSI"]

        # ====================================
        # MARKET ANALYSIS
        # ====================================

        analysis = (

            self.market_quality_analyzer
            .analyze(

                self.daily_df.iloc[
                    :max(50, self.current_step // 75)
                ],

                self.hourly_df.iloc[
                    :max(50, self.current_step // 12)
                ],

                self.five_df.iloc[
                    :self.current_step
                ]
            )
        )

        bullish_alignment = (

            self.daily_df.iloc[
                max(0, self.current_step // 75)
            ]["EMA20"]

            >

            self.daily_df.iloc[
                max(0, self.current_step // 75)
            ]["EMA50"]
        )

        volatility_ratio = (
            atr / current_price
        )

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

                current_row["EMA20"],

                current_row["EMA50"],

                volatility_ratio
            )
        )

        # ====================================
        # REGIME FILTER
        # ====================================

        if regime == "trending":

            confidence += 0.10

        elif regime == "volatile":

            confidence -= 0.10

        elif regime == "choppy":

            confidence -= 0.15

        # ====================================
        # AUTO EXIT
        # ====================================

        if symbol in self.positions:

            position = self.positions[symbol]

            position["highest_price"] = max(

                position["highest_price"],

                current_price
            )

            adaptive_stop = (

                self.adaptive_trailing_engine
                .calculate(

                    position["entry_price"],

                    current_price,

                    atr,

                    confidence,

                    analysis["quality_score"]
                )
            )

            locked_stop = (

                self.profit_lock_engine
                .calculate(

                    position["entry_price"],

                    current_price
                )
            )

            final_stop = max(

                adaptive_stop,

                locked_stop
            )

            risk_exit = None

            if current_price < final_stop:

                risk_exit = (
                    "adaptive_trailing"
                )

            else:

                risk_exit = (

                    self.risk_manager
                    .check_exit(

                        position,

                        current_price,

                        self.current_step
                    )
                )

            if risk_exit is not None:

                pnl = self._close_position(

                    symbol,

                    current_price,

                    risk_exit
                )

                reward += pnl / 3000

                if pnl > 0:

                    reward += pnl / 1000

                else:

                    reward -= abs(
                        pnl / 2000
                    )

                action = 0

        # ====================================
        # BUY
        # ====================================

        if action == 1:

            valid_trade = (

                self.trade_validator
                .validate_buy(

                    self.daily_df.iloc[
                        :max(
                            50,
                            self.current_step // 75
                        )
                    ],

                    self.hourly_df.iloc[
                        :max(
                            50,
                            self.current_step // 12
                        )
                    ],

                    self.five_df.iloc[
                        :self.current_step
                    ]
                )
            )

            if (

                valid_trade

                and

                confidence > 0.40

                and

                symbol not in self.positions

                and

                len(self.positions)
                < self.max_positions
            ):

                dynamic_position_size = (

                    self.position_sizer
                    .calculate(

                        analysis[
                            "quality_score"
                        ],

                        volatility_ratio,

                        bullish_alignment
                    )
                )

                dynamic_position_size *= (
                    0.5 + confidence
                )

                allocation = (

                    self.balance

                    *

                    dynamic_position_size
                )

                if allocation > 1000:

                    shares = (
                        allocation
                        / current_price
                    )

                    buy_cost = (

                        allocation

                        +

                        self.brokerage_per_trade
                    )

                    buy_cost *= (
                        1 + self.slippage_percent
                    )

                    if buy_cost <= self.balance:

                        self.balance -= buy_cost

                        self.positions[symbol] = {

                            "entry_price":
                            current_price,

                            "shares":
                            shares,

                            "remaining_shares":
                            shares,

                            "entry_step":
                            self.current_step,

                            "highest_price":
                            current_price,

                            "partial_exit_done":
                            False
                        }

                        reward -= 0.02

        # ====================================
        # MANUAL SELL
        # ====================================

        elif action == 2:

            if symbol in self.positions:

                position = self.positions[
                    symbol
                ]

                holding_period = (

                    self.current_step

                    -

                    position["entry_step"]
                )

                if (

                    holding_period

                    >=

                    self.minimum_holding_steps
                ):

                    pnl = self._close_position(

                        symbol,

                        current_price,

                        "RL_SELL"
                    )

                    reward += pnl / 3000

                    if pnl > 0:

                        reward += pnl / 1000

                        if holding_period > 50:

                            reward += 2

                        elif holding_period > 20:

                            reward += 1

                    else:

                        reward -= abs(
                            pnl / 2000
                        )

                    reward += confidence

        # ====================================
        # PORTFOLIO VALUE
        # ====================================

        self._update_portfolio_value()

        # ====================================
        # DRAWDOWN CONTROL
        # ====================================

        portfolio_drawdown = (

            self.initial_balance

            -

            self.portfolio_value
        ) / self.initial_balance

        if portfolio_drawdown > 0.05:

            reward -= 1

        if portfolio_drawdown > 0.10:

            reward -= 3

        if portfolio_drawdown > 0.15:

            reward -= 8

        if portfolio_drawdown > 0.20:

            reward -= 15

        # ====================================
        # NEXT STEP
        # ====================================

        self.current_step += 1

        if (

            self.current_step

            >=

            len(self.five_df) - 1
        ):

            self.done = True

        self.total_reward += reward

        next_state = self._get_state()

        return (

            next_state,

            reward,

            self.done,

            {}
        )

    # ====================================
    # CLOSE POSITION
    # ====================================

    def _close_position(

        self,

        symbol,

        current_price,

        exit_reason
    ):

        position = self.positions[
            symbol
        ]

        shares = position[
            "remaining_shares"
        ]

        sell_value = (

            shares

            *

            current_price
        )

        sell_value -= (
            self.brokerage_per_trade
        )

        sell_value *= (
            1 - self.slippage_percent
        )

        pnl = sell_value - (

            shares

            *

            position["entry_price"]
        )

        self.balance += sell_value

        self.trade_history.append({

            "symbol": symbol,

            "entry_price":
            position["entry_price"],

            "exit_price":
            current_price,

            "pnl": pnl,

            "holding_period": (

                self.current_step

                -

                position["entry_step"]
            ),

            "exit_reason":
            exit_reason
        })

        del self.positions[symbol]

        return pnl

    # ====================================
    # PORTFOLIO VALUE
    # ====================================

    def _update_portfolio_value(self):

        positions_value = 0

        for symbol, position in self.positions.items():

            latest_price = self.five_data[
                symbol
            ].iloc[
                min(

                    self.current_step,

                    len(
                        self.five_data[symbol]
                    ) - 1
                )
            ]["close"]

            positions_value += (

                position["remaining_shares"]

                *

                latest_price
            )

        self.portfolio_value = (

            self.balance

            +

            positions_value
        )

    # ====================================
    # METRICS
    # ====================================

    def get_metrics(self):

        total_pnl = (

            self.portfolio_value

            -

            self.initial_balance
        )

        wins = [

            t for t in self.trade_history

            if t["pnl"] > 0
        ]

        win_rate = 0

        if len(self.trade_history) > 0:

            win_rate = (

                len(wins)

                /

                len(self.trade_history)
            ) * 100

        return {

            "portfolio_value":
            self.portfolio_value,

            "balance":
            self.balance,

            "pnl":
            total_pnl,

            "trades":
            len(self.trade_history),

            "win_rate":
            win_rate,

            "open_positions":
            len(self.positions)
        }
