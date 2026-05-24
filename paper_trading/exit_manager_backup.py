def manage_exit(
    signal,
    entry_price,
    future_candles,
    atr
):
    def _safe_atr(x):
        try:
            val = float(x)
            return val if val > 0 else 0.01 * float(entry_price)
        except Exception:
            return 0.01 * float(entry_price)

    def _risk_multiple(exit_px, side, risk_r):
        if side == "BUY":
            pnl = exit_px - entry_price
        else:
            pnl = entry_price - exit_px
        return pnl / (risk_r + 1e-9)

    atr = _safe_atr(atr)
    side = signal
    risk_r = atr * 1.2

    # Core adaptive controls
    initial_stop_mult = 1.2
    trail_mult_normal = 1.6
    trail_mult_volatile = 2.2
    breakeven_trigger_r = 0.9
    profit_lock_trigger_r = 1.8
    min_hold_bars = 2

    if side == "BUY":
        stop_price = entry_price - initial_stop_mult * atr
        best_price = entry_price
    elif side == "SELL":
        stop_price = entry_price + initial_stop_mult * atr
        best_price = entry_price
    else:
        px = float(future_candles.iloc[-1]["close"])
        return {
            "exit_price": round(px, 2),
            "exit_reason": "TIME EXIT",
            "holding_time": int(len(future_candles)),
            "risk_multiple": round(0.0, 3),
        }

    for i, (_, candle) in enumerate(future_candles.iterrows(), start=1):
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])
        bar_atr = float(candle.get("ATR", atr)) if "ATR" in candle else atr
        bar_atr = bar_atr if bar_atr > 0 else atr

        atr_pct = bar_atr / (abs(close) + 1e-9)
        trail_mult = trail_mult_volatile if atr_pct > 0.02 else trail_mult_normal

        if side == "BUY":
            best_price = max(best_price, high)
            unrealized_r = (best_price - entry_price) / (risk_r + 1e-9)

            # Break-even protection once trade proves itself.
            if unrealized_r >= breakeven_trigger_r:
                stop_price = max(stop_price, entry_price)

            # Dynamic profit lock: protect a share of gains while allowing continuation.
            if unrealized_r >= profit_lock_trigger_r:
                lock_price = entry_price + (best_price - entry_price) * 0.45
                stop_price = max(stop_price, lock_price)

            # ATR trailing stop for trend continuation holding.
            trailing_stop = best_price - trail_mult * bar_atr
            stop_price = max(stop_price, trailing_stop)

            if i >= min_hold_bars and low <= stop_price:
                exit_px = stop_price
                return {
                    "exit_price": round(exit_px, 2),
                    "exit_reason": "ATR_TRAIL_STOP",
                    "holding_time": i,
                    "risk_multiple": round(_risk_multiple(exit_px, side, risk_r), 3),
                }

        else:  # SELL
            best_price = min(best_price, low)
            unrealized_r = (entry_price - best_price) / (risk_r + 1e-9)

            if unrealized_r >= breakeven_trigger_r:
                stop_price = min(stop_price, entry_price)

            if unrealized_r >= profit_lock_trigger_r:
                lock_price = entry_price - (entry_price - best_price) * 0.45
                stop_price = min(stop_price, lock_price)

            trailing_stop = best_price + trail_mult * bar_atr
            stop_price = min(stop_price, trailing_stop)

            if i >= min_hold_bars and high >= stop_price:
                exit_px = stop_price
                return {
                    "exit_price": round(exit_px, 2),
                    "exit_reason": "ATR_TRAIL_STOP",
                    "holding_time": i,
                    "risk_multiple": round(_risk_multiple(exit_px, side, risk_r), 3),
                }

    # Time/last-candle exit fallback.
    final_px = float(future_candles.iloc[-1]["close"])
    return {
        "exit_price": round(final_px, 2),
        "exit_reason": "TIME_EXIT",
        "holding_time": int(len(future_candles)),
        "risk_multiple": round(_risk_multiple(final_px, side, risk_r), 3),
    }
