import math


def _clip01(value):
    return max(0.0, min(1.0, float(value)))


def _safe_float(row, key, default=0.0):
    value = row.get(key, default)
    if value is None:
        return float(default)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(value) or math.isinf(value):
        return float(default)
    return value


def _signed_strength(latest, close, volume_mean_20):
    components = {}
    reasons = []

    # 1) EMA trend alignment (direction + quality)
    ema_fast = _safe_float(latest, "EMA_9", close)
    ema_slow = _safe_float(latest, "EMA_21", close)
    ema_spread_pct = abs(ema_fast - ema_slow) / (abs(close) + 1e-9)
    ema_quality = _clip01(ema_spread_pct / 0.01)
    ema_direction = 1.0 if ema_fast > ema_slow else (-1.0 if ema_fast < ema_slow else 0.0)
    components["ema_trend"] = ema_direction * ema_quality
    if ema_direction > 0 and ema_quality > 0.35:
        reasons.append("EMA trend supports upside continuation")
    elif ema_direction < 0 and ema_quality > 0.35:
        reasons.append("EMA trend supports downside continuation")

    # 2) RSI momentum (continuous mapping around neutral 50)
    rsi = _safe_float(latest, "RSI", 50.0)
    rsi_centered = (rsi - 50.0) / 25.0
    components["rsi_momentum"] = max(-1.0, min(1.0, rsi_centered))
    if rsi >= 58:
        reasons.append("RSI momentum is bullish")
    elif rsi <= 42:
        reasons.append("RSI momentum is bearish")

    # 3) VWAP alignment (distance + side)
    vwap = _safe_float(latest, "VWAP", close)
    vwap_dist = (close - vwap) / (abs(close) + 1e-9)
    vwap_quality = _clip01(abs(vwap_dist) / 0.005)
    vwap_direction = 1.0 if vwap_dist > 0 else (-1.0 if vwap_dist < 0 else 0.0)
    components["vwap_alignment"] = vwap_direction * vwap_quality
    if vwap_direction > 0 and vwap_quality > 0.3:
        reasons.append("Price is holding above VWAP")
    elif vwap_direction < 0 and vwap_quality > 0.3:
        reasons.append("Price is holding below VWAP")

    # 4) ADX trend strength (amplifier, not direction)
    adx = _safe_float(latest, "ADX", 15.0)
    adx_strength = _clip01((adx - 15.0) / 20.0)
    components["adx_trend_strength"] = adx_strength
    if adx_strength > 0.55:
        reasons.append("Trend strength is confirmed by ADX")

    # 5) Breakout pressure (already normalized in your feature engine)
    breakout_pressure = _clip01(_safe_float(latest, "breakout_pressure", 0.0))
    components["breakout_pressure"] = breakout_pressure
    if breakout_pressure > 0.6:
        reasons.append("Breakout pressure is elevated")

    # 6) Momentum persistence (direction-aware when possible)
    persistence = _clip01(_safe_float(latest, "momentum_persistence", 0.0))
    momentum_score = _clip01(_safe_float(latest, "momentum_score", 0.0))
    momentum_direction = 1.0 if components["rsi_momentum"] >= 0 else -1.0
    components["momentum_persistence"] = momentum_direction * (0.6 * persistence + 0.4 * momentum_score)
    if persistence > 0.55:
        reasons.append("Momentum persistence supports follow-through")

    # 7) Relative volume (computed on the fly if not provided)
    relative_volume = _safe_float(latest, "relative_volume", 0.0)
    if relative_volume <= 0:
        relative_volume = _safe_float(latest, "volume", 0.0) / (volume_mean_20 + 1e-9)
    relative_volume = _clip01(relative_volume / 2.0)
    components["relative_volume"] = relative_volume
    if relative_volume > 0.55:
        reasons.append("Participation is strong via relative volume")

    return components, reasons


def generate_signal(df):
    latest = df.iloc[-1]
    close = _safe_float(latest, "close", 0.0)
    volume_mean_20 = float(df["volume"].tail(20).mean()) if "volume" in df.columns else 0.0

    components, reasons = _signed_strength(latest, close, volume_mean_20)

    # Weighted score: directional components drive bias, quality components scale conviction.
    directional_weights = {
        "ema_trend": 0.24,
        "rsi_momentum": 0.16,
        "vwap_alignment": 0.16,
        "momentum_persistence": 0.14,
    }
    quality_weights = {
        "adx_trend_strength": 0.14,
        "breakout_pressure": 0.10,
        "relative_volume": 0.06,
    }

    directional_score = sum(
        directional_weights[k] * components.get(k, 0.0)
        for k in directional_weights
    )
    quality_score = sum(
        quality_weights[k] * components.get(k, 0.0)
        for k in quality_weights
    )

    final_bias = directional_score * (0.70 + 0.30 * quality_score)

    buy_gate = 0.12
    sell_gate = -0.12

    if final_bias >= buy_gate:
        signal = "BUY"
        trend = "BULLISH"
    elif final_bias <= sell_gate:
        signal = "SELL"
        trend = "BEARISH"
    else:
        signal = "HOLD"
        trend = "SIDEWAYS"
        reasons = reasons + ["Signal quality is mixed; capital preservation preferred"]

    # Recalibrated confidence mapping:
    # - keeps probabilistic meaning from weighted bias
    # - expands mid/high bands to avoid bucket collapse near 0-20
    # - still preserves low confidence for mixed/weak setups
    abs_bias = abs(final_bias)
    raw_conf_01 = _clip01((abs_bias - 0.015) / 0.32)
    confidence = int(round(raw_conf_01 * 100))
    strength = "STRONG" if confidence >= 70 else ("MEDIUM" if confidence >= 45 else "WEAK")

    return {
        "signal": signal,
        "confidence": confidence,
        "reasons": reasons[:6],
        # Backward-compatible fields for existing callers.
        "trend": trend,
        "strength": strength,
        "components": components,
        "raw_bias": round(float(final_bias), 6),
        "raw_confidence_01": round(float(raw_conf_01), 6),
    }
