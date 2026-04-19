---
name: zoom
description: "Zoom meetings, webinars, users, registrants, and participants — via Zoom REST API with Server-to-Server OAuth."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [Zoom, Meetings, Webinars, Registrants, Participants, Video, API]
---

# Zoom API

Zoom REST API access for meetings, webinars, users, registrants, and participants.

## Prerequisites

- Zoom Server-to-Server OAuth app (one-time setup, ~5 minutes)

## Setup

### Step 1: Create Zoom Server-to-Server OAuth app

1. Go to: https://marketplace.zoom.us/develop/create
2. Choose: **"Server-to-Server OAuth"**
3. Name it (e.g. "Hermes Integration") and click **Create**
4. Under **Scopes**, add these (minimum):
   - `meeting:read:list_meetings`
   - `meeting:read:meeting`
   - `meeting:read:list_meeting_registrants`
   - `report:read:list_meeting_participants`
   - `user:read:user`
   - `user:read:list_users`
   - `webinar:read:list_webinars`
   - `webinar:read:list_webinar_registrants`
5. Go to **Activation** and click **Activate**
6. Note down: **Account ID**, **Client ID**, **Client Secret**

### Step 2: Store credentials

Save to a JSON file:
```json
{
  "account_id": "YOUR_ACCOUNT_ID",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
```

Then run:
```bash
ZSETUP="python3 ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/zoom/scripts/setup.py"
$ZSETUP --set-credentials --file /path/to/credentials.json
```

### Step 3: Verify

```bash
$ZSETUP --check
```

Should print `AUTHENTICATED: email@example.com`.

## Usage

Set shorthand:
```bash
ZAPI="python3 ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/zoom/scripts/zoom_api.py"
```

### Meetings

```bash
# List upcoming/scheduled/live meetings
$ZAPI meetings list --type upcoming
$ZAPI meetings list --type scheduled

# Get meeting details
$ZAPI meetings get 123456789

# List meeting registrants
$ZAPI meetings registrants 123456789
$ZAPI meetings registrants 123456789 --status approved
$ZAPI meetings registrants 123456789 --status pending

# List past meeting participants (who actually attended)
$ZAPI meetings participants 123456789
```

### Users

```bash
$ZAPI users list
$ZAPI users get
$ZAPI users get --user-id someone@company.com
```

### Webinars

```bash
$ZAPI webinars list
$ZAPI webinars registrants 987654321
```

### Raw API (any endpoint)

```bash
# Any Zoom API endpoint directly
$ZAPI raw "/v2/users/me/settings"
$ZAPI raw "/v2/meetings/123456789" --method PATCH --body '{"topic": "New Title"}'
```

### Pagination

Add `--page-all` to any list endpoint to get all results as NDJSON:
```bash
$ZAPI --page-all meetings registrants 123456789
$ZAPI --page-all meetings participants 123456789
```

## Output Format

All commands return JSON.

- `meetings list`: `{meetings: [...], next_page_token, page_count, ...}`
- `meetings registrants`: `{registrants: [{id, email, first_name, last_name, status, ...}], ...}`
- `meetings participants`: `{participants: [{id, name, user_email, join_time, leave_time, duration, ...}], ...}`
- `raw`: Full API response

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run `setup.py --check` or re-add credentials |
| `401 Unauthorized` | Token expired — it auto-refreshes. Check credentials if persistent |
| `403 Forbidden` | Missing scope — add required scopes in Zoom Marketplace app settings |
| `4711 scope error on --check` | `user:read:user` scope not configured. Check still passes (falls back to meetings endpoint). Add scope in Zoom Marketplace for user info access |
| `400 Bad Request` | Check API parameters, meeting ID exists, user has permission |

## Revoking

```bash
ZSETUP="python3 ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/zoom/scripts/setup.py"
$ZSETUP --revoke
```
