"""Plan info screen with organic, layered animation.

Layers (decoupled phases so it doesn't feel mechanical):
  - Center dot       : ease pulse at base rhythm
  - Spokes           : ripple around the circle (phase offset per spoke)
  - Glyph rotation   : continuous slow drift (~30deg per cycle)
  - Halo             : breathes at 0.7x base rate (polyrhythm)

2.4s base cycle, 30 frames @ 80ms.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import theme as t


CREDENTIALS_PATH = Path(os.environ["USERPROFILE"]) / ".claude" / ".credentials.json"


def _read_plan() -> str:
    try:
        with CREDENTIALS_PATH.open("r", encoding="utf-8") as f:
            creds = json.load(f)
        inner = creds.get("claudeAiOauth") or creds
        rate_tier = inner.get("rateLimitTier", "")
        if "max_20x" in rate_tier:
            return "MAX 20X"
        if "max_5x" in rate_tier or "max5x" in rate_tier:
            return "MAX 5X"
        if "pro" in rate_tier.lower():
            return "PRO"
        return rate_tier.upper().replace("_", " ") or "CLAUDE"
    except Exception:
        return "CLAUDE"


def _glyph(d: ImageDraw.ImageDraw, cx: int, cy: int, phase: float) -> None:
    """phase in [0..1]. Spokes ripple around the circle with phase offsets;
    the whole glyph drifts slowly (30deg per cycle)."""

    base_rotation = phase * math.pi / 6

    center_phase = (phase * 1.17) % 1.0
    center_breath = t.ease_in_out(center_phase if center_phase < 0.5 else 1 - center_phase) * 2
    r_inner = 3.6 + 0.35 * center_breath
    d.ellipse(
        [cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
        fill=t.ACCENT,
    )

    n_spokes = 12
    inner_base = 12.0
    outer_base = 29.0
    for i in range(n_spokes):
        spoke_phase = (phase - i / n_spokes) % 1.0
        weight = max(0.0, math.cos(2 * math.pi * spoke_phase))
        weight = weight ** 2

        outer = outer_base + 3.2 * weight
        inner = inner_base + 0.4 * weight

        if weight > 0.4:
            color = t.ACCENT_BRIGHT
        else:
            color = t.ACCENT

        a = i * 2 * math.pi / n_spokes + base_rotation
        x1 = cx + math.cos(a) * inner
        y1 = cy + math.sin(a) * inner
        x2 = cx + math.cos(a) * outer
        y2 = cy + math.sin(a) * outer
        d.line([(x1, y1), (x2, y2)], fill=color, width=2)


def _draw_halo(size: int, cy: int) -> Image.Image:
    halo = Image.new("RGB", (size, size), t.BG)
    hd = ImageDraw.Draw(halo)
    for i in range(6, 0, -1):
        hd.ellipse(
            [size // 2 - 7 * i, cy - 7 * i, size // 2 + 7 * i, cy + 7 * i],
            outline=(204, 120, 92),
            width=1,
        )
    return halo.filter(ImageFilter.GaussianBlur(radius=8))


def _draw_text_layer(
    d: ImageDraw.ImageDraw, model: str, plan: str
) -> None:
    model_font = t.font_bold(22)
    plan_font = t.font_bold(18)

    mw = d.textlength(model, font=model_font)
    d.text(((t.SIZE - mw) // 2, 160), model, font=model_font, fill=t.TEXT)

    pw = d.textlength(plan, font=plan_font)
    d.text(((t.SIZE - pw) // 2, 194), plan, font=plan_font, fill=t.ACCENT)


def _render_frame(
    phase: float, model: str, plan: str, halo_layer: Image.Image
) -> Image.Image:
    halo_phase = (phase * 0.7) % 1.0
    halo_breath = t.ease_in_out(halo_phase if halo_phase < 0.5 else 1 - halo_phase) * 2
    halo_blend = 0.42 + 0.08 * halo_breath

    img = Image.new("RGB", (t.SIZE, t.SIZE), t.BG)
    img = Image.blend(img, halo_layer, halo_blend)

    d = ImageDraw.Draw(img)
    _glyph(d, t.SIZE // 2, 88, phase)
    _draw_text_layer(d, model, plan)
    return img


def render(model: str = "OPUS 4.7") -> Image.Image:
    plan = _read_plan()
    halo = _draw_halo(t.SIZE, 88)
    return _render_frame(0.0, model, plan, halo)


def render_gif(
    out_path: Path,
    model: str = "OPUS 4.7",
    frames: int = 30,
    frame_ms: int = 80,
) -> Path:
    plan = _read_plan()
    halo = _draw_halo(t.SIZE, 88)
    imgs = [
        _render_frame(i / frames, model, plan, halo).convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=64
        )
        for i in range(frames)
    ]
    imgs[0].save(
        out_path,
        save_all=True,
        append_images=imgs[1:],
        duration=frame_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return out_path
