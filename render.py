"""Render 4 animated dashboard GIFs with delta tracking.

Order on device rotation:
  1. session.gif   - 5h limit %, end-cap pulse + delta badge
  2. weekly.gif    - 7d limit %, end-cap pulse + delta badge
  3. alltime.gif   - cost + stats, eased token shimmer
  4. claude.gif    - plan info, rippling spokes + decoupled halo
"""
from __future__ import annotations

from pathlib import Path

import config
import data
import state
import usage_api
from src.screens import alltime as alltime_s
from src.screens import claude_info
from src.screens import session as session_s
from src.screens import weekly as weekly_s


def render_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    u = usage_api.fetch()
    a = data.all_time()

    five_pct = u.five_hour.utilization if u.five_hour else None
    seven_pct = u.seven_day.utilization if u.seven_day else None

    previous = state.load()
    if previous is not None:
        d_five = state.delta(five_pct, previous.five_hour_pct)
        d_seven = state.delta(seven_pct, previous.seven_day_pct)
    else:
        d_five = None
        d_seven = None

    paths: list[Path] = []

    paths.append(
        session_s.render_gif(
            out_dir / "session.gif",
            pct=five_pct or 0.0,
            reset_seconds=u.five_hour.seconds_until_reset if u.five_hour else None,
            delta_pp=d_five,
        )
    )
    paths.append(
        weekly_s.render_gif(
            out_dir / "weekly.gif",
            pct=seven_pct or 0.0,
            resets_at=u.seven_day.resets_at if u.seven_day else None,
            delta_pp=d_seven,
        )
    )
    paths.append(
        alltime_s.render_gif(
            out_dir / "alltime.gif",
            total_cost=a.cost,
            total_tokens=a.tokens,
            weeks=a.weeks,
            active_days=a.active_days,
        )
    )
    paths.append(
        claude_info.render_gif(
            out_dir / "claude.gif",
            model="OPUS 4.7",
            context="1M CONTEXT",
        )
    )

    state.save(five_pct, seven_pct)
    return paths


if __name__ == "__main__":
    paths = render_all(Path(config.OUT_DIR))
    for p in paths:
        print(p, p.stat().st_size, "bytes")
