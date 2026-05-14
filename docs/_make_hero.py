"""One-shot helper: composes the 4 screens into a 2x2 hero image for the README.

Run from project root:
    python docs/_make_hero.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent
SCREEN_SIZE = 240
GAP = 24
PAD = 32
BG = (10, 10, 10)

screens = ["session.gif", "weekly.gif", "alltime.gif", "claude.gif"]

frames = [
    Image.open(PROJECT / "docs" / "screenshots" / name).convert("RGB")
    for name in screens
]

W = PAD * 2 + SCREEN_SIZE * 2 + GAP
H = PAD * 2 + SCREEN_SIZE * 2 + GAP
canvas = Image.new("RGB", (W, H), BG)

positions = [
    (PAD, PAD),
    (PAD + SCREEN_SIZE + GAP, PAD),
    (PAD, PAD + SCREEN_SIZE + GAP),
    (PAD + SCREEN_SIZE + GAP, PAD + SCREEN_SIZE + GAP),
]
for f, p in zip(frames, positions):
    canvas.paste(f, p)

out = PROJECT / "docs" / "screenshots" / "hero.png"
canvas.save(out, format="PNG", optimize=True)
print(f"saved {out}  ({out.stat().st_size}b)")
