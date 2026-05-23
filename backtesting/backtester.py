from strategy.indicators import add_indicators
from strategy.signal_engine import generate_signal
from paper_trading.exit_manager import manage_exit
from strategy.market_regime import detect_market_regime
from risk.position_sizer import calculate_position_size
from strategy.confidence_score import calculate_confidence

def run_backtest(df):

    trades = []

    # Add indicators
    df = add_indicators(df)

    # Start after indicators stabilize
    for i in range(30, len(df) - 10):

        current_df = df.iloc[:i]

        latest = current_df.iloc[-1]

        signal_data = generate_signal(current_df)

        signal = signal_data["signal"]
        # Confidence score
        confidence = calculate_confidence(
    current_df
)       
        # Skip weak setups
        if confidence < 75:

         continue
        # Detect market regime
        regime = detect_market_regime(current_df)
        # Position sizing
        capital = calculate_position_size(regime)
        
        # Skip sideways markets
        if regime == "SIDEWAYS":
         continue

        # Skip HOLD trades
        if signal == "HOLD":
            continue

        # Entry price
        entry_price = latest["close"]

        # ATR for dynamic exits
        atr = latest["ATR"]

        # Future candles for exit management
        future_candles = df.iloc[i:i + 10]

        # Dynamic ATR-based exit management
        exit_data = manage_exit(
            signal,
            entry_price,
            future_candles,
            atr
        )

        exit_price = exit_data["exit_price"]

        # Calculate PnL
        if signal == "BUY":

            pnl = exit_price - entry_price

        else:

            pnl = entry_price - exit_price

        # Store trade
        trade = {

            "signal": signal,
            "confidence": confidence,

            "entry_price": float(round(entry_price, 2)),
            "exit_price": float(round(exit_price, 2)),

            "pnl": float(round(pnl, 2)),

            "exit_reason": exit_data["exit_reason"],
            "market_regime": regime,
            "capital": capital,

            "atr": float(round(atr, 2))
        }

        trades.append(trade)

    return trades