import math


def _clip01(value):
    return max(0.0, min(1.0, float(value)))


def _safe_float(row, key, default=0.0):
    try:
        value = float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(value) or math.isinf(value):
        return float(default)
    return value


def _relative_volume(df, latest):
    rel_vol = _safe_float(latest, "relative_volume", 0.0)
    if rel_vol > 0:
        return rel_vol
    if "volume" not in df.columns:
        return 1.0
    baseline = float(df["volume"].tail(20).mean())
    return _safe_float(latest, "volume", 0.0) / (baseline + 1e-9)


def detect_market_regime_details(df):
    latest = df.iloc[-1]
    close = _safe_float(latest, "close", 0.0)

    ema_fast = _safe_float(latest, "EMA_9", close)
    ema_slow = _safe_float(latest, "EMA_21", close)
    adx = _safe_float(latest, "ADX", 15.0)
    atr = _safe_float(latest, "ATR", 0.0)
    rel_vol = _relative_volume(df, latest)

    ema_slope = 0.0
    if "EMA_9" in df.columns and len(df) >= 6:
        ema_now = float(df["EMA_9"].iloc[-1])
        ema_prev = float(df["EMA_9"].iloc[-6])
        ema_slope = (ema_now - ema_prev) / (abs(close) + 1e-9)

    atr_pct = atr / (abs(close) + 1e-9) if close else 0.0
    ema_spread_pct = abs(ema_fast - ema_slow) / (abs(close) + 1e-9) if close else 0.0

    adx_strength = _clip01((adx - 14.0) / 22.0)
    trend_shape = _clip01(ema_spread_pct / 0.01)
    slope_strength = _clip01(abs(ema_slope) / 0.008)
    trend_strength = _clip01(0.45 * adx_strength + 0.30 * trend_shape + 0.25 * slope_strength)

    vol_strength = _clip01(atr_pct / 0.025)
    high_participation = rel_vol >= 1.2
    low_participation = rel_vol <= 0.8

    reasons = []
    if adx_strength > 0.5:
        reasons.append("ADX confirms directional persistence")
    if slope_strength > 0.45:
        reasons.append("EMA slope indicates directional continuation")
    if vol_strength > 0.7:
        reasons.append("ATR indicates elevated volatility")
    if high_participation:
        reasons.append("Relative volume shows strong participation")
    if low_participation:
        reasons.append("Relative volume is below normal participation")

    if low_participation and trend_strength < 0.55:
        regime = "LOW_VOLUME"
    elif trend_strength >= 0.58:
        regime = "TRENDING_BULL" if ema_slope >= 0 else "TRENDING_BEAR"
    elif vol_strength >= 0.82 and trend_strength < 0.58:
        regime = "VOLATILE"
    else:
        regime = "SIDEWAYS"

    return {
        "regime": regime,
        "strength": round(float(trend_strength), 4),
        "reasons": reasons[:5],
    }


def detect_market_regime(df):
    """
    Backward-compatible API: returns string regime for existing pipeline.
    """
    detailed = detect_market_regime_details(df)
    regime = detailed["regime"]
    if regime in ("TRENDING_BULL", "TRENDING_BEAR"):
        return "TRENDING"
    return regime
