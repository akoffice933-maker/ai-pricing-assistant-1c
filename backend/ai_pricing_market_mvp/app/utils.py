"""Мелкие математические/временные хелперы, используемые в нескольких services."""

import math
from datetime import datetime, timezone
from typing import List


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def percentile(sorted_values: List[float], q: float) -> float:
    """Линейный percentile для уже отсортированного списка."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return float(sorted_values[int(pos)])
    return float(sorted_values[low] * (high - pos) + sorted_values[high] * (pos - low))
