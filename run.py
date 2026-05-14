"""Live loop: render → upload → let the device's Photo Album rotation
play the four animated GIFs natively.

We do NOT drive rotation from the PC — the device cycles through the
images in /image/ by itself every SCREEN_ROTATE_SECONDS, which also
lets each GIF's frame-level animation play without being interrupted.

The Python loop only re-renders + re-uploads every DATA_REFRESH_SECONDS
so the percentages stay current.

Run:   python run.py
Stop:  Ctrl+C
"""
from __future__ import annotations

import sys
import time
import traceback
import urllib.request
from pathlib import Path

import config
import device
import render


SCREEN_FILES = ["session.gif", "weekly.gif", "alltime.gif", "claude.gif"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def refresh_and_upload() -> None:
    log("rendering 4 screens...")
    paths = render.render_all(Path(config.OUT_DIR))
    for p in paths:
        log(f"upload  {p.name:<14} {p.stat().st_size:>6}b")
        device.upload(p, config.REMOTE_DIR)


def enable_autoplay() -> None:
    log("theme=3 (Photo Album), autoplay on, interval=%ds" % config.SCREEN_ROTATE_SECONDS)
    device.set_theme(3)
    url = (
        f"http://{config.DEVICE_IP}/set?"
        f"i_i={config.SCREEN_ROTATE_SECONDS}&autoplay=1"
    )
    urllib.request.urlopen(url, timeout=10).read()


def main() -> int:
    log("starting claude dashboard")
    try:
        refresh_and_upload()
        enable_autoplay()
    except Exception:
        log("initial setup failed:")
        traceback.print_exc()
        return 1

    log(f"refresh cadence: every {config.DATA_REFRESH_SECONDS}s")
    try:
        while True:
            time.sleep(config.DATA_REFRESH_SECONDS)
            try:
                refresh_and_upload()
                # Re-issue autoplay because some firmware operations
                # reset it (notably /set?clear=image).
                enable_autoplay()
            except Exception:
                log("refresh failed:")
                traceback.print_exc()
    except KeyboardInterrupt:
        log("stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
