import numpy as np


# ====================================
# SAFE NORMALIZATION
# ====================================

def safe_divide(a, b):

    if b == 0:

        return 0

    return a / b


# ====================================
# BUILD STATE
# ====================================

def build_state(df):

    # ====================================
    # USE LATEST ROW
    # ====================================

    latest = df.iloc[-1]

    # ====================================
    # PRICE
    # ====================================

    close = latest["close"]

    # ====================================
    # RSI
    # ====================================

    rsi = safe_divide(

        latest["RSI"],

        100
    )

    # ====================================
    # MACD
    # ====================================

    macd = safe_divide(

        latest["MACD"],

        close
    )

    macd_signal = safe_divide(

        latest["MACD_SIGNAL"],

        close
    )

    macd_diff = safe_divide(

        latest["MACD_DIFF"],

        close
    )

    # ====================================
    # EMA DISTANCE
    # ====================================

    ema20_dist = safe_divide(

        close - latest["EMA20"],

        close
    )

    ema50_dist = safe_divide(

        close - latest["EMA50"],

        close
    )

    # ====================================
    # VWAP DISTANCE
    # ====================================

    vwap_dist = safe_divide(

        close - latest["VWAP"],

        close
    )

    # ====================================
    # ATR VOLATILITY
    # ====================================

    atr = safe_divide(

        latest["ATR"],

        close
    )

    # ====================================
    # BOLLINGER BAND POSITION
    # ====================================

    bb_high = latest["BB_HIGH"]

    bb_low = latest["BB_LOW"]

    bb_mid = latest["BB_MID"]

    bb_width = safe_divide(

        bb_high - bb_low,

        close
    )

    bb_position = safe_divide(

        close - bb_low,

        bb_high - bb_low
    )

    # ====================================
    # RETURNS
    # ====================================

    return_1 = latest["RETURN_1"]

    return_5 = latest["RETURN_5"]

    return_10 = latest["RETURN_10"]

    # ====================================
    # VOLATILITY
    # ====================================

    volatility = latest["VOLATILITY_10"]

    # ====================================
    # MOMENTUM
    # ====================================

    momentum = latest["MOMENTUM_10"] - 1

    # ====================================
    # VOLUME NORMALIZATION
    # ====================================

    recent_volume_mean = (

        df["volume"]

        .tail(20)

        .mean()
    )

    relative_volume = safe_divide(

        latest["volume"],

        recent_volume_mean
    )

    # ====================================
    # TREND STRENGTH
    # ====================================

    trend_strength = abs(

        ema20_dist - ema50_dist
    )

    # ====================================
    # PRICE VS RECENT RANGE
    # ====================================

    recent_high = (

        df["high"]

        .tail(20)

        .max()
    )

    recent_low = (

        df["low"]

        .tail(20)

        .min()
    )

    range_position = safe_divide(

        close - recent_low,

        recent_high - recent_low
    )

    # ====================================
    # STATE VECTOR
    # ====================================

    state = np.array([

        # MOMENTUM
        rsi,
        macd,
        macd_signal,
        macd_diff,

        # TREND
        ema20_dist,
        ema50_dist,
        trend_strength,

        # VWAP
        vwap_dist,

        # VOLATILITY
        atr,
        volatility,
        bb_width,
        bb_position,

        # RETURNS
        return_1,
        return_5,
        return_10,

        # MOMENTUM
        momentum,

        # VOLUME
        relative_volume,

        # PRICE STRUCTURE
        range_position
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