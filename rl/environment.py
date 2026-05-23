from rl.state_builder import StateBuilder
from rl.reward_engine import RewardEngine
from rl.trade_logger import TradeLogger
from rl.portfolio_tracker import PortfolioTracker

class TradingEnvironment:

    def __init__(self, df):

        # =========================
        # DATA
        # =========================

        self.df = df.reset_index(drop=True)

        # =========================
        # STATE BUILDER
        # =========================

        self.state_builder = StateBuilder()

        # =========================
        # REWARD ENGINE
        # =========================

        self.reward_engine = RewardEngine()

        # =========================
        # TRADE LOGGER
        # =========================

        self.trade_logger = TradeLogger()

        # =========================
        # PORTFOLIO TRACKER
        # =========================

        self.portfolio_tracker = PortfolioTracker()

        # =========================
        # ENVIRONMENT VARIABLES
        # =========================

        self.current_step = 0

        # 0 = no position
        # 1 = long
        # -1 = short
        self.current_position = 0

        self.entry_price = 0

        self.holding_time = 0

        self.done = False

    # ====================================
    # RESET ENVIRONMENT
    # ====================================

    def reset(self):

        self.current_step = 0

        self.current_position = 0

        self.entry_price = 0

        self.holding_time = 0

        self.done = False

        return self._get_state()

    # ====================================
    # GET CURRENT STATE
    # ====================================

    def _get_state(self):

        row = self.df.iloc[self.current_step]

        current_price = row["close"]

        unrealized_pnl = 0

        # ====================================
        # LONG POSITION
        # ====================================

        if self.current_position == 1:

            unrealized_pnl = (
                current_price - self.entry_price
            ) / self.entry_price

        # ====================================
        # SHORT POSITION
        # ====================================

        elif self.current_position == -1:

            unrealized_pnl = (
                self.entry_price - current_price
            ) / self.entry_price

        # ====================================
        # BUILD STATE
        # ====================================

        state = self.state_builder.build_state(
            row=row,
            current_position=self.current_position,
            entry_price=self.entry_price,
            holding_time=self.holding_time,
            unrealized_pnl=unrealized_pnl
        )

        return state

    # ====================================
    # STEP FUNCTION
    # ====================================

    def step(self, action):

        row = self.df.iloc[self.current_step]

        current_price = row["close"]

        reward = 0

        # ====================================
        # ACTION = BUY
        # ====================================

        if action == 1:

            # CLOSE SHORT POSITION

            if self.current_position == -1:

                pnl = (
                    self.entry_price - current_price
                ) / self.entry_price

                # LOG TRADE

                self.trade_logger.log_trade(
                    direction="SHORT",
                    entry_price=self.entry_price,
                    exit_price=current_price,
                    pnl=pnl,
                    holding_time=self.holding_time
                )

                reward = pnl
                self.portfolio_tracker.update(pnl)

                self.current_position = 0

                self.entry_price = 0

                self.holding_time = 0

            # OPEN LONG POSITION

            elif self.current_position == 0:

                self.current_position = 1

                self.entry_price = current_price

                self.holding_time = 0

        # ====================================
        # ACTION = SELL
        # ====================================

        elif action == 2:

            # CLOSE LONG POSITION

            if self.current_position == 1:

                pnl = (
                    current_price - self.entry_price
                ) / self.entry_price

                # LOG TRADE

                self.trade_logger.log_trade(
                    direction="LONG",
                    entry_price=self.entry_price,
                    exit_price=current_price,
                    pnl=pnl,
                    holding_time=self.holding_time
                )

                reward = pnl
                self.portfolio_tracker.update(pnl)
                self.current_position = 0

                self.entry_price = 0

                self.holding_time = 0

            # OPEN SHORT POSITION

            elif self.current_position == 0:

                self.current_position = -1

                self.entry_price = current_price

                self.holding_time = 0

        # ====================================
        # REWARD ENGINE
        # ====================================

        reward += self.reward_engine.calculate_reward(
            current_position=self.current_position,
            entry_price=self.entry_price,
            current_price=current_price,
            action=action
        )

        # ====================================
        # MOVE TO NEXT CANDLE
        # ====================================

        self.current_step += 1

        self.holding_time += 1

        # ====================================
        # CHECK END
        # ====================================

        if self.current_step >= len(self.df) - 1:

            self.done = True

        # ====================================
        # NEXT STATE
        # ====================================

        next_state = self._get_state()

        return next_state, reward, self.done

    # ====================================
    # GET TRADE HISTORY
    # ====================================

    def get_trade_history(self):

        return self.trade_logger.get_trades()
    # ====================================
# GET PORTFOLIO METRICS
# ====================================

    def get_portfolio_metrics(self):

        return self.portfolio_tracker.get_metrics()
