# Design System

The whole project is 240×240 pixels, four screens, dark canvas. The
design constraints are tight enough that every decision matters.

## Palette

```python
BG            "#0a0a0a"   pure-black canvas
SURFACE       "#141414"   slightly raised surface
HAIRLINE      "#262626"   dividers, bar tracks
MUTED         "#737373"   tertiary text
TEXT_DIM      "#a3a3a3"   secondary text
TEXT          "#fafafa"   primary text, hero numbers
ACCENT        "#cc785c"   Claude coral — single accent color
ACCENT_BRIGHT "#e89478"   highlighted state (active spoke, glow peak)
ACCENT_DIM    "#5a3528"   dim state (color-blend low end)
GREEN         "#4ade80"   positive delta (used less this period)
RED           "#ef4444"   error / over-budget (currently unused)
```

The whole palette is six gray-scale steps plus one accent and its two
modulations. No gradients, no neon. Read as Cloudflare-dashboard or
shadcn/ui, not as default-LLM purple-blue.

## Typography

Single typeface: **Cascadia Code** (mono). Used because:

- Monospace digits keep the hero number visually anchored when it
  changes (`9 → 12` doesn't shift the suffix `%`).
- The slight technical/dev-tool feel matches what the data represents.
- Ships with Windows 11; no font installation step.

Sizes used:

| Use | Size |
|---|---|
| Hero percentage | 110pt bold |
| Hero `$9,077` cost | 54pt bold |
| Section labels (`SESSION`, `ALL-TIME`) | 16pt bold |
| Big stat values (`56 days`) | 16pt bold |
| `%` suffix | 28pt regular |
| Reset time / inline meta | 14pt regular |
| Delta chip text | 11pt bold |
| Small stat labels (`AVG/D`) | 11pt regular |

## Animation philosophy

The hardest design problem in this project: how do you make a static
display **feel alive without becoming busy?**

The answer this project arrived at: **eased polyrhythms.**

### Eased instead of sin

Pure `sin(t)` motion has constant first-derivative at the zero crossings,
which means objects pass through the midpoint at maximum speed and feel
mechanical. Real breath, real blink, real heartbeat all spend more time
near the extremes than in transit.

```python
def ease_in_out(t):                   # cosine-eased — used for color blends
    return 0.5 - 0.5 * math.cos(t * math.pi)

def breath_eased(phase: float):       # smooth pulse 0..1..0 over the cycle
    triangle = 1 - abs(2 * phase - 1)
    return ease_in_out(triangle)
```

The triangle wave → `ease_in_out` composition gives "linger at the
peaks, accelerate through the middle, decelerate before the next peak."
Used for all the bar end-cap pulses and color shifts.

### Polyrhythms instead of lockstep

Every animated element on every screen has a slightly different period:

| Screen | Element | Period (× base 2.4s) |
|---|---|---|
| session/weekly | bar end-cap glow | 1.0× |
| alltime | token-line color | 1.0× |
| claude | center dot | 1.17× |
| claude | spoke ripple | 1.0× per spoke, offset by index/12 |
| claude | halo intensity | 0.7× |
| claude | glyph rotation | 1 full 30° drift per cycle |

Because no two elements complete their cycles at the same time, the
visual texture never repeats. Even though every individual element is
periodic, the **combination** doesn't loop visibly until the LCM of all
their periods — which is large enough that no glance catches it.

### Spoke ripple

The Claude glyph has 12 radial spokes. The naive approach is "all spokes
pulse together" — which reads as a robot LED. Instead each spoke `i` is
phase-offset by `i / 12`:

```python
for i in range(12):
    spoke_phase = (phase - i / 12) % 1.0
    weight = max(0, math.cos(2 * math.pi * spoke_phase)) ** 2
    # weight peaks for one spoke, dies off for neighbors,
    # creating a soft "wave" traveling around the ring
```

`max(0, cos)^2` gives a narrow peak that only "lights up" 2–3 spokes
at a time. Combined with the slow 30°-per-cycle base rotation, the
result is a barely-perceptible orbit of brightness around the ring.
Not a strobe, not a chase — a calm presence.

### Halo decoupled

The halo's breath period is **0.7× the glyph's**. This is the single
most important detail. If they had the same period the whole composition
would lock and feel canned. At 0.7× they desynchronize enough that any
particular alignment you see in one frame won't repeat in the next loop.

## Delta indicator

When usage moves between refreshes, a small chip appears next to the
section label:

- `+N` (going up) — outline + text in `ACCENT_BRIGHT`
- `-N` (going down — reset, etc.) — outline + text in `GREEN`
- absolute value < 1 → no chip (the number didn't actually move)

The chip is **outlined, not filled**, so it doesn't compete with the
hero number visually. It reads as annotation, not as primary data.

State persistence is in `.state/usage_last.json` — a single JSON file
with the previous `five_hour_pct` and `seven_day_pct`. On every render,
load → compute delta → render → overwrite. No history; just the
"vs. last time" comparison.

## Layout rhythm

Every screen uses 16px outer padding and the same vertical zones:

```
 y =  10..36   header (label left, meta right, hairline underneath)
 y =  60..160  hero zone (big number, big text, or glyph)
 y = 160..230  secondary zone (bar, stat grid, tagline)
```

Even though the four screens have different content density, they read
as a series because the eye lands in the same place every time.

## Why monospace digits matter at 240×240

The Claude `%` symbol sits to the right of the integer. When the value
jumps from a single-digit to a double-digit number, in a proportional
font the `%` would slide noticeably to the right and back. In Cascadia
Code, each digit occupies the same advance width, so a 6 → 7 → 11
sequence keeps the `%` perfectly still. The motion in the screen is
intentional motion (the animation), not jitter from text layout.
