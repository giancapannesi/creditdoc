from __future__ import annotations

import base64
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path("/srv/BusinessOps/creditdoc")
DB_PATH = ROOT / "tools" / "creditdoc_pinterest_ui" / "state" / "pinterest_ui.db"
ENV_PATH = ROOT / ".env"
AUTH_URL = "https://www.pinterest.com/oauth/"
TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
API_URL = "https://api.pinterest.com/v5"
DEFAULT_SCOPES = "pins:read,pins:write,boards:read,boards:write,user_accounts:read"


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    try:
        lines = ENV_PATH.read_text().splitlines()
    except PermissionError:
        # systemd loads this file via EnvironmentFile for the service user.
        # If direct reads are denied, keep using the already exported env.
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env(name: str, default: str = "") -> str:
    load_env()
    return os.environ.get(name, default)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def basic_auth_header() -> str:
    client_id = env("PINTEREST_APP_ID")
    secret = env("PINTEREST_APP_SECRET")
    token = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    return f"Basic {token}"


def redirect_uri() -> str:
    return env("PINS_UI_REDIRECT_URI", "https://pins.saviumwealth.com/oauth/callback")


def build_authorize_url(state: str) -> str:
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": env("PINTEREST_APP_ID"),
        "redirect_uri": redirect_uri(),
        "scope": DEFAULT_SCOPES,
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict[str, Any]:
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": basic_auth_header()},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri(),
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Pinterest token exchange failed {response.status_code}: {response.text[:800]}")
    return response.json()


def refresh_token(refresh: str) -> dict[str, Any]:
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": basic_auth_header()},
        data={"grant_type": "refresh_token", "refresh_token": refresh, "scope": DEFAULT_SCOPES},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Pinterest token refresh failed {response.status_code}: {response.text[:800]}")
    return response.json()


def save_token(payload: dict[str, Any]) -> dict[str, Any]:
    access_token = payload["access_token"]
    refresh = payload.get("refresh_token")
    expires_in = int(payload.get("expires_in") or 3600)
    expires_at = iso(utc_now() + timedelta(seconds=expires_in))
    scope = payload.get("scope") or DEFAULT_SCOPES
    account = get_user_account(access_token)
    username = account.get("username") or account.get("account_type") or "connected"
    with db() as conn:
        conn.execute(
            """
            INSERT INTO pinterest_oauth
                (id, access_token, refresh_token, token_type, expires_at, scope, account_username, connected_at, updated_at)
            VALUES
                (1, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                access_token=excluded.access_token,
                refresh_token=coalesce(excluded.refresh_token, pinterest_oauth.refresh_token),
                token_type=excluded.token_type,
                expires_at=excluded.expires_at,
                scope=excluded.scope,
                account_username=excluded.account_username,
                updated_at=datetime('now')
            """,
            (access_token, refresh, payload.get("token_type"), expires_at, scope, username),
        )
    return {"account_username": username, "scope": scope, "expires_at": expires_at}


def save_access_token(access_token: str, scope: str = "pins:read,boards:read,user_accounts:read") -> dict[str, Any]:
    account = get_user_account(access_token)
    username = account.get("username") or account.get("account_type") or "connected"
    # Pinterest generated test tokens do not always expose refresh metadata.
    expires_at = iso(utc_now() + timedelta(days=30))
    with db() as conn:
        conn.execute(
            """
            INSERT INTO pinterest_oauth
                (id, access_token, refresh_token, token_type, expires_at, scope, account_username, connected_at, updated_at)
            VALUES
                (1, ?, NULL, 'bearer', ?, ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                access_token=excluded.access_token,
                refresh_token=NULL,
                token_type=excluded.token_type,
                expires_at=excluded.expires_at,
                scope=excluded.scope,
                account_username=excluded.account_username,
                updated_at=datetime('now')
            """,
            (access_token, expires_at, scope, username),
        )
    return {"account_username": username, "scope": scope, "expires_at": expires_at}


def get_stored_token() -> sqlite3.Row | None:
    with db() as conn:
        return conn.execute("SELECT * FROM pinterest_oauth WHERE id=1").fetchone()


def get_active_token() -> str:
    row = get_stored_token()
    if row:
        expires_at = parse_iso(row["expires_at"])
        if expires_at and expires_at > utc_now() + timedelta(minutes=10):
            return row["access_token"]
        if row["refresh_token"]:
            payload = refresh_token(row["refresh_token"])
            save_token(payload)
            fresh = get_stored_token()
            if fresh:
                return fresh["access_token"]
    raise RuntimeError("Pinterest is not connected. Click Connect Pinterest first.")


def api_get(path: str, token: str | None = None) -> dict[str, Any]:
    response = requests.get(
        f"{API_URL}{path}",
        headers={"Authorization": f"Bearer {token or get_active_token()}"},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Pinterest GET {path} failed {response.status_code}: {response.text[:800]}")
    return response.json()


def api_post(path: str, payload: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    response = requests.post(
        f"{API_URL}{path}",
        headers={"Authorization": f"Bearer {token or get_active_token()}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if not response.ok:
        raise RuntimeError(f"Pinterest POST {path} failed {response.status_code}: {response.text[:1200]}")
    return response.json()


def get_user_account(token: str | None = None) -> dict[str, Any]:
    return api_get("/user_account", token)


def list_boards(token: str | None = None) -> list[dict[str, Any]]:
    data = api_get("/boards?page_size=100", token)
    return data.get("items", [])
