import numpy as np

from utils.multi_timeframe_state_builder import (
    build_multi_timeframe_state
)


class StateManager:

    def __init__(self):

        pass

    # ====================================
    # BUILD STATE
    # ====================================

    def build_state(
    self,
    daily_df,
    hourly_df,
    five_df,
    current_step,
    balance,
    initial_balance,
    positions,
    max_positions,
    portfolio_value
):
    # ====================================
    # SAFE INDICES
    # ====================================
    daily_index = min(
        len(daily_df) - 1,
        max(
            50,
            current_step // 75
        )
    )

    hourly_index = min(
        len(hourly_df) - 1,
        max(
            50,
            current_step // 12
        )
    )

    five_index = min(
        len(five_df) - 1,
        current_step
    )

    # ====================================
    # DATA WINDOWS
    # ====================================
    daily_window = daily_df.iloc[:daily_index]
    hourly_window = hourly_df.iloc[:hourly_index]
    five_window = five_df.iloc[:five_index]

    # ====================================
    # CURRENT ROW
    # ====================================
    current_row = five_df.iloc[five_index]

    # ====================================
    # PORTFOLIO FEATURES
    # ====================================
    portfolio_features = np.array([
        balance / initial_balance,
        len(positions) / max_positions,
        portfolio_value / initial_balance,
        current_row["compression_score"],
        current_row["breakout_pressure"],
        current_row["momentum_persistence"],
        current_row["momentum_score"]
    ])

    # ====================================
    # BUILD MULTI‑TIMEFRAME STATE (dict)
    # ====================================
    components = build_multi_timeframe_state(
        daily_window,
        hourly_window,
        five_window,
        portfolio_features
    )

    # Concatenate all components into a single vector
    state = np.concatenate([
        components["daily"],
        components["hourly"],
        components["five"],
        components["regime"],
        components["portfolio"]
    ])

    # Truncate / pad to exactly 21 elements for RL stability
    if state.shape[0] >= 21:
        state = state[:21]
    else:
        # Pad with zeros if somehow shorter
        state = np.pad(state, (0, 21 - state.shape[0]), "constant")

    return state.astype(np.float32)

        # ====================================
        # SAFE INDICES
        # ====================================

        daily_index = min(

            len(daily_df) - 1,

            max(
                50,
                current_step // 75
            )
        )

        hourly_index = min(

            len(hourly_df) - 1,

            max(
                50,
                current_step // 12
            )
        )

        five_index = min(

            len(five_df) - 1,

            current_step
        )

        # ====================================
        # DATA WINDOWS
        # ====================================

        daily_window = daily_df.iloc[
            :daily_index
        ]

        hourly_window = hourly_df.iloc[
            :hourly_index
        ]

        five_window = five_df.iloc[
            :five_index
        ]

        # ====================================
        # CURRENT ROW
        # ====================================

        current_row = five_df.iloc[
            five_index
        ]

        # ====================================
        # PORTFOLIO FEATURES
        # ====================================

        portfolio_features = np.array([

    # ====================================
    # PORTFOLIO FEATURES
    # ====================================

    balance / initial_balance,

    len(positions)
    / max_positions,

    portfolio_value
    / initial_balance,

    # ====================================
    # VOLATILITY STRUCTURE
    # ====================================

    current_row[
        "compression_score"
    ],

    # ====================================
    # BREAKOUT STRUCTURE
    # ====================================

    current_row[
        "breakout_pressure"
    ],

    # ====================================
    # MOMENTUM STRUCTURE
    # ====================================

    current_row[
        "momentum_persistence"
    ],

    current_row[
        "momentum_score"
    ]
])

        # ====================================
        # BUILD MULTI-TIMEFRAME STATE
        # ====================================

        state = build_multi_timeframe_state(

            daily_window,

            hourly_window,

            five_window,

            portfolio_features
        )

        return state.astype(np.float32)