# GeekMagic SmallTV-Ultra HTTP API

Reference for the stock-firmware HTTP API as observed on
**Smalltv-Ultra Ultra-V9.0.21**. The device exposes a small unauthenticated
HTTP server on port 80 of its LAN IP.

> ⚠ Everything is unauthenticated. Treat the device as untrusted: keep it
> on a trusted LAN, never port-forward.

## Read endpoints

All read endpoints return JSON or HTML. Method is `GET`.

### `/v.json`
Model and firmware version.
```json
{"m": "Smalltv-Ultra", "v": "Ultra-V9.0.21"}
```

### `/app.json`
Currently active theme (1–7).
```json
{"theme": 3}
```

### `/album.json`
Photo Album rotation settings.
```json
{"autoplay": 1, "i_i": 8}
```
`i_i` is the rotation interval in seconds.

### `/space.json`
Filesystem usage (bytes).
```json
{"total": 3121152, "free": 1056268}
```

### `/brt.json`
Display brightness 0–255.
```json
{"brt": "147"}
```

### `/theme_list.json`
Auto-switch configuration (cycling through multiple themes).
```json
{"list": "0,0,0,0,0,0,0", "sw_en": "0", "sw_i": "30"}
```

### `/filelist?dir=<path>`
**Returns HTML**, not JSON. A table listing files in the given directory.
Pass `/image` for Photo Album content.

## Write endpoints (the `/set` family)

All of these are `GET` with query params and return `"OK"` on success
(plain text, no JSON wrapper).

| Query | Effect |
|---|---|
| `/set?theme=N` | Switch to theme N (1–7). `3 = Photo Album`. |
| `/set?img=/image/foo.jpg` | Immediately display this image (overrides rotation). |
| `/set?i_i=8&autoplay=1` | Set Photo Album rotation interval + enable autoplay. |
| `/set?theme_list=a,b,...&sw_en=1&theme_interval=30` | Configure inter-theme auto-switch. |
| `/set?brt=N` | Set brightness (0–255). |
| `/set?t1=H&t2=H&b1=N&b2=N&en=1` | Night-mode (dim between hours). |
| `/set?reset=1` | Factory reset (keeps `/image/` files). |
| `/set?reboot=1` | Reboot. |
| `/set?clear=image` | Delete every file under `/image/`. |

### Theme IDs
```
1  Weather Clock Today
2  Weather Forecast
3  Photo Album            ← what we use; cycles JPG/GIF files
4  Time Style 1
5  Time Style 2
6  Time Style 3
7  Simple Weather Clock
```

## File upload

### `POST /doUpload?dir=<path>`

`multipart/form-data` with a `file` field. Accepts JPG and GIF. Path is
the destination directory (`/image` for Photo Album).

**Quirk:** the response sends **two** `Content-Length` headers, which
Python's `urllib3` parser rejects. That's why
[`device.py`](../device.py) shells out to `curl` for uploads instead of
using `requests` or `urllib`.

```bash
curl -F 'file=@my.gif;type=image/gif' \
     'http://192.168.178.90/doUpload?dir=/image'
```

### `GET /delete?file=<url-encoded-path>`

Delete a single file. The response body is `"Fail"` even on success —
the file is actually deleted, the response just lies. Verify via
`/filelist?dir=<path>` after.

```bash
curl 'http://192.168.178.90/delete?file=%2Fimage%2Fold.jpg'
```

### `POST /update`

Firmware update via uploaded `.bin` / `.bin.gz`. **Bricks the device if
you upload the wrong file.** Don't touch unless you have UART recovery.

## Observed quirks

- `/set?clear=image` resets `autoplay` back to `0`. Always re-issue
  `/set?i_i=N&autoplay=1` after clearing.
- The HTML in `/filelist` references icon resources that don't exist —
  ignore those, parse the `<a>` text.
- The 240×240 display is **square**, not round, despite the round-display
  resolution being identical (some SmallTV variants ship with GC9A01
  round panels — Ultra is ST7789-ish square).
- Storage is ~3 MB total. Mind the GIF sizes; a single 240×240 GIF with
  48 frames at 64 colors is ~140 KB.

## Reference: stock firmware webUI

A snapshot of the device's own web UI is preserved under
[`research/stock_firmware_ui/`](../research/stock_firmware_ui/) — handy
when you want to look up what a particular `/set?...` query does and
where you'd toggle it from the device's own pages.
