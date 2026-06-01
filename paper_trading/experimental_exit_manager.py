from analysis.thesis_lifecycle_logger import (
    log_thesis_lifecycle
)


def manage_exit(
    signal,
    entry_price,
    future_candles,
    atr
):

    # ==================================================
    # SAFE ATR
    # ==================================================

    def _safe_atr(x):

        try:

            val = float(x)

            return val if val > 0 else (
                0.01 * float(entry_price)
            )

        except Exception:

            return (
                0.01 * float(entry_price)
            )

    # ==================================================
    # RISK MULTIPLE
    # ==================================================

    def _risk_multiple(
        exit_px,
        side,
        risk_r
    ):

        if side == "BUY":

            pnl = (
                exit_px - entry_price
            )

        else:

            pnl = (
                entry_price - exit_px
            )

        return pnl / (
            risk_r + 1e-9
        )

    # ==================================================
    # INITIALIZATION
    # ==================================================

    atr = _safe_atr(atr)

    side = signal

    risk_r = atr * 1.2

    # ==================================================
    # CORE CONTROLS
    # ==================================================

    initial_stop_mult = 1.2

    trail_mult_normal = 1.6

    trail_mult_volatile = 2.2

    breakeven_trigger_r = 0.9

    profit_lock_trigger_r = 1.8

    min_hold_bars = 2

    # ==================================================
    # THESIS ENGINE
    # ==================================================

    peak_thesis_score = 0

    # ==================================================
    # INITIAL STOPS
    # ==================================================

    if side == "BUY":

        stop_price = (
            entry_price
            - initial_stop_mult * atr
        )

        best_price = entry_price

    elif side == "SELL":

        stop_price = (
            entry_price
            + initial_stop_mult * atr
        )

        best_price = entry_price

    else:

        px = float(
            future_candles.iloc[-1]["close"]
        )

        return {

            "exit_price": round(px, 2),

            "exit_reason": "TIME_EXIT",

            "holding_time": int(
                len(future_candles)
            ),

            "risk_multiple": round(
                0.0,
                3
            ),
        }

    # ==================================================
    # MAIN LOOP
    # ==================================================

    for i, (_, candle) in enumerate(
        future_candles.iterrows(),
        start=1
    ):

        # ==================================================
        # PRICE DATA
        # ==================================================

        high = float(candle["high"])

        low = float(candle["low"])

        close = float(candle["close"])

        # ==================================================
        # ATR
        # ==================================================

        bar_atr = float(
            candle.get("ATR", atr)
        ) if "ATR" in candle else atr

        bar_atr = (
            bar_atr
            if bar_atr > 0
            else atr
        )

        atr_pct = (
            bar_atr
            / (abs(close) + 1e-9)
        )

        trail_mult = (

            trail_mult_volatile

            if atr_pct > 0.02

            else trail_mult_normal
        )

        # ==================================================
        # THESIS SCORE
        # ==================================================

        thesis_score = 0

        # VWAP
        if (
            "VWAP" in candle
            and close > float(candle["VWAP"])
        ):
            thesis_score += 1

        # BREAKOUT PRESSURE
        if (
            "breakout_pressure" in candle
            and float(
                candle["breakout_pressure"]
            ) > 0
        ):
            thesis_score += 1

        # MOMENTUM PERSISTENCE
        if (
            "momentum_persistence" in candle
            and float(
                candle["momentum_persistence"]
            ) > 0
        ):
            thesis_score += 1

        # EMA STRUCTURE
        if (
            "EMA_9" in candle
            and "EMA_20" in candle
            and float(candle["EMA_9"])
            > float(candle["EMA_20"])
        ):
            thesis_score += 1

        # ADX TREND QUALITY
        if (
            "ADX" in candle
            and float(candle["ADX"]) > 20
        ):
            thesis_score += 1

        # ==================================================
        # TRACK PEAK THESIS
        # ==================================================

        peak_thesis_score = max(
            peak_thesis_score,
            thesis_score
        )

        # ==================================================
        # BUY SIDE
        # ==================================================

        if side == "BUY":

            best_price = max(
                best_price,
                high
            )

            unrealized_r = (
                best_price - entry_price
            ) / (
                risk_r + 1e-9
            )

            # ==================================================
            # LIFECYCLE LOGGER
            # ==================================================

            log_thesis_lifecycle(

                symbol="UNKNOWN",

                side=side,

                holding_time=i,

                close=close,

                thesis_score=thesis_score,

                peak_thesis_score=peak_thesis_score,

                unrealized_r=unrealized_r,

                market_regime=candle.get(
                    "market_regime",
                    "UNKNOWN"
                ),

                entry_price=entry_price,

                exit_reason=None
            )

            # ==================================================
            # BREAK EVEN
            # ==================================================

            if (
                unrealized_r
                >= breakeven_trigger_r
            ):

                stop_price = max(
                    stop_price,
                    entry_price
                )

            # ==================================================
            # PROFIT LOCK
            # ==================================================

            if (
                unrealized_r
                >= profit_lock_trigger_r
            ):

                lock_price = (

                    entry_price

                    + (
                        best_price
                        - entry_price
                    ) * 0.45
                )

                stop_price = max(
                    stop_price,
                    lock_price
                )

            # ==================================================
            # DELAYED TRAILING
            # ==================================================

            if unrealized_r >= 1.5:

                trailing_stop = (

                    best_price

                    - trail_mult * bar_atr
                )

                stop_price = max(
                    stop_price,
                    trailing_stop
                )

            # ==================================================
            # THESIS DETERIORATION EXIT
            # ==================================================

            if (
                peak_thesis_score >= 4
                and thesis_score <= 2
            ):

                return {

                    "exit_price": round(
                        close,
                        2
                    ),

                    "exit_reason":
                    "THESIS_DETERIORATION",

                    "holding_time": i,

                    "risk_multiple": round(
                        _risk_multiple(
                            close,
                            side,
                            risk_r
                        ),
                        3
                    ),
                }

            # ==================================================
            # HARD STOP EXIT
            # ==================================================

            if (
                i >= min_hold_bars
                and low <= stop_price
            ):

                exit_px = stop_price

                return {

                    "exit_price": round(
                        exit_px,
                        2
                    ),

                    "exit_reason":
                    "ATR_TRAIL_STOP",

                    "holding_time": i,

                    "risk_multiple": round(
                        _risk_multiple(
                            exit_px,
                            side,
                            risk_r
                        ),
                        3
                    ),
                }

        # ==================================================
        # SELL SIDE
        # ==================================================

        else:

            best_price = min(
                best_price,
                low
            )

            unrealized_r = (
                entry_price
                - best_price
            ) / (
                risk_r + 1e-9
            )

            # ==================================================
            # LIFECYCLE LOGGER
            # ==================================================

            log_thesis_lifecycle(

                symbol="UNKNOWN",

                side=side,

                holding_time=i,

                close=close,

                thesis_score=thesis_score,

                peak_thesis_score=peak_thesis_score,

                unrealized_r=unrealized_r,

                market_regime=candle.get(
                    "market_regime",
                    "UNKNOWN"
                ),

                entry_price=entry_price,

                exit_reason=None
            )

            # ==================================================
            # BREAK EVEN
            # ==================================================

            if (
                unrealized_r
                >= breakeven_trigger_r
            ):

                stop_price = min(
                    stop_price,
                    entry_price
                )

            # ==================================================
            # PROFIT LOCK
            # ==================================================

            if (
                unrealized_r
                >= profit_lock_trigger_r
            ):

                lock_price = (

                    entry_price

                    - (
                        entry_price
                        - best_price
                    ) * 0.45
                )

                stop_price = min(
                    stop_price,
                    lock_price
                )

            # ==================================================
            # DELAYED TRAILING
            # ==================================================

            if unrealized_r >= 1.5:

                trailing_stop = (

                    best_price

                    + trail_mult * bar_atr
                )

                stop_price = min(
                    stop_price,
                    trailing_stop
                )

            # ==================================================
            # THESIS DETERIORATION EXIT
            # ==================================================

            if (
                peak_thesis_score >= 4
                and thesis_score <= 2
            ):

                return {

                    "exit_price": round(
                        close,
                        2
                    ),

                    "exit_reason":
                    "THESIS_DETERIORATION",

                    "holding_time": i,

                    "risk_multiple": round(
                        _risk_multiple(
                            close,
                            side,
                            risk_r
                        ),
                        3
                    ),
                }

            # ==================================================
            # HARD STOP EXIT
            # ==================================================

            if (
                i >= min_hold_bars
                and high >= stop_price
            ):

                exit_px = stop_price

                return {

                    "exit_price": round(
                        exit_px,
                        2
                    ),

                    "exit_reason":
                    "ATR_TRAIL_STOP",

                    "holding_time": i,

                    "risk_multiple": round(
                        _risk_multiple(
                            exit_px,
                            side,
                            risk_r
                        ),
                        3
                    ),
                }

    # ==================================================
    # FINAL EXIT
    # ==================================================

    final_px = float(
        future_candles.iloc[-1]["close"]
    )

    return {

        "exit_price": round(
            final_px,
            2
        ),

        "exit_reason": "TIME_EXIT",

        "holding_time": int(
            len(future_candles)
        ),

        "risk_multiple": round(
            _risk_multiple(
                final_px,
                side,
                risk_r
            ),
            3
        ),
    }
