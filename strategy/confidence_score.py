from strategy.signal_engine import generate_signal

_CONF_STATS = {
    "raw_min": 101.0,
    "raw_max": -1.0,
    "norm_min": 101.0,
    "norm_max": -1.0,
    "raw_hist": {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0},
    "norm_hist": {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0},
}


def _clip(value, lower, upper):
    return max(lower, min(upper, float(value)))


def _normalize_confidence(value, center=50.0, span=50.0):
    """
    Normalize 0-100 confidence around a center.
    Returns 0-100 to preserve pipeline compatibility.
    """
    normalized = (float(value) - center) / (span + 1e-9)
    normalized = _clip(normalized, -1.0, 1.0)
    return (normalized + 1.0) * 50.0


def _bucket_label(value):
    v = float(value)
    if v < 20:
        return "0-20"
    if v < 40:
        return "20-40"
    if v < 60:
        return "40-60"
    if v < 80:
        return "60-80"
    return "80-100"


def _update_stats(raw_confidence, normalized_confidence):
    _CONF_STATS["raw_min"] = min(_CONF_STATS["raw_min"], float(raw_confidence))
    _CONF_STATS["raw_max"] = max(_CONF_STATS["raw_max"], float(raw_confidence))
    _CONF_STATS["norm_min"] = min(_CONF_STATS["norm_min"], float(normalized_confidence))
    _CONF_STATS["norm_max"] = max(_CONF_STATS["norm_max"], float(normalized_confidence))
    _CONF_STATS["raw_hist"][_bucket_label(raw_confidence)] += 1
    _CONF_STATS["norm_hist"][_bucket_label(normalized_confidence)] += 1


def _smooth_confidence(raw_confidence, previous_confidence=None, alpha=0.70):
    """
    Exponential smoothing hook to reduce whipsaw confidence jumps.
    If previous confidence is unavailable, returns raw confidence.
    """
    if previous_confidence is None:
        return float(raw_confidence)
    return alpha * float(raw_confidence) + (1.0 - alpha) * float(previous_confidence)


def _apply_regime_adjustment(confidence, regime=None):
    """
    Regime adjustment hook.
    Kept intentionally lightweight and non-conflicting with signal-engine weights.
    """
    if regime is None:
        return confidence, None

    regime_key = str(regime).upper()
    if regime_key == "SIDEWAYS":
        adjusted = confidence * 0.90
        return adjusted, "Regime penalty: SIDEWAYS x0.90"
    if regime_key == "VOLATILE":
        adjusted = confidence * 0.95
        return adjusted, "Regime penalty: VOLATILE x0.95"
    if regime_key == "TRENDING":
        adjusted = confidence * 1.03
        return adjusted, "Regime boost: TRENDING x1.03"
    if regime_key == "LOW_VOLUME":
        adjusted = confidence * 0.70
        return adjusted, "Regime penalty: LOW_VOLUME x0.70"
    return confidence, None


def _apply_volatility_penalty(confidence, latest_row, atr_col="ATR", close_col="close"):
    """
    Volatility penalty hook based on ATR percentage of price.
    Designed as a soft penalty to prevent overtrading in unstable conditions.
    """
    if latest_row is None or atr_col not in latest_row or close_col not in latest_row:
        return confidence, None

    close = float(latest_row.get(close_col, 0.0) or 0.0)
    atr = float(latest_row.get(atr_col, 0.0) or 0.0)
    if close <= 0:
        return confidence, None

    atr_pct = atr / (close + 1e-9)
    if atr_pct > 0.03:
        adjusted = confidence * 0.92
        return adjusted, "Volatility penalty: ATR%>3% x0.92"
    if atr_pct > 0.02:
        adjusted = confidence * 0.96
        return adjusted, "Volatility penalty: ATR%>2% x0.96"
    return confidence, None


def calculate_confidence_details(
    df,
    regime=None,
    previous_confidence=None,
    drawdown=None,
    normalize=False,
    smoothing=True,
    confidence_floor=0.0,
    confidence_ceiling=100.0,
):
    """
    Structured confidence API aligned to signal_engine.py single-source logic.
    """
    signal_data = generate_signal(df)
    raw_confidence = float(signal_data.get("confidence", 0.0))
    confidence = raw_confidence
    adjustments = []

    if normalize:
        before = confidence
        confidence = _normalize_confidence(confidence)
        adjustments.append(f"Normalization applied: {before:.2f}->{confidence:.2f}")

    latest_row = df.iloc[-1] if len(df) else None

    confidence, regime_note = _apply_regime_adjustment(confidence, regime=regime)
    if regime_note:
        adjustments.append(regime_note)

    # Harder filter semantics in low participation regime:
    # reject the weakest low-volume setups entirely by collapsing confidence.
    if str(regime).upper() == "LOW_VOLUME" and confidence < 72:
        adjustments.append("LOW_VOLUME gate: confidence<72 -> forced to 0")
        confidence = 0.0

    confidence, vol_note = _apply_volatility_penalty(confidence, latest_row=latest_row)
    if vol_note:
        adjustments.append(vol_note)

    # Drawdown hook reserved for portfolio-aware callers.
    if drawdown is not None and drawdown > 0.10:
        before = confidence
        confidence *= 0.95
        adjustments.append(f"Drawdown guard (>10%): {before:.2f}->{confidence:.2f}")

    if smoothing:
        before = confidence
        confidence = _smooth_confidence(confidence, previous_confidence=previous_confidence)
        if previous_confidence is not None:
            adjustments.append(f"Smoothing applied: {before:.2f}->{confidence:.2f}")

    clipped = _clip(confidence, confidence_floor, confidence_ceiling)
    if clipped != confidence:
        adjustments.append(
            f"Clipping applied: {confidence:.2f}->{clipped:.2f} [{confidence_floor:.1f},{confidence_ceiling:.1f}]"
        )
    confidence = clipped
    _update_stats(raw_confidence, confidence)

    return {
        "confidence": int(round(confidence)),
        "adjustments": adjustments,
        "raw_confidence": int(round(raw_confidence)),
        "diagnostics": {
            "raw_score_range": [round(_CONF_STATS["raw_min"], 2), round(_CONF_STATS["raw_max"], 2)],
            "normalized_score_range": [round(_CONF_STATS["norm_min"], 2), round(_CONF_STATS["norm_max"], 2)],
            "raw_histogram_counts": dict(_CONF_STATS["raw_hist"]),
            "normalized_histogram_counts": dict(_CONF_STATS["norm_hist"]),
        },
    }


def calculate_confidence(df, **kwargs):
    """
    Backward-compatible API used by backtesting pipeline.
    Returns numeric confidence only.
    """
    details = calculate_confidence_details(df, **kwargs)
    return details["confidence"]
