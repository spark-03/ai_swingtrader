import numpy as np


class StateBuilder:

    def __init__(self):
        pass

    def build_state(
        self,
        row,
        current_position=0,
        entry_price=0,
        holding_time=0,
        unrealized_pnl=0
    ):

        # -------- PRICE FEATURES -------- #

        close = row["close"]
        volume = row["volume"]

        # -------- INDICATORS -------- #

        rsi = row["RSI"]

        ema9 = row["EMA_9"]
        ema21 = row["EMA_21"]

        vwap = row["VWAP"]

        atr = row["ATR"]
        adx = row["ADX"]

        # -------- FEATURE ENGINEERING -------- #

        ema_spread = (ema9 - ema21) / close

        distance_from_vwap = (close - vwap) / close

        atr_percent = atr / close

        # Candle structure

        candle_body = (row["close"] - row["open"]) / row["open"]

        upper_wick = (
            row["high"] -
            max(row["open"], row["close"])
        ) / row["open"]

        lower_wick = (
            min(row["open"], row["close"]) -
            row["low"]
        ) / row["open"]

        # -------- NORMALIZED STATE VECTOR -------- #

        state = np.array([

            close / ema21,
            volume / 1000000,

            rsi / 100,

            ema_spread,

            distance_from_vwap,

            atr_percent,

            adx / 100,

            candle_body,
            upper_wick,
            lower_wick,

            current_position,

            unrealized_pnl,

            holding_time

        ], dtype=np.float32)

        return state