"""Design tokens for the 240x240 display.

Palette chosen to read as a premium dark dashboard: pure-black canvas,
off-white primary, claude orange as the single accent, muted grays for
secondary info. Mirrors the Cloudflare / shadcn aesthetic.
"""
from __future__ import annotations

import math

from PIL import ImageFont

SIZE = 240

BG = "#0a0a0a"
SURFACE = "#141414"
HAIRLINE = "#262626"
MUTED = "#737373"
TEXT_DIM = "#a3a3a3"
TEXT = "#fafafa"
ACCENT = "#cc785c"
ACCENT_BRIGHT = "#e89478"
ACCENT_DIM = "#5a3528"
GREEN = "#4ade80"
RED = "#ef4444"


def ease_in_out(x: float) -> float:
    """Smooth cosine-based ease, more organic than raw sin."""
    return 0.5 - 0.5 * math.cos(x * math.pi)


def ease_in_out_cubic(x: float) -> float:
    """Cubic ease with stronger acceleration near the ends."""
    if x < 0.5:
        return 4 * x * x * x
    p = 2 * x - 2
    return 1 + p * p * p / 2


def blend(c1: str, c2: str, t_: float) -> tuple[int, int, int]:
    """Linear blend between two hex colors. t_ in [0..1]."""
    def rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    a, b = rgb(c1), rgb(c2)
    return tuple(int(a[i] + (b[i] - a[i]) * t_) for i in range(3))  # type: ignore

FONT_PATH = "C:/Windows/Fonts/CascadiaCode.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/CascadiaCode.ttf"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def font_bold(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD_PATH, size)


def spaced(text: str, gap: str = " ") -> str:
    """Letter-space a label by injecting a thin gap between chars."""
    return gap.join(text)


def fmt_money(usd: float) -> str:
    if usd >= 1000:
        return f"${usd:,.0f}"
    return f"${usd:,.2f}"


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def fmt_duration(seconds: int) -> str:
    seconds = max(0, seconds)
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    if h > 0:
        return f"{h}H {m:02d}M"
    return f"{m}M"


def shorten_model(name: str) -> str:
    n = name.replace("claude-", "")
    for suf in ("-20251001", "-20250929", "-20250514"):
        n = n.replace(suf, "")
    return n.upper()
