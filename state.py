"""Persists last-seen utilization values so the renderer can compute
delta badges (e.g. '+2 PP') on the next refresh.

Single JSON file keyed by metric name -> last value.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

STATE_DIR = Path(__file__).parent / ".state"
STATE_PATH = STATE_DIR / "usage_last.json"


@dataclass
class Snapshot:
    five_hour_pct: float | None
    seven_day_pct: float | None
    timestamp: float


def load() -> Snapshot | None:
    if not STATE_PATH.exists():
        return None
    try:
        with STATE_PATH.open("r", encoding="utf-8") as f:
            d = json.load(f)
        return Snapshot(
            five_hour_pct=d.get("five_hour_pct"),
            seven_day_pct=d.get("seven_day_pct"),
            timestamp=d.get("timestamp", 0.0),
        )
    except Exception:
        return None


def save(five_hour_pct: float | None, seven_day_pct: float | None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "five_hour_pct": five_hour_pct,
                "seven_day_pct": seven_day_pct,
                "timestamp": time.time(),
            },
            f,
        )


def delta(current: float | None, previous: float | None) -> float | None:
    """Returns rounded delta (in percentage points) or None if no comparison."""
    if current is None or previous is None:
        return None
    d = round(current - previous)
    if d == 0:
        return None
    return float(d)
