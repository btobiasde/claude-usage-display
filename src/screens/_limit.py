"""Shared template for single-limit screens (session, weekly).

Animation: subtle end-cap glow at the bar's fill end (eased, not raw sin).
Delta badge: when the value has changed since the last refresh, a small
'+2' or '-3' chip appears next to the label in a highlight color.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from . import theme as t


def _draw_delta_badge(
    d: ImageDraw.ImageDraw, x: int, y: int, delta_pp: float
) -> int:
    """Draws a small +N / -N chip next to the label. Returns width drawn."""
    sign = "+" if delta_pp > 0 else ""
    text = f"{sign}{int(delta_pp)}"
    chip_font = t.font_bold(11)
    tw = d.textlength(text, font=chip_font)
    pad_x = 6
    chip_w = int(tw + pad_x * 2)
    chip_h = 17
    fill = t.ACCENT_BRIGHT if delta_pp > 0 else t.GREEN
    d.rounded_rectangle(
        [(x, y), (x + chip_w, y + chip_h)],
        radius=4,
        fill=t.BG,
        outline=fill,
        width=1,
    )
    d.text((x + pad_x, y + 1), text, font=chip_font, fill=fill)
    return chip_w


def _render_frame(
    label: str,
    pct: float,
    reset_text: str,
    phase: float,
    delta_pp: float | None,
) -> Image.Image:
    img = Image.new("RGB", (t.SIZE, t.SIZE), t.BG)
    d = ImageDraw.Draw(img)

    PAD = 16

    label_font = t.font_bold(16)
    reset_font = t.font(14)

    d.text((PAD, PAD), label, font=label_font, fill=t.TEXT)

    if delta_pp is not None and abs(delta_pp) >= 1:
        lw = d.textlength(label, font=label_font)
        _draw_delta_badge(d, PAD + int(lw) + 8, PAD - 1, delta_pp)

    if reset_text:
        rw = d.textlength(reset_text, font=reset_font)
        d.text(
            (t.SIZE - PAD - rw, PAD + 2),
            reset_text,
            font=reset_font,
            fill=t.TEXT_DIM,
        )

    d.line(
        [(PAD, PAD + 26), (t.SIZE - PAD, PAD + 26)],
        fill=t.HAIRLINE,
        width=1,
    )

    pct_int = int(round(pct))
    pct_text = f"{pct_int}"
    pct_font = t.font_bold(110)
    pct_w = d.textlength(pct_text, font=pct_font)

    suffix_font = t.font(28)
    suffix = "%"
    suffix_w = d.textlength(suffix, font=suffix_font)

    block_w = pct_w + 8 + suffix_w
    base_x = (t.SIZE - block_w) // 2
    pct_y = 64
    d.text((base_x, pct_y), pct_text, font=pct_font, fill=t.TEXT)
    d.text(
        (base_x + pct_w + 8, pct_y + 64),
        suffix,
        font=suffix_font,
        fill=t.TEXT_DIM,
    )

    bar_y = 204
    bar_h = 6
    bar_x0 = PAD
    bar_x1 = t.SIZE - PAD
    bar_w = bar_x1 - bar_x0
    d.rounded_rectangle(
        [(bar_x0, bar_y), (bar_x1, bar_y + bar_h)],
        radius=3,
        fill=t.HAIRLINE,
    )
    fill_w = max(3, int(bar_w * max(0.0, min(1.0, pct / 100.0))))
    d.rounded_rectangle(
        [(bar_x0, bar_y), (bar_x0 + fill_w, bar_y + bar_h)],
        radius=3,
        fill=t.ACCENT,
    )

    triangle = 1 - abs(2 * phase - 1)
    breath = t.ease_in_out(triangle)
    cap_r = 3.2 + 1.6 * breath
    cap_cx = bar_x0 + fill_w
    cap_cy = bar_y + bar_h // 2
    glow_r = cap_r + 1.5 * breath
    glow_color = t.blend(t.ACCENT_DIM, t.ACCENT_BRIGHT, breath)
    d.ellipse(
        [cap_cx - glow_r, cap_cy - glow_r, cap_cx + glow_r, cap_cy + glow_r],
        fill=glow_color,
    )
    d.ellipse(
        [cap_cx - cap_r, cap_cy - cap_r, cap_cx + cap_r, cap_cy + cap_r],
        fill=t.ACCENT_BRIGHT,
    )

    return img


def render(
    label: str,
    pct: float,
    reset_text: str,
    delta_pp: float | None = None,
) -> Image.Image:
    return _render_frame(label, pct, reset_text, 0.5, delta_pp)


def render_gif(
    out_path: Path,
    label: str,
    pct: float,
    reset_text: str,
    delta_pp: float | None = None,
    frames: int = 30,
    frame_ms: int = 80,
) -> Path:
    imgs = [
        _render_frame(label, pct, reset_text, i / frames, delta_pp).convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=32
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
