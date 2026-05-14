# Anthropic `/api/oauth/usage` — reverse-engineered

This is the endpoint that powers the **Account & Usage** panel in
claude.ai's settings and in the Claude Code VS Code extension. It is
**not** the documented public API (`docs.anthropic.com`); it sits on
`api.anthropic.com` but under the `/api/` prefix used by claude.ai's
own frontend.

The endpoint is **undocumented**. Anthropic may change it without notice.
This project depends on it; if it changes, you'll need to grep the
extension again.

## Endpoint

```
GET https://api.anthropic.com/api/oauth/usage

Headers:
  Authorization:     Bearer <oauth_access_token>
  Content-Type:      application/json
  anthropic-version: 2023-06-01
```

## Auth: where the token comes from

Claude Code stores its OAuth credentials at:

| Platform | Path |
|---|---|
| Windows | `%USERPROFILE%\.claude\.credentials.json` |
| macOS / Linux | `~/.claude/.credentials.json` |

Shape:

```json
{
  "claudeAiOauth": {
    "accessToken":  "sk-ant-...",
    "refreshToken": "...",
    "expiresAt":    1778790244045,
    "scopes": [
      "user:file_upload",
      "user:inference",
      "user:mcp_servers",
      "user:profile",
      "user:sessions:claude_code"
    ],
    "subscriptionType": "max",
    "rateLimitTier":    "default_claude_max_20x"
  }
}
```

Some installations put the same fields at top-level rather than under
`claudeAiOauth`. The reader in [`usage_api.py`](../usage_api.py) handles
both shapes.

`subscriptionType` and `rateLimitTier` are also what the Claude screen
uses to render `OPUS 4.7 / MAX 20X`.

## Response

```json
{
  "five_hour": {
    "utilization": 12.0,
    "resets_at":   "2026-05-14T19:40:00.324257+00:00"
  },
  "seven_day": {
    "utilization": 2.0,
    "resets_at":   "2026-05-21T16:00:01.324285+00:00"
  },
  "seven_day_sonnet":     { "utilization": 0.0, "resets_at": null },
  "seven_day_opus":       null,
  "seven_day_oauth_apps": null,
  "seven_day_cowork":     null,
  "seven_day_omelette":   { "utilization": 0.0, "resets_at": null },
  "tangelo":              null,
  "iguana_necktie":       null,
  "omelette_promotional": null,
  "extra_usage": {
    "is_enabled":      false,
    "monthly_limit":   null,
    "used_credits":    null,
    "utilization":     null,
    "currency":        null,
    "disabled_reason": "org_level_disabled_until"
  }
}
```

### Bucket schema

Every non-null usage bucket is:
```ts
{ utilization: number, resets_at: ISO-8601 | null }
```
`utilization` is a percentage 0–100 against the bucket's enforced limit.

### What each bucket means

| Field | Meaning |
|---|---|
| `five_hour` | The 5-hour rolling block. Resets at the time shown. This is what the claude.ai UI calls "Aktuelle Sitzung". |
| `seven_day` | All-models 7-day rolling quota. claude.ai labels this "Wöchentlich → Alle Modelle". |
| `seven_day_sonnet` | Sonnet-specific 7-day sub-quota. |
| `seven_day_opus` | Opus-specific. Often `null` if you don't have a separate Opus bucket. |
| `seven_day_oauth_apps` | API requests via OAuth-issued keys (e.g. Claude Code-as-a-server scenarios). |
| `seven_day_cowork`, `seven_day_omelette` | Internal/experimental buckets — both currently exposed but typically `null` or `0`. |
| `tangelo`, `iguana_necktie`, `omelette_promotional` | Promotional / feature-flag buckets. Probably codenames. Currently null for most accounts. |
| `extra_usage` | Pay-as-you-go credit pool when enabled. `disabled_reason: "org_level_disabled_until"` means the org has not opted in. |

## How this was found

1. The Claude VS Code extension is installed at
   `~/.vscode/extensions/anthropic.claude-code-*/extension.js`.
2. The "Account & Usage" panel renders into a webview, so the data has
   to come through `extension.js` first. A grep for URL fragments turned
   up `/api/oauth/usage` on line ~282.
3. The surrounding function reveals the headers, the auth source
   (`authManager.getAuthHeaders()`), and the response parser (which
   filters to `five_hour`, `seven_day`, `seven_day_sonnet`, `extra_usage`).

The full grep + function are reproduced in
[`research/README.md`](../research/README.md).

## Implementation notes

The `usage_api.py` client is intentionally tiny — only stdlib
(`urllib.request`, `json`, `datetime`). No `requests` dependency.

```python
from usage_api import fetch

u = fetch()
print(u.five_hour.utilization)              # 12.0
print(u.five_hour.seconds_until_reset)      # 1768
print(u.seven_day.resets_at)                # datetime in UTC
```

The OAuth token is checked for expiry only by the Anthropic server. If
the token is expired, the request fails with 401; you'll need to
re-authenticate via `claude login` to refresh it. This client does **not**
implement the refresh-token flow.

## Stability

This is an undocumented, internal endpoint. Realistic risks:

- Anthropic could change the URL, header set, or response shape at any
  point. If your screens go blank, grep the current
  `~/.vscode/extensions/anthropic.claude-code-*/extension.js` for
  `/api/oauth/usage` (or whatever it's been renamed to).
- The bucket names (especially `iguana_necktie`, `omelette_promotional`)
  are clearly experimental — they may come, go, or be renamed.
- The endpoint may eventually require a different scope or product surface.

We use only the stable-feeling fields (`five_hour`, `seven_day`,
`seven_day_sonnet`) plus `rateLimitTier` from the credentials file —
those are the same surface that powers claude.ai's own settings UI, so
they're as load-bearing as it gets.
