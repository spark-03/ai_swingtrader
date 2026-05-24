import numpy as np
from utils.state_builder import build_state
from utils.regime_detector import detect_market_regime

def build_multi_timeframe_state(
    daily_df,
    hourly_df,
    five_df,
    portfolio_features
) -> dict:
    """Construct a composite state for the RL agent.

    Returns a dictionary containing separate component vectors:
        - daily:   state from daily timeframe
        - hourly:  state from hourly timeframe
        - five:    state from 5‑minute timeframe
        - regime:  market regime vector (5 elements)
        - portfolio: user‑provided portfolio feature vector
    """
    # Build individual timeframe states
    daily_state = build_state(daily_df)
    hourly_state = build_state(hourly_df)
    five_state = build_state(five_df)

    # Detect market regime based on daily data
    regime_state = detect_market_regime(daily_df)

    # Ensure numeric safety and correct dtype
    daily_state = np.nan_to_num(daily_state.astype(np.float32))
    hourly_state = np.nan_to_num(hourly_state.astype(np.float32))
    five_state = np.nan_to_num(five_state.astype(np.float32))
    regime_state = np.nan_to_num(regime_state.astype(np.float32))
    portfolio_features = np.nan_to_num(np.array(portfolio_features, dtype=np.float32))

    return {
        "daily": daily_state,
        "hourly": hourly_state,
        "five": five_state,
        "regime": regime_state,
        "portfolio": portfolio_features,
    }