"""Screen: Aktuelle Sitzung (5h limit)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from . import _limit


def _fmt_reset(seconds: int | None) -> str:
    if seconds is None:
        return ""
    if seconds < 60:
        return "<1M"
    if seconds < 3600:
        return f"{seconds // 60}M"
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    return f"{h}H {m:02d}M" if m else f"{h}H"


def render(
    pct: float, reset_seconds: int | None, delta_pp: float | None = None
) -> Image.Image:
    return _limit.render("SESSION", pct, _fmt_reset(reset_seconds), delta_pp)


def render_gif(
    out_path: Path,
    pct: float,
    reset_seconds: int | None,
    delta_pp: float | None = None,
) -> Path:
    return _limit.render_gif(
        out_path, "SESSION", pct, _fmt_reset(reset_seconds), delta_pp
    )
