"""Screen: Woechentliches Limit (7d, alle Modelle)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from PIL import Image

from . import _limit


WEEKDAY_DE = ["MO", "DI", "MI", "DO", "FR", "SA", "SO"]


def _fmt_reset(resets_at: dt.datetime | None) -> str:
    if resets_at is None:
        return ""
    local = resets_at.astimezone()
    return f"{WEEKDAY_DE[local.weekday()]} {local.strftime('%H:%M')}"


def render(
    pct: float, resets_at: dt.datetime | None, delta_pp: float | None = None
) -> Image.Image:
    return _limit.render("7-DAY", pct, _fmt_reset(resets_at), delta_pp)


def render_gif(
    out_path: Path,
    pct: float,
    resets_at: dt.datetime | None,
    delta_pp: float | None = None,
) -> Path:
    return _limit.render_gif(
        out_path, "7-DAY", pct, _fmt_reset(resets_at), delta_pp
    )
