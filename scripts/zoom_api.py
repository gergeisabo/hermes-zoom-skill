#!/usr/bin/env python3
"""Zoom API client for Hermes Agent.

Usage:
  zoom_api.py meetings list [--type upcoming|scheduled|live] [--page-size N]
  zoom_api.py meetings get MEETING_ID
  zoom_api.py meetings registrants MEETING_ID [--status approved|pending|denied] [--page-size N]
  zoom_api.py meetings participants MEETING_ID [--type past] [--page-size N]
  zoom_api.py users list [--status active|inactive|pending] [--page-size N]
  zoom_api.py users get [--user-id ID|me]
  zoom_api.py webinars list [--page-size N]
  zoom_api.py webinars registrants WEBINAR_ID [--status approved|pending|denied] [--page-size N]
  zoom_api.py raw PATH [--params JSON] [--method GET|POST|PUT|PATCH|DELETE] [--body JSON]

All commands return JSON. Paginated endpoints return first page by default.
Use --page-all for NDJSON (one record per line, all pages).

Examples:
  zoom_api.py meetings list --type upcoming
  zoom_api.py meetings registrants 123456789 --status approved
  zoom_api.py meetings participants 123456789
  zoom_api.py raw "/v2/users/me/settings"
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

# Import token getter from setup
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from setup import get_access_token


BASE_URL = "https://api.zoom.us"


def api_call(path: str, params: dict = None, method: str = "GET", body: dict = None) -> dict:
    """Make a Zoom API call. Returns parsed JSON response."""
    token = get_access_token()
    if not token:
        print(json.dumps({"error": "NOT_AUTHENTICATED", "message": "Run setup.py --check first"}))
        sys.exit(1)

    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = json.dumps(body).encode() if body else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            error_json = json.loads(error_body)
        except Exception:
            error_json = {"raw": error_body}
        print(json.dumps({"error": e.code, "message": error_json}))
        sys.exit(1)


def paginate(path: str, params: dict = None, page_size: int = 30, max_pages: int = None):
    """Auto-paginate a Zoom API endpoint. Yields individual records."""
    if params is None:
        params = {}
    params["page_size"] = min(page_size, 300)

    page_count = 0
    next_page_token = None

    while True:
        if next_page_token:
            params["next_page_token"] = next_page_token

        result = api_call(path, params=params)

        records = result.get("registrants") or result.get("participants") or result.get("meetings") or result.get("users") or result.get("webinars") or []

        for r in records:
            yield r

        next_page_token = result.get("next_page_token")
        page_count += 1

        if not next_page_token:
            break
        if max_pages and page_count >= max_pages:
            break


# --- Command handlers ---

def cmd_meetings_list(args):
    params = {"type": args.type or "scheduled"}
    if args.page_size:
        params["page_size"] = args.page_size

    if args.page_all:
        for record in paginate("/v2/users/me/meetings", params=params):
            print(json.dumps(record))
    else:
        result = api_call("/v2/users/me/meetings", params=params)
        print(json.dumps(result, indent=2))


def cmd_meetings_get(args):
    result = api_call(f"/v2/meetings/{args.meeting_id}")
    print(json.dumps(result, indent=2))


def cmd_meetings_registrants(args):
    params = {}
    if args.status:
        params["status"] = args.status
    if args.page_size:
        params["page_size"] = args.page_size

    if args.page_all:
        for record in paginate(f"/v2/meetings/{args.meeting_id}/registrants", params=params):
            print(json.dumps(record))
    else:
        result = api_call(f"/v2/meetings/{args.meeting_id}/registrants", params=params)
        print(json.dumps(result, indent=2))


def cmd_meetings_participants(args):
    params = {"type": args.type or "past"}
    if args.page_size:
        params["page_size"] = args.page_size

    if args.page_all:
        for record in paginate(f"/v2/report/meetings/{args.meeting_id}/participants", params=params):
            print(json.dumps(record))
    else:
        result = api_call(f"/v2/report/meetings/{args.meeting_id}/participants", params=params)
        print(json.dumps(result, indent=2))


def cmd_users_list(args):
    params = {}
    if args.status:
        params["status"] = args.status
    if args.page_size:
        params["page_size"] = args.page_size

    if args.page_all:
        for record in paginate("/v2/users", params=params):
            print(json.dumps(record))
    else:
        result = api_call("/v2/users", params=params)
        print(json.dumps(result, indent=2))


def cmd_users_get(args):
    user_id = args.user_id or "me"
    result = api_call(f"/v2/users/{user_id}")
    print(json.dumps(result, indent=2))


def cmd_webinars_list(args):
    params = {}
    if args.page_size:
        params["page_size"] = args.page_size

    if args.page_all:
        for record in paginate("/v2/users/me/webinars", params=params):
            print(json.dumps(record))
    else:
        result = api_call("/v2/users/me/webinars", params=params)
        print(json.dumps(result, indent=2))


def cmd_webinars_registrants(args):
    params = {}
    if args.status:
        params["status"] = args.status
    if args.page_size:
        params["page_size"] = args.page_size

    if args.page_all:
        for record in paginate(f"/v2/webinars/{args.webinar_id}/registrants", params=params):
            print(json.dumps(record))
    else:
        result = api_call(f"/v2/webinars/{args.webinar_id}/registrants", params=params)
        print(json.dumps(result, indent=2))


def cmd_raw(args):
    params = json.loads(args.params) if args.params else None
    body = json.loads(args.body) if args.body else None
    result = api_call(args.path, params=params, method=args.method or "GET", body=body)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Zoom API client")
    parser.add_argument("--page-all", action="store_true", help="Paginate all results as NDJSON")

    sub = parser.add_subparsers(dest="command")

    # meetings
    m = sub.add_parser("meetings")
    ms = m.add_subparsers(dest="action")

    ml = ms.add_parser("list")
    ml.add_argument("--type", choices=["upcoming", "scheduled", "live"])
    ml.add_argument("--page-size", type=int)

    mg = ms.add_parser("get")
    mg.add_argument("meeting_id")

    mr = ms.add_parser("registrants")
    mr.add_argument("meeting_id")
    mr.add_argument("--status", choices=["approved", "pending", "denied"])
    mr.add_argument("--page-size", type=int)

    mp = ms.add_parser("participants")
    mp.add_argument("meeting_id")
    mp.add_argument("--type", default="past")
    mp.add_argument("--page-size", type=int)

    # users
    u = sub.add_parser("users")
    us = u.add_subparsers(dest="action")

    ul = us.add_parser("list")
    ul.add_argument("--status", choices=["active", "inactive", "pending"])
    ul.add_argument("--page-size", type=int)

    ug = us.add_parser("get")
    ug.add_argument("--user-id", default="me")

    # webinars
    w = sub.add_parser("webinars")
    ws = w.add_subparsers(dest="action")

    wl = ws.add_parser("list")
    wl.add_argument("--page-size", type=int)

    wr = ws.add_parser("registrants")
    wr.add_argument("webinar_id")
    wr.add_argument("--status", choices=["approved", "pending", "denied"])
    wr.add_argument("--page-size", type=int)

    # raw
    r = sub.add_parser("raw")
    r.add_argument("path", help="API path, e.g. /v2/users/me")
    r.add_argument("--params", help="Query params as JSON")
    r.add_argument("--method", default="GET", choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    r.add_argument("--body", help="Request body as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = {
        "meetings": {
            "list": cmd_meetings_list,
            "get": cmd_meetings_get,
            "registrants": cmd_meetings_registrants,
            "participants": cmd_meetings_participants,
        },
        "users": {
            "list": cmd_users_list,
            "get": cmd_users_get,
        },
        "webinars": {
            "list": cmd_webinars_list,
            "registrants": cmd_webinars_registrants,
        },
        "raw": {"*": cmd_raw},
    }

    if args.command == "raw":
        cmd_raw(args)
    else:
        action = args.action
        if not action:
            print(f"Error: no action for {args.command}. Use: {args.command} list|get|registrants|participants")
            sys.exit(1)
        fn = handler.get(args.command, {}).get(action)
        if not fn:
            print(f"Error: unknown action '{action}' for {args.command}")
            sys.exit(1)
        fn(args)


if __name__ == "__main__":
    main()
