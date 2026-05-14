"""Anthropic OAuth usage endpoint client.

Reverse-engineered from the Claude Code VS Code extension (extension.js, ~line 282).
Endpoint: GET https://api.anthropic.com/api/oauth/usage
Auth:     Bearer token from ~/.claude/.credentials.json
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path


CREDENTIALS_PATH = Path(os.environ["USERPROFILE"]) / ".claude" / ".credentials.json"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"


@dataclass
class Bucket:
    utilization: float  # 0..100
    resets_at: dt.datetime | None

    @property
    def seconds_until_reset(self) -> int | None:
        if self.resets_at is None:
            return None
        now = dt.datetime.now(dt.timezone.utc)
        return max(0, int((self.resets_at - now).total_seconds()))


@dataclass
class Usage:
    five_hour: Bucket | None
    seven_day: Bucket | None
    seven_day_sonnet: Bucket | None
    raw: dict


def _load_token() -> str:
    with CREDENTIALS_PATH.open("r", encoding="utf-8") as f:
        creds = json.load(f)
    inner = creds.get("claudeAiOauth") or creds
    token = inner.get("accessToken")
    if not token:
        raise RuntimeError("no accessToken in credentials file")
    return token


def _parse_bucket(raw: dict | None) -> Bucket | None:
    if not raw or raw.get("utilization") is None:
        return None
    util = float(raw["utilization"])
    resets_iso = raw.get("resets_at")
    resets = None
    if resets_iso:
        resets = dt.datetime.fromisoformat(resets_iso.replace("Z", "+00:00"))
    return Bucket(utilization=util, resets_at=resets)


def fetch() -> Usage:
    token = _load_token()
    req = urllib.request.Request(
        USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = json.loads(r.read().decode("utf-8"))
    return Usage(
        five_hour=_parse_bucket(raw.get("five_hour")),
        seven_day=_parse_bucket(raw.get("seven_day")),
        seven_day_sonnet=_parse_bucket(raw.get("seven_day_sonnet")),
        raw=raw,
    )


if __name__ == "__main__":
    u = fetch()
    print(f"5h:  {u.five_hour}")
    print(f"7d:  {u.seven_day}")
    print(f"7ds: {u.seven_day_sonnet}")
