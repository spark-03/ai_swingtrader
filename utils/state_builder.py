import numpy as np
import pandas as pd

class StateError(Exception):
    """Raised when the RL state vector is invalid (wrong shape or contains NaNs)."""

def validate_state(state: np.ndarray, expected_len: int = 21) -> None:
    """Validate that `state` has the expected length and contains no NaNs/Infs.

    Parameters
    ----------
    state: np.ndarray
        The state vector to validate.
    expected_len: int, optional
        Expected number of elements (default 21).

    Raises
    ------
    StateError
        If the length is incorrect or NaNs/Infs are present.
    """
    if state.shape[0] != expected_len:
        raise StateError(f"State length {state.shape[0]} != expected {expected_len}")
    if np.isnan(state).any() or np.isinf(state).any():
        raise StateError("State contains NaN or infinite values")
    """Validate that `state` has the expected length and contains no NaNs/Infs.

    Parameters
    ----------
    state: np.ndarray
        The state vector to validate.
    expected_len: int, optional
        Expected number of elements (default 19).

    Raises
    ------
    StateError
        If the length is incorrect or NaNs/Infs are present.
    """
    if state.shape[0] != expected_len:
        raise StateError(f"State length {state.shape[0]} != expected {expected_len}")
    if np.isnan(state).any() or np.isinf(state).any():
        raise StateError("State contains NaN or infinite values")

def safe_divide(a, b, eps=1e-9):
    """Safely divide ``a`` by ``b`` returning 0 when ``b`` is near zero.

    Parameters
    ----------
    a : float or np.ndarray
        Numerator.
    b : float or np.ndarray
        Denominator.
    eps : float, optional
        Small epsilon to avoid division by zero (default 1e-9).
    """
    return np.where(np.abs(b) > eps, a / b, 0.0)

def build_state(df: pd.DataFrame, position_flag: int = 0, hold_candles: int = 0) -> np.ndarray:
    """Build a feature vector from the **latest** row of a DataFrame.

    The function extracts a set of technical indicators, normalises them and
    returns a 1‑D ``np.ndarray`` of ``float32`` values ready for an RL agent.

    It is defensive: if the DataFrame is empty it raises a ``ValueError``.
    """
    if df.empty:
        # Return a zero‑filled state vector matching the expected feature size (18)
        return np.zeros(18, dtype=np.float32)

    latest = df.iloc[-1]
    close = latest["close"]

    # ------------------------------------------------------------------
    # Indicator normalisation (safe division where needed)
    # ------------------------------------------------------------------
    rsi = safe_divide(latest.get("RSI", 0), 100)
    macd = safe_divide(latest.get("MACD", 0), close)
    macd_signal = safe_divide(latest.get("MACD_SIGNAL", 0), close)
    macd_diff = safe_divide(latest.get("MACD_DIFF", 0), close)

    ema20_dist = safe_divide(close - latest.get("EMA20", 0), close)
    ema50_dist = safe_divide(close - latest.get("EMA50", 0), close)
    vwap_dist = safe_divide(close - latest.get("VWAP", 0), close)
    atr = safe_divide(latest.get("ATR", 0), close)

    # Bollinger bands
    bb_high = latest.get("BB_HIGH", 0)
    bb_low = latest.get("BB_LOW", 0)
    bb_width = safe_divide(bb_high - bb_low, close)
    bb_position = safe_divide(close - bb_low, bb_high - bb_low)

    # Returns
    return_1 = latest.get("RETURN_1", 0)
    return_5 = latest.get("RETURN_5", 0)
    return_10 = latest.get("RETURN_10", 0)

    volatility = latest.get("VOLATILITY_10", 0)
    momentum = latest.get("MOMENTUM_10", 0) - 1

    # Volume normalisation
    recent_volume_mean = df["volume"].tail(20).mean()
    relative_volume = safe_divide(latest["volume"], recent_volume_mean)

    # Trend strength
    trend_strength = np.abs(ema20_dist - ema50_dist)

    # Recent price range
    recent_high = df["high"].tail(20).max()
    recent_low = df["low"].tail(20).min()
    range_position = safe_divide(close - recent_low, recent_high - recent_low)

    # Assemble state vector
    state = np.array([
        rsi,
        macd,
        macd_signal,
        macd_diff,
        ema20_dist,
        ema50_dist,
        trend_strength,
        vwap_dist,
        atr,
        volatility,
        bb_width,
        bb_position,
        return_1,
        return_5,
        return_10,
        momentum,
        relative_volume,
        range_position,
        # New features for state integrity
        float(position_flag),
        float(hold_candles),
    ], dtype=np.float32)

    # Replace NaNs/Infs with zeros for safety
    state = np.nan_to_num(state, nan=0.0, posinf=0.0, neginf=0.0)
    return state