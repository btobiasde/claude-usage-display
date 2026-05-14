"""GeekMagic SmallTV-Ultra HTTP API client.

Reverse-engineered surface — full reference in docs/DEVICE_API.md.

Uses curl as subprocess for uploads because the stock firmware emits
two Content-Length headers on /doUpload responses, which Python's
urllib3 strict parser rejects.
"""
from __future__ import annotations

import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import config


def _get(path: str) -> str:
    url = f"http://{config.DEVICE_IP}{path}"
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read().decode("utf-8", errors="replace")


def upload(local_path: Path, remote_dir: str = "/image") -> None:
    """POST a file to /doUpload via curl (handles the dup-header bug).

    The file's mime type doesn't actually matter to the device — it
    inspects the extension. We send image/jpeg for everything; the
    device will still accept and store .gif files correctly.
    """
    url = f"http://{config.DEVICE_IP}/doUpload?dir={remote_dir}"
    res = subprocess.run(
        [
            "curl", "-s", "-m", "30",
            "-F", f"file=@{local_path};type=image/jpeg",
            url,
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"upload failed: {res.stderr}")


def set_image(remote_path: str) -> None:
    """Display a specific file immediately (overrides autoplay rotation
    until autoplay is re-enabled or another /set?img= call is made)."""
    q = urllib.parse.quote(remote_path)
    r = _get(f"/set?img={q}")
    if r.strip() != "OK":
        raise RuntimeError(f"set_image failed: {r!r}")


def set_theme(n: int) -> None:
    """Switch active theme. 3 = Photo Album (what we use)."""
    r = _get(f"/set?theme={n}")
    if r.strip() != "OK":
        raise RuntimeError(f"set_theme failed: {r!r}")


def clear_images() -> None:
    """Delete every file under /image/. Side effect: resets autoplay to 0."""
    _get("/set?clear=image")


def delete_file(remote_path: str) -> None:
    """Delete a single file under /image/. The device replies "Fail"
    even on success — verify via filelist if you need certainty."""
    q = urllib.parse.quote(remote_path)
    _get(f"/delete?file={q}")
