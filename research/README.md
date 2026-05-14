# Research notes

How the pieces of this project were figured out. Useful if you want to
extend the dashboard to other Anthropic usage buckets, port it to a
different display, or just understand the provenance.

## Files in this folder

### `stock_firmware_ui/`

A snapshot of every HTML/CSS/JS page served by the GeekMagic
SmallTV-Ultra's own web interface, fetched directly from the device at
its LAN address (`http://<DEVICE_IP>/<page>.html`).

| Page | Purpose |
|---|---|
| `index.html` | Theme picker + brightness + factory reset + firmware update entry |
| `image.html` | Photo Album upload UI — this is the one that reveals `POST /doUpload?dir=...` |
| `network.html` | WiFi setup |
| `settings.html` | Same content as `index.html` (just routed twice) |
| `time.html`, `weather.html`, `update.html` | Theme-specific config pages |
| `js/settings.js` | The shared frontend script. Reading this is faster than running mitmproxy — every `/set?...` query and `/*.json` endpoint name is right in the source. |
| `css/style.css` | The device's stylesheet (not used by us, but kept for completeness) |

I downloaded all of these with a few `curl http://192.168.178.90/<page>.html`
calls. Treat it as a frozen reference; nothing in the project imports
from this folder.

The reverse-engineered API surface is documented in
[`../docs/DEVICE_API.md`](../docs/DEVICE_API.md).

## Finding the Anthropic `/api/oauth/usage` endpoint

The Claude Code VS Code extension renders an "Account & Usage" panel
showing your 5-hour and 7-day percentages. That data has to be coming
over the wire from somewhere — the question was just *where*.

### The hunt

The extension lives at:
```
~/.vscode/extensions/anthropic.claude-code-<version>-<platform>/
├── extension.js       # 882 lines, minified-ish but not fully obfuscated
├── webview/
│   ├── index.js       # ~2000 lines, the React UI
│   └── index.css
├── resources/
│   └── native-binary/
│       └── claude.exe # ~228MB, the actual Claude Code CLI bundled in
└── package.json
```

`extension.js` is the host-side bridge that the webview talks to. If
the panel data is fetched from a network endpoint, the fetch call has
to be in `extension.js` (the webview doesn't have direct network access
— it goes through the host).

```bash
grep -oE 'https?://[a-zA-Z0-9./_-]+' extension.js | sort -u
# ... reveals:
#   https://api.anthropic.com
#   https://platform.claude.com/oauth/...
#   https://api.anthropic.com/api/oauth/claude_cli/...
# ... and lots more
```

```bash
grep -oE '"/(v1|api|usage|account)[a-zA-Z0-9_/.-]*"' extension.js | sort -u
# ... reveals:
#   /api/oauth/usage           ← match
#   /api/oauth/claude_cli/...
#   /api/organizations/
#   /v1/messages
#   /v1/oauth/token
```

There it is: `/api/oauth/usage`. Reading the surrounding ~50 lines gave:

```js
// approximately reproduced from extension.js minified output
async function B30(z, K) {
  if (z.getAuthStatus()?.authMethod !== "claudeai") return;
  const headers = await z.getAuthHeaders();
  const url = `${BASE_API_URL}/api/oauth/usage`;
  const resp = await axios.get(url, {
    headers: { "Content-Type": "application/json", ...headers },
    timeout: 5000,
  });
  return parseUsage(resp.data);
}

function parseUsage(z) {
  const out = {};
  if (z.five_hour?.utilization != null) out.fiveHour = {
    utilization: z.five_hour.utilization,
    resetsAt:    z.five_hour.resets_at,
  };
  if (z.seven_day?.utilization != null) out.sevenDay = { ... };
  if (z.seven_day_sonnet?.utilization != null) out.sevenDaySonnet = { ... };
  if (z.extra_usage) out.extraUsage = {
    isEnabled:    z.extra_usage.is_enabled,
    monthlyLimit: z.extra_usage.monthly_limit,
    usedCredits:  z.extra_usage.used_credits,
    utilization:  z.extra_usage.utilization,
  };
  return out;
}
```

The auth headers come from `authManager.getAuthHeaders()`, which is the
extension's wrapper around the OAuth token persisted in
`~/.claude/.credentials.json`.

### Verifying it lives

Once the endpoint is known, you can curl it directly:

```bash
TOKEN=$(python -c "
import json, os
p = os.path.expanduser('~/.claude/.credentials.json')
d = json.load(open(p))
print(d.get('claudeAiOauth', d)['accessToken'])
")

curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  https://api.anthropic.com/api/oauth/usage | python -m json.tool
```

That should return a JSON object with `five_hour`, `seven_day`, etc.
The schema is documented in [`../docs/ANTHROPIC_API.md`](../docs/ANTHROPIC_API.md).

### Why this is safe-ish

The endpoint is not advertised publicly, but it's also not a secret —
it's served by your authenticated session and it returns only your own
usage data. Anthropic could rate-limit or rename it at any time. We
poll it once every 2 minutes, which is well below any reasonable rate
ceiling.

This project does not:

- Send your token anywhere except api.anthropic.com
- Cache server responses beyond the in-memory render cycle
- Refresh the token automatically (if it expires, you re-run
  `claude login` and the credentials file is updated for you)

## Hardware datapoints

For reference (not used directly by the code):

| | |
|---|---|
| Chipset | ESP32 variant (exact part not confirmed; no UART exposed externally) |
| Display | 240×240 IPS, square. Driver is likely ST7789. |
| Flash | ~3 MB user filesystem, ~700 KB–1 MB free after a stock install. |
| Network | 2.4 GHz Wi-Fi only |
| Power | USB-C, 5V |
| Web server | The stock firmware embeds a custom HTTP server. Headers are non-standard (see `device.py` for the dup-`Content-Length` quirk). |

If you ever flash custom firmware on this device, you almost certainly
want UART recovery wired up first. The stock OTA endpoint at `/update`
is exposed but it doesn't verify the image — a wrong binary will brick
you.
