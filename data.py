"""ccusage wrapper — runs `npx ccusage` and normalizes the JSON."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from dataclasses import dataclass


def _ccusage(*args: str) -> dict:
    cmd = ["npx", "--yes", "ccusage@latest", *args, "--json", "--offline"]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"ccusage failed: {res.stderr}")
    return json.loads(res.stdout)


@dataclass
class ActiveBlock:
    cost: float
    tokens: int
    entries: int
    elapsed_seconds: int
    total_seconds: int
    model: str
    burn_per_hour: float
    projected_cost: float
    percent_used: float

    @property
    def remaining_seconds(self) -> int:
        return max(0, self.total_seconds - self.elapsed_seconds)

    @property
    def time_progress(self) -> float:
        if self.total_seconds <= 0:
            return 0.0
        return min(1.0, self.elapsed_seconds / self.total_seconds)


@dataclass
class WeekBlock:
    label: str
    cost: float
    tokens: int
    days: list[float]
    top_model: str


@dataclass
class AllTime:
    cost: float
    tokens: int
    weeks: int
    active_days: int
    top_model: str


def active_session() -> ActiveBlock | None:
    data = _ccusage("blocks", "--active", "--token-limit", "max")
    blocks = data.get("blocks", [])
    if not blocks:
        return None
    b = blocks[0]
    start = dt.datetime.fromisoformat(b["startTime"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    elapsed = int((now - start).total_seconds())
    total = 5 * 3600
    burn_per_hour = b.get("burnRate", {}).get("costPerHour", 0.0) or 0.0
    proj = b.get("projection", {}).get("totalCost", b["costUSD"]) or b["costUSD"]
    pct = b.get("tokenLimitStatus", {}).get("percentUsed", 0.0) or 0.0
    return ActiveBlock(
        cost=b["costUSD"],
        tokens=b["totalTokens"],
        entries=b["entries"],
        elapsed_seconds=elapsed,
        total_seconds=total,
        model=(b["models"][0] if b["models"] else "claude"),
        burn_per_hour=burn_per_hour,
        projected_cost=proj,
        percent_used=pct,
    )


def _model_short(name: str) -> str:
    n = name.replace("claude-", "")
    for suf in ("-20251001", "-20250929"):
        n = n.replace(suf, "")
    return n


def current_week() -> WeekBlock:
    data = _ccusage("weekly")
    weeks = data.get("weekly", [])
    if not weeks:
        return WeekBlock("WEEK", 0.0, 0, [0] * 7, "claude")
    w = weeks[-1]
    daily = _ccusage("daily", "--since", w["week"].replace("-", ""))
    daily_items = daily.get("daily", [])
    week_start = dt.date.fromisoformat(w["week"])
    days: list[float] = [0.0] * 7
    for item in daily_items:
        d = dt.date.fromisoformat(item["date"])
        idx = (d - week_start).days
        if 0 <= idx < 7:
            days[idx] = item.get("totalCost", 0.0)
    top = max(w["modelBreakdowns"], key=lambda m: m["cost"])
    return WeekBlock(
        label=f"W{week_start.isocalendar().week:02d}",
        cost=w["totalCost"],
        tokens=w["totalTokens"],
        days=days,
        top_model=_model_short(top["modelName"]),
    )


def all_time() -> AllTime:
    data = _ccusage("weekly")
    weeks = data.get("weekly", [])
    if not weeks:
        return AllTime(0.0, 0, 0, 0, "claude")
    total_cost = sum(w["totalCost"] for w in weeks)
    total_tok = sum(w["totalTokens"] for w in weeks)
    daily = _ccusage("daily").get("daily", [])
    active_days = len(daily)
    model_totals: dict[str, float] = {}
    for w in weeks:
        for m in w["modelBreakdowns"]:
            model_totals[m["modelName"]] = model_totals.get(m["modelName"], 0) + m["cost"]
    top = max(model_totals.items(), key=lambda kv: kv[1])[0] if model_totals else "claude"
    return AllTime(
        cost=total_cost,
        tokens=total_tok,
        weeks=len(weeks),
        active_days=active_days,
        top_model=_model_short(top),
    )
