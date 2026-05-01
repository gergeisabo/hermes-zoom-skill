#!/usr/bin/env python3
"""Zoom API credential setup for Hermes Agent.

Commands:
  setup.py --check                          # Are credentials valid? Exit 0 = yes, 1 = no
  setup.py --set-credentials               # Store Account ID, Client ID, Client Secret
  setup.py --set-credentials --file PATH   # Store from JSON file
  setup.py --revoke                         # Delete stored credentials
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

def _get_hermes_home() -> Path:
    return Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))

HERMES_HOME = _get_hermes_home()
CREDENTIALS_PATH = HERMES_HOME / "zoom_credentials.json"
TOKEN_CACHE_PATH = HERMES_HOME / "zoom_token_cache.json"

ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"


def get_access_token() -> str | None:
    """Get a valid Zoom access token, refreshing if needed."""
    # Check cached token
    if TOKEN_CACHE_PATH.exists():
        try:
            cache = json.loads(TOKEN_CACHE_PATH.read_text())
            import time
            if cache.get("expires_at", 0) > time.time() + 60:
                return cache["access_token"]
        except Exception:
            pass

    # Get fresh token
    if not CREDENTIALS_PATH.exists():
        return None

    creds = json.loads(CREDENTIALS_PATH.read_text())
    account_id = creds.get("account_id")
    client_id = creds.get("client_id")
    client_secret = creds.get("client_secret")

    if not all([account_id, client_id, client_secret]):
        return None

    import base64
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    data = urllib.parse.urlencode({
        "grant_type": "account_credentials",
        "account_id": account_id,
    }).encode()

    req = urllib.request.Request(
        ZOOM_TOKEN_URL,
        data=data,
        headers={"Authorization": f"Basic {auth}"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            access_token = result["access_token"]
            expires_in = result.get("expires_in", 3600)

            import time
            TOKEN_CACHE_PATH.write_text(json.dumps({
                "access_token": access_token,
                "expires_at": time.time() + expires_in,
            }))

            return access_token
    except Exception as e:
        print(f"ERROR: Failed to get Zoom access token: {e}", file=sys.stderr)
        return None


def cmd_check():
    """Check if Zoom credentials are configured and token works."""
    if not CREDENTIALS_PATH.exists():
        print("NOT_CONFIGURED: No credentials at", CREDENTIALS_PATH)
        sys.exit(1)

    creds = json.loads(CREDENTIALS_PATH.read_text())
    missing = [k for k in ["account_id", "client_id", "client_secret"] if not creds.get(k)]
    if missing:
        print(f"NOT_CONFIGURED: Missing fields: {', '.join(missing)}")
        sys.exit(1)

    token = get_access_token()
    if not token:
        print("TOKEN_FAILED: Could not obtain access token")
        sys.exit(1)

    # Test with a simple API call — try users/me first, fall back to meetings list
    try:
        req = urllib.request.Request(
            "https://api.zoom.us/v2/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req) as resp:
            user = json.loads(resp.read())
            print(f"AUTHENTICATED: {user.get('email', 'unknown')} ({user.get('type', '?')} account)")
            print(f"Credentials: {CREDENTIALS_PATH}")
            print(f"Token cache: {TOKEN_CACHE_PATH}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if hasattr(e, 'read') else str(e)
        if e.code in (400, 4711) and "user:read:user" in error_body:
            # Token works but user:read:user scope missing — verify with meetings endpoint instead
            try:
                req2 = urllib.request.Request(
                    "https://api.zoom.us/v2/users/me/meetings?page_size=1",
                    headers={"Authorization": f"Bearer {token}"},
                )
                with urllib.request.urlopen(req2):
                    print(f"AUTHENTICATED: (token valid, user:read:user scope not configured)")
                    print(f"Note: add 'user:read:user' scope in Zoom Marketplace for user info access")
                    print(f"Credentials: {CREDENTIALS_PATH}")
                    print(f"Token cache: {TOKEN_CACHE_PATH}")
            except Exception as e2:
                print(f"API_ERROR: {e2}")
                sys.exit(1)
        else:
            body = e.read().decode() if hasattr(e, 'read') else str(e)
            print(f"API_ERROR: {e.code} - {body}")
            sys.exit(1)


def cmd_set_credentials(file_path: str = None):
    """Store Zoom credentials."""
    if file_path:
        cred_file = Path(file_path).resolve()
        if not cred_file.is_file():
            print(f"ERROR: {file_path} does not exist or is not a file")
            sys.exit(1)
        if cred_file.suffix != ".json":
            print("ERROR: credentials file must be a .json file")
            sys.exit(1)
        data = json.loads(cred_file.read_text())
        account_id = data.get("account_id")
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
    else:
        print("Provide credentials as JSON. Required fields: account_id, client_id, client_secret")
        print("Use: setup.py --set-credentials --file /path/to/credentials.json")
        sys.exit(1)

    if not all([account_id, client_id, client_secret]):
        print("ERROR: Missing one or more required fields: account_id, client_id, client_secret")
        sys.exit(1)

    CREDENTIALS_PATH.write_text(json.dumps({
        "account_id": account_id,
        "client_id": client_id,
        "client_secret": client_secret,
    }, indent=2))

    print(f"OK: Credentials saved to {CREDENTIALS_PATH}")


def cmd_revoke():
    """Delete stored credentials and token cache."""
    for p in [CREDENTIALS_PATH, TOKEN_CACHE_PATH]:
        if p.exists():
            p.unlink()
            print(f"Deleted: {p}")
    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Zoom API setup for Hermes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--set-credentials", action="store_true")
    group.add_argument("--revoke", action="store_true")
    parser.add_argument("--file", help="Path to credentials JSON file")

    args = parser.parse_args()

    if args.check:
        cmd_check()
    elif args.set_credentials:
        cmd_set_credentials(args.file)
    elif args.revoke:
        cmd_revoke()


if __name__ == "__main__":
    main()
