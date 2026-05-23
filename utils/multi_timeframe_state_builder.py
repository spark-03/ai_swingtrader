import numpy as np

from utils.state_builder import build_state

from utils.regime_detector import (
    detect_market_regime
)


# ====================================
# BUILD MULTI-TIMEFRAME STATE
# ====================================

def build_multi_timeframe_state(

    daily_df,

    hourly_df,

    five_df,

    portfolio_features
):

    # ====================================
    # TIMEFRAME STATES
    # ====================================

    daily_state = build_state(

        daily_df
    )

    hourly_state = build_state(

        hourly_df
    )

    five_state = build_state(

        five_df
    )

    # ====================================
    # MARKET REGIME
    # ====================================

    regime_state = detect_market_regime(

        daily_df
    )

    # ====================================
    # COMBINE ALL STATES
    # ====================================

    state = np.concatenate([

        # DAILY
        daily_state,

        # HOURLY
        hourly_state,

        # 5MIN
        five_state,

        # REGIME
        regime_state,

        # PORTFOLIO
        portfolio_features
    ])

    # ====================================
    # CLEAN
    # ====================================

    state = np.nan_to_num(

        state,

        nan=0,

        posinf=0,

        neginf=0
    )

    return state.astype(np.float32)