def manage_exit(
    signal,
    entry_price,
    future_candles,
    atr
):

    # Dynamic target & stoploss using ATR

    target_multiplier = 1.5
    stoploss_multiplier = 1.0

    # BUY Trade
    if signal == "BUY":

        target_price = (
            entry_price +
            (atr * target_multiplier)
        )

        stoploss_price = (
            entry_price -
            (atr * stoploss_multiplier)
        )

        for _, candle in future_candles.iterrows():

            high = candle["high"]
            low = candle["low"]

            # Target Hit
            if high >= target_price:

                return {
                    "exit_price": round(target_price, 2),
                    "exit_reason": "TARGET HIT"
                }

            # Stoploss Hit
            elif low <= stoploss_price:

                return {
                    "exit_price": round(stoploss_price, 2),
                    "exit_reason": "STOPLOSS HIT"
                }

    # SELL Trade
    elif signal == "SELL":

        target_price = (
            entry_price -
            (atr * target_multiplier)
        )

        stoploss_price = (
            entry_price +
            (atr * stoploss_multiplier)
        )

        for _, candle in future_candles.iterrows():

            high = candle["high"]
            low = candle["low"]

            # Target Hit
            if low <= target_price:

                return {
                    "exit_price": round(target_price, 2),
                    "exit_reason": "TARGET HIT"
                }

            # Stoploss Hit
            elif high >= stoploss_price:

                return {
                    "exit_price": round(stoploss_price, 2),
                    "exit_reason": "STOPLOSS HIT"
                }

    # Time Exit
    return {

        "exit_price": round(
            future_candles.iloc[-1]["close"],
            2
        ),

        "exit_reason": "TIME EXIT"
    }