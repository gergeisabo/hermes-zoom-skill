# hermes-zoom-skill

Zoom REST API skill for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

## Features

- List meetings (upcoming, scheduled, live)
- Get meeting details
- List meeting registrants with custom questions
- List past meeting participants (attendance reports)
- List users and webinars
- Raw API passthrough for any Zoom endpoint
- Auto-pagination (NDJSON output)
- Automatic token refresh (Server-to-Server OAuth)

## Prerequisites

- Python 3.10+
- Zoom Server-to-Server OAuth app

## Quick Start

### 1. Create Zoom Server-to-Server OAuth app

1. Go to: https://marketplace.zoom.us/develop/create
2. Choose: **"Server-to-Server OAuth"**
3. Add scopes:
   - `meeting:read:list_meetings`
   - `meeting:read:meeting`
   - `meeting:read:list_meeting_registrants`
   - `report:read:list_meeting_participants`
   - `user:read:user`
   - `user:read:list_users`
   - `webinar:read:list_webinars`
   - `webinar:read:list_webinar_registrants`
4. Activate the app
5. Note down: **Account ID**, **Client ID**, **Client Secret**

### 2. Install

```bash
# Copy to Hermes skills directory
git clone https://github.com/gergeisabo/hermes-zoom-skill.git
cp -r hermes-zoom-skill ~/.hermes/skills/productivity/zoom
```

### 3. Configure credentials

Create a JSON file with your Zoom credentials:

```json
{
  "account_id": "YOUR_ACCOUNT_ID",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
```

Store them:

```bash
python3 ~/.hermes/skills/productivity/zoom/scripts/setup.py --set-credentials --file /path/to/credentials.json
```

### 4. Verify

```bash
python3 ~/.hermes/skills/productivity/zoom/scripts/setup.py --check
```

## Usage

```bash
ZAPI="python3 ~/.hermes/skills/productivity/zoom/scripts/zoom_api.py"

# List meetings
$ZAPI meetings list --type upcoming
$ZAPI meetings list --type scheduled

# Get meeting details
$ZAPI meetings get 123456789

# List registrants (with custom questions like agency, ID)
$ZAPI meetings registrants 123456789
$ZAPI meetings registrants 123456789 --status approved

# List past meeting participants (who attended)
$ZAPI meetings participants 123456789

# List users
$ZAPI users list

# Raw API (any Zoom endpoint)
$ZAPI raw "/v2/users/me/settings"

# Paginate all results
$ZAPI --page-all meetings registrants 123456789
```

## Output Format

All commands return JSON.

- `meetings registrants`: includes `custom_questions` array with registration form fields
- `meetings participants`: includes `join_time`, `leave_time`, `duration`
- `--page-all`: NDJSON output (one record per line, all pages)

## Terminal Logs & Agent Workflow

### Registrant query (agent-driven)

```
$ hermes "list registrants for today's onboarding meeting"

# → Agent loads zoom skill
# → skill_view("zoom") → reads SKILL.md
# → Runs: python3 scripts/zoom_api.py meetings list --type upcoming
# → Picks meeting ID 89189605850
# → Runs: python3 scripts/zoom_api.py meetings registrants 89189605850
```

Output (custom questions include ÜGYNÖKSÉG, TÖRZSSZÁM):

```json
{
  "id": 89189605850,
  "topic": "ONLINE IGÉNYFELKELTÉS 2",
  "registrants": [
    {
      "email": "ugynok@peldahu.hu",
      "first_name": "András",
      "last_name": "Kovács",
      "custom_questions": [
        {"title": "ÜGYNÖKSÉG", "value": "Alpha Bt."},
        {"title": "TÖRZSSZÁM", "value": "XY12345"}
      ]
    }
  ]
}
```

### Recording download + cloud cleanup (real session, April 25 2026)

```
$ hermes "download all Zoom recordings to /mnt/storagebox/ZOOM/"

# Agent flow:
# → zoom_api.py raw "/v2/users/me/recordings"
# → Found: 3 recordings, 26 files, ~4.3 GB
# → curl -L -H "Authorization: Bearer {token}" for each download URL
# → Saved to /mnt/storagebox/ZOOM/
# → DELETE /v2/meetings/{meetingId}/recordings — all 3 cleared
```

Downloads completed in ~12 min for 4.3 GB.

## Contributors

Built with:

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — the AI agent framework
- [DeepSeek](https://deepseek.com) — code review partner
- [Xiaomi MiMo v2 Pro](https://xiaomimimo.com) (`mimo-v2-pro`) — authored the initial skill

## License

MIT
