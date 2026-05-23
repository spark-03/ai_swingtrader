import random

import numpy as np
import pandas as pd

from utils.state_builder import build_state


class MultiStockEnvironment:

    def __init__(

        self,

        stock_files,

        initial_balance=100000,

        trade_size=50000
    ):

        # ====================================
        # STOCK DATA
        # ====================================

        self.stock_files = stock_files

        self.data = {}

        for symbol, path in stock_files.items():

            df = pd.read_parquet(path)

            df = df.reset_index(drop=True)

            self.data[symbol] = df

        # ====================================
        # SETTINGS
        # ====================================

        self.initial_balance = initial_balance

        self.trade_size = trade_size

        # ====================================
        # RESET
        # ====================================

        self.reset()

    # ====================================
    # RESET ENVIRONMENT
    # ====================================

    def reset(self):

        self.current_symbol = random.choice(

            list(self.data.keys())
        )

        self.df = self.data[self.current_symbol]

        self.current_step = 120

        self.balance = self.initial_balance

        self.position = None

        self.entry_price = 0

        self.hold_steps = 0

        self.done = False

        self.total_trades = 0

        return self._get_state()

    # ====================================
    # GET STATE
    # ====================================

    def _get_state(self):

        current_df = self.df.iloc[
            :self.current_step + 1
        ]

        state = build_state(current_df)

        # ====================================
        # POSITION FEATURES
        # ====================================

        position_flag = 1.0 if self.position else 0.0

        unrealized_pnl = 0.0

        if self.position == "LONG":

            current_price = self.df.iloc[
                self.current_step
            ]["close"]

            unrealized_pnl = (

                current_price -

                self.entry_price

            ) / self.entry_price

        # ====================================
        # ADD FEATURES
        # ====================================

        state[-3] = position_flag

        state[-2] = unrealized_pnl

        state[-1] = self.hold_steps / 50.0

        return state

    # ====================================
    # STEP FUNCTION
    # ====================================

    def step(self, action):

        reward = 0

        current_price = self.df.iloc[
            self.current_step
        ]["close"]

        next_price = self.df.iloc[
            self.current_step + 1
        ]["close"]

        # ====================================
        # FUTURE TREND
        # ====================================

        future_return = (

            next_price -

            current_price

        ) / current_price

        # ====================================
        # HOLD
        # ====================================

        if action == 0:

            if self.position == "LONG":

                unrealized_pnl = (

                    current_price -

                    self.entry_price

                ) / self.entry_price

                # SMALL HOLD REWARD

                reward = unrealized_pnl * 0.003

                # PENALIZE HOLDING LOSERS

                if unrealized_pnl < -0.01:

                    reward -= 0.01

                # PENALIZE HOLDING TOO LONG

                if self.hold_steps > 30:

                    reward -= 0.002

            else:

                # PENALIZE MISSING STRONG MOVES

                if abs(future_return) > 0.005:

                    reward -= 0.003

                else:

                    reward = 0

        # ====================================
        # BUY
        # ====================================

        elif action == 1:

            if self.position is None:

                self.position = "LONG"

                self.entry_price = current_price

                self.hold_steps = 0

                self.total_trades += 1

                # REWARD GOOD ENTRIES

                reward = future_return * 15

                # BONUS FOR STRONG MOMENTUM

                if future_return > 0.004:

                    reward += 0.01

            else:

                # PENALIZE OVERTRADING

                reward = -0.003

        # ====================================
        # SELL
        # ====================================

        elif action == 2:

            if self.position == "LONG":

                pnl_pct = (

                    current_price -

                    self.entry_price

                ) / self.entry_price

                pnl = self.trade_size * pnl_pct

                self.balance += pnl

                # ====================================
                # MAIN EXIT REWARD
                # ====================================

                reward = pnl_pct * 25

                # ====================================
                # BIG WINNER BONUS
                # ====================================

                if pnl_pct > 0.02:

                    reward += 0.05

                # ====================================
                # STRONG LOSS PENALTY
                # ====================================

                if pnl_pct < -0.015:

                    reward -= 0.05

                # ====================================
                # RESET POSITION
                # ====================================

                self.position = None

                self.entry_price = 0

                self.hold_steps = 0

            else:

                # PENALIZE RANDOM SELLING

                reward = -0.003

        # ====================================
        # HOLD MANAGEMENT
        # ====================================

        if self.position == "LONG":

            self.hold_steps += 1

            unrealized_pnl = (

                current_price -

                self.entry_price

            ) / self.entry_price

            # ====================================
            # FORCE EXIT
            # ====================================

            if self.hold_steps >= 40:

                pnl_pct = unrealized_pnl

                pnl = self.trade_size * pnl_pct

                self.balance += pnl

                reward += pnl_pct * 10

                self.position = None

                self.entry_price = 0

                self.hold_steps = 0

        # ====================================
        # STEP FORWARD
        # ====================================

        self.current_step += 1

        # ====================================
        # DONE
        # ====================================

        if self.current_step >= len(self.df) - 2:

            self.done = True

            # FORCE CLOSE FINAL POSITION

            if self.position == "LONG":

                final_price = self.df.iloc[
                    self.current_step
                ]["close"]

                pnl_pct = (

                    final_price -

                    self.entry_price

                ) / self.entry_price

                pnl = self.trade_size * pnl_pct

                self.balance += pnl

                self.position = None

        next_state = self._get_state()

        return next_state, reward, self.done

    # ====================================
    # METRICS
    # ====================================

    def get_metrics(self):

        total_pnl = (

            self.balance -

            self.initial_balance
        )

        return {

            "symbol": self.current_symbol,

            "balance": self.balance,

            "total_pnl": total_pnl,

            "trades": self.total_trades
        }