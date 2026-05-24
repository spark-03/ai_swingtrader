from execution.exit_manager import ExitManager, ExitReason
from .trade_logger import TradeLogger

class ExecutionManager:
    def __init__(
        self,
        trade_validator,
        position_sizer,
        adaptive_trailing_engine,
        profit_lock_engine,
        risk_manager,
        reward_engine,
        portfolio_manager
    ):
        self.trade_validator = trade_validator
        self.position_sizer = position_sizer
        self.adaptive_trailing_engine = adaptive_trailing_engine
        self.profit_lock_engine = profit_lock_engine
        # Regime manager placeholder removed; using RegimeClassifier directly
        from ai.regime_classifier import RegimeClassifier
        self.regime_classifier = RegimeClassifier()
        self.risk_manager = risk_manager
        self.reward_engine = reward_engine
        self.portfolio_manager = portfolio_manager
        self.trade_logger = TradeLogger()

    # ====================================
    # BUY EXECUTION
    # ====================================

    def execute_buy(

        self,

        env,

        symbol,

        current_price,

        confidence,

        analysis,

        volatility_ratio,

        bullish_alignment,
        regime
    ):

        # Enforce regime filter: skip actions in undesirable regimes
        if not self.regime_classifier.is_acceptable(regime):
            return 0  # force HOLD

        reward = 0

        valid_trade = (

            self.trade_validator
            .validate_buy(

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

        if (

            valid_trade

            and

            confidence > 0.40

            and

            symbol not in env.positions

            and

            len(env.positions)
            < env.max_positions
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

                env.balance

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

                    env.brokerage_per_trade
                )

                buy_cost *= (
                    1 + env.slippage_percent
                )

                if buy_cost <= env.balance:

                    env.balance -= buy_cost

                    env.positions[symbol] = {

                        "entry_price":
                        current_price,

                        "shares":
                        shares,

                        "remaining_shares":
                        shares,

                        "entry_step":
                        env.current_step,

                        "highest_price":
                        current_price,

                        "partial_exit_done":
                        False
                    }

                    reward -= 0.02

        return reward

    # ====================================
    # SELL EXECUTION
    # ====================================

    def execute_sell(

        self,

        env,

        symbol,

        current_price,

        analysis
    ):

        reward = 0

        if symbol not in env.positions:

            return reward

        position = env.positions[symbol]

        holding_period = (

            env.current_step

            -

            position["entry_step"]
        )

        if (

            holding_period

            <

            env.minimum_holding_steps
        ):

            return reward

        pnl, env.balance = (

            self.portfolio_manager
            .close_position(

                env.positions,

                env.trade_history,

                env.balance,

                symbol,

                current_price,

                env.current_step,

                "RL_SELL"
            )
        )

        realized_pnl_percent = (

            current_price

            -

            position["entry_price"]

        ) / position["entry_price"]

        reward += self.reward_engine.calculate(

            realized_pnl_percent=

            realized_pnl_percent,

            holding_steps=

            holding_period,

            trade_closed=True,

            profitable_trade=

            pnl > 0,

            stop_loss_hit=False,

            trailing_exit=False,

            market_quality=

            analysis["quality_score"]
        )
        self.trade_logger.log_trade(

    exit_price=
    current_price,

    pnl=pnl,

    reward=reward,

    confidence=0,

    regime="manual_sell",

    holding_steps=
    holding_period,

    exit_reason="RL_SELL",

    market_quality=
    analysis["quality_score"],

    volatility_ratio=0
)

        return reward

    # ====================================
    # AUTO EXIT
    # ====================================

    def handle_auto_exit(

        self,

        env,

        symbol,

        current_price,

        atr,

        confidence,

        analysis
    ):

        reward = 0

        if symbol not in env.positions:

            return reward

        position = env.positions[symbol]

        # Use the ExitManager for asymmetric exit evaluation
        exit_manager = ExitManager()
        exit_reason = exit_manager.evaluate(position, current_price, atr, confidence, analysis)

        if exit_reason == ExitReason.NONE:
            return reward

        # Close position based on the evaluated reason
        pnl, env.balance = (

            self.portfolio_manager

            .close_position(

                env.positions,

                env.trade_history,

                env.balance,

                symbol,

                current_price,

                env.current_step,

                exit_reason.name  # convert enum to string name
            )
        )

        realized_pnl_percent = (

            current_price - position["entry_price"]

        ) / position["entry_price"]

        # Map ExitReason to flags for reward calculation
        stop_loss_hit = exit_reason == ExitReason.STOP_LOSS
        trailing_stop_hit = exit_reason == ExitReason.TRAILING_STOP

        reward += self.reward_engine.calculate(

            realized_pnl_percent=realized_pnl_percent,

            holding_steps=env.current_step - position["entry_step"],

            trade_closed=True,

            profitable_trade=pnl > 0,

            stop_loss_hit=stop_loss_hit,

            trailing_exit=trailing_stop_hit,

            market_quality=analysis["quality_score"]
        )

        self.trade_logger.log_trade(

            symbol=symbol,

            entry_price=position["entry_price"],

            exit_price=current_price,

            pnl=pnl,

            reward=reward,

            confidence=confidence,

            regime="auto_exit",

            holding_steps=env.current_step - position["entry_step"],

            exit_reason=exit_reason.name,

            market_quality=analysis["quality_score"],

            volatility_ratio=atr / current_price

        )

        return reward