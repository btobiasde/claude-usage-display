"""Screen: All-time cumulative stats with eased accent shimmer."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import theme as t


def _fmt_money(usd: float) -> str:
    if usd >= 1000:
        return f"${usd:,.0f}"
    return f"${usd:,.2f}"


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _render_frame(
    total_cost: float,
    total_tokens: int,
    weeks: int,
    active_days: int,
    phase: float,
) -> Image.Image:
    img = Image.new("RGB", (t.SIZE, t.SIZE), t.BG)
    d = ImageDraw.Draw(img)

    PAD = 16

    label_font = t.font_bold(16)
    d.text((PAD, PAD), "ALL-TIME", font=label_font, fill=t.TEXT)

    d.line(
        [(PAD, PAD + 26), (t.SIZE - PAD, PAD + 26)],
        fill=t.HAIRLINE,
        width=1,
    )

    cost_text = _fmt_money(total_cost)
    cost_font = t.font_bold(54)
    cw = d.textlength(cost_text, font=cost_font)
    d.text(
        ((t.SIZE - cw) // 2, 60),
        cost_text,
        font=cost_font,
        fill=t.TEXT,
    )

    # Token accent text breathes with cubic easing so it lingers
    # at each extreme rather than running through them linearly.
    triangle = 1 - abs(2 * phase - 1)
    breath = t.ease_in_out(triangle)
    token_color = t.blend(t.ACCENT_DIM, t.ACCENT_BRIGHT, breath)
    tokens_text = _fmt_tokens(total_tokens) + " TOKENS"
    tokens_font = t.font_bold(16)
    tw = d.textlength(tokens_text, font=tokens_font)
    d.text(
        ((t.SIZE - tw) // 2, 124),
        tokens_text,
        font=tokens_font,
        fill=token_color,
    )

    d.line(
        [(40, 158), (t.SIZE - 40, 158)],
        fill=t.HAIRLINE,
        width=1,
    )

    daily_avg = total_cost / max(1, active_days)
    stats_font_label = t.font(11)
    stats_font_val = t.font_bold(16)

    cell_w = (t.SIZE - PAD * 2) // 3
    cells = [
        ("WEEKS", str(weeks)),
        ("DAYS", str(active_days)),
        ("AVG/D", _fmt_money(daily_avg)),
    ]
    for i, (label, value) in enumerate(cells):
        cx = PAD + i * cell_w + cell_w // 2
        lw = d.textlength(label, font=stats_font_label)
        vw = d.textlength(value, font=stats_font_val)
        d.text((cx - vw // 2, 174), value, font=stats_font_val, fill=t.TEXT)
        d.text((cx - lw // 2, 200), label, font=stats_font_label, fill=t.TEXT_DIM)

    return img


def render(
    total_cost: float, total_tokens: int, weeks: int, active_days: int
) -> Image.Image:
    return _render_frame(total_cost, total_tokens, weeks, active_days, 0.25)


def render_gif(
    out_path: Path,
    total_cost: float,
    total_tokens: int,
    weeks: int,
    active_days: int,
    frames: int = 30,
    frame_ms: int = 80,
) -> Path:
    imgs = [
        _render_frame(total_cost, total_tokens, weeks, active_days, i / frames).convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=48
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
