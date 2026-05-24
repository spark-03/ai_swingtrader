import math
from typing import Dict, Any

# Default weight configuration for elite scoring (must sum to 100)
DEFAULT_WEIGHTS = {
    "compression": 20,
    "breakout_pressure": 20,
    "momentum_persistence": 15,
    "trend_alignment": 15,
    "relative_volume": 10,
    "relative_strength": 20,
}

def _load_weights() -> Dict[str, int]:
    """Load scoring weights from a config file if present.
    Falls back to DEFAULT_WEIGHTS.
    """
    try:
        from utils.config_loader import ConfigLoader
        config = ConfigLoader("config/elite_scoring.yaml")
        weights = config.get("weights", DEFAULT_WEIGHTS)
        for key, default in DEFAULT_WEIGHTS.items():
            if key not in weights:
                weights[key] = default
        return weights
    except Exception:
        return DEFAULT_WEIGHTS

_WEIGHTS = _load_weights()
_TOTAL_WEIGHT = sum(_WEIGHTS.values())

def _normalize(value: Any, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp and normalize a value to [0, 1] range.
    If the value is already between 0 and 1 it is returned unchanged.
    """
    try:
        v = float(value)
    except Exception:
        return 0.0
    if max_val == min_val:
        return 0.0
    v = (v - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, v))

def _relative_strength(row: Dict[str, Any]) -> float:
    """Extract or compute relative strength feature.
    Expected column ``relative_strength``; defaults to 0.5.
    """
    return _normalize(row.get("relative_strength", 0.5))

def _score(row: Dict[str, Any], relative_volume: float) -> float:
    """Core scoring formula returning 0‑100 range.
    All individual features are assumed to be in a 0‑1 range.
    """
    compression = _normalize(row.get("compression_score", 0.0))
    breakout = _normalize(row.get("breakout_pressure", 0.0))
    momentum = _normalize(row.get("momentum_score", 0.0))
    trend = _normalize(row.get("trend_alignment", 0.0))
    rel_vol = _normalize(relative_volume)
    rel_str = _relative_strength(row)

    weighted_sum = (
        compression * _WEIGHTS["compression"]
        + breakout * _WEIGHTS["breakout_pressure"]
        + momentum * _WEIGHTS["momentum_persistence"]
        + trend * _WEIGHTS["trend_alignment"]
        + rel_vol * _WEIGHTS["relative_volume"]
        + rel_str * _WEIGHTS["relative_strength"]
    )
    return (weighted_sum / _TOTAL_WEIGHT) * 100.0

class EliteScoring:
    """Convenient wrapper exposing ``is_elite`` and ``score`` methods.
    ``threshold`` defaults to 80 as defined in the redesign plan.
    """
    def __init__(self, threshold: float = 80.0):
        self.threshold = threshold

    def score(self, row: Dict[str, Any], relative_volume: float) -> float:
        return _score(row, relative_volume)

    def is_elite(self, row: Dict[str, Any], relative_volume: float) -> bool:
        return self.score(row, relative_volume) >= self.threshold
