from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from . import oauth

try:
    import bcrypt
except ImportError:  # pragma: no cover
    bcrypt = None

ROOT = Path("/srv/BusinessOps/creditdoc")
MEDIA_ROOT = ROOT / "public" / "pinterest" / "uploads"
MEDIA_URL = "/pinterest/uploads"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("PINS_UI_SECRET_KEY") or os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=12 * 1024 * 1024,
)


def db() -> sqlite3.Connection:
    return oauth.db()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def verify_password(stored_hash: str, password: str) -> bool:
    if stored_hash.startswith("$2") and bcrypt is not None:
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    try:
        return check_password_hash(stored_hash, password)
    except ValueError:
        return False


def ensure_schema() -> None:
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pins_ui_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pinterest_oauth (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT,
                expires_at TEXT,
                scope TEXT,
                account_username TEXT,
                connected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pinterest_pin_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT NOT NULL UNIQUE,
                pillar TEXT NOT NULL,
                money_page_slug TEXT,
                title TEXT,
                description TEXT,
                alt_text TEXT,
                image_prompt TEXT,
                image_path TEXT,
                link TEXT,
                status TEXT NOT NULL DEFAULT 'queued',
                rejection_reason TEXT,
                queued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                generated_at TEXT,
                posted_at TEXT,
                pin_id TEXT,
                scheduled_for TEXT,
                board_id TEXT,
                created_by TEXT
            )
            """
        )
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(pinterest_pin_queue)")}
        for name, decl in {
            "scheduled_for": "TEXT",
            "board_id": "TEXT",
            "created_by": "TEXT",
        }.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE pinterest_pin_queue ADD COLUMN {name} {decl}")
        username = oauth.env("PINS_UI_SEED_USERNAME")
        password = oauth.env("PINS_UI_SEED_PASSWORD")
        existing = conn.execute("SELECT id FROM pins_ui_users WHERE username=?", (username,)).fetchone() if username else None
        if username and password and not existing:
            conn.execute(
                "INSERT INTO pins_ui_users(username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )


ensure_schema()


def require_login() -> bool:
    return bool(session.get("user_id"))


def json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def login_required_json():
    if not require_login():
        return json_error("Not logged in", 401)
    return None


@app.get("/health")
def health():
    return "ok\n"


@app.get("/login")
def login_page():
    if require_login():
        return redirect(url_for("index"))
    return render_template("login.html", error=None)


@app.post("/login")
def login_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    with db() as conn:
        user = conn.execute("SELECT * FROM pins_ui_users WHERE username=?", (username,)).fetchone()
        if user and verify_password(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            try:
                conn.execute("UPDATE pins_ui_users SET last_login_at=? WHERE id=?", (now_utc(), user["id"]))
            except sqlite3.OperationalError:
                pass
            return redirect(url_for("index"))
    return render_template("login.html", error="Invalid username or password"), 401


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.get("/")
def index():
    if not require_login():
        return redirect(url_for("login_page"))
    return render_template("index.html", username=session.get("username", "gian"))


@app.get("/connect")
def connect():
    if not require_login():
        return redirect(url_for("login_page"))
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    return redirect(oauth.build_authorize_url(state))


@app.get("/oauth/callback")
def oauth_callback():
    if not require_login():
        return redirect(url_for("login_page"))
    if request.args.get("error"):
        return render_template("oauth_result.html", ok=False, message=request.args.get("error_description") or request.args["error"])
    if request.args.get("state") != session.get("oauth_state"):
        return render_template("oauth_result.html", ok=False, message="OAuth state did not match. Start Connect Pinterest again."), 400
    code = request.args.get("code")
    if not code:
        return render_template("oauth_result.html", ok=False, message="Pinterest did not return an authorization code."), 400
    try:
        result = oauth.save_token(oauth.exchange_code(code))
    except Exception as exc:
        return render_template("oauth_result.html", ok=False, message=str(exc)), 500
    return redirect(url_for("index", connected="1"))


@app.post("/disconnect")
def disconnect():
    if not require_login():
        return redirect(url_for("login_page"))
    with db() as conn:
        conn.execute("DELETE FROM pinterest_oauth WHERE id=1")
    return redirect(url_for("index"))


@app.post("/api/connect-token")
def api_connect_token():
    denied = login_required_json()
    if denied:
        return denied
    data = request.get_json(force=True, silent=True) or {}
    token = str(data.get("access_token") or "").strip()
    if not token:
        return json_error("Paste the Pinterest generated access token first")
    try:
        result = oauth.save_access_token(token)
        return jsonify({"ok": True, "account_username": result["account_username"], "scope": result["scope"]})
    except Exception as exc:
        return json_error(str(exc), 502)


@app.get("/api/me")
def api_me():
    denied = login_required_json()
    if denied:
        return denied
    row = oauth.get_stored_token()
    legacy_token_configured = bool(oauth.env("PINTEREST_ACCESS_TOKEN"))
    return jsonify(
        {
            "ok": True,
            "user": session.get("username"),
            "pinterest_connected": bool(row),
            "token_source": "oauth" if row else None,
            "legacy_token_configured": legacy_token_configured,
            "account_username": row["account_username"] if row else None,
            "scope": row["scope"] if row else None,
            "expires_at": row["expires_at"] if row else None,
        }
    )


@app.get("/api/pinterest/account")
def api_account():
    denied = login_required_json()
    if denied:
        return denied
    try:
        return jsonify({"ok": True, "account": oauth.get_user_account()})
    except Exception as exc:
        return json_error(str(exc), 502)


@app.get("/api/boards")
def api_boards():
    denied = login_required_json()
    if denied:
        return denied
    try:
        return jsonify({"ok": True, "boards": oauth.list_boards()})
    except Exception as exc:
        return json_error(str(exc), 502)


@app.post("/api/upload")
def api_upload():
    denied = login_required_json()
    if denied:
        return denied
    file = request.files.get("image")
    if not file or not file.filename:
        return json_error("No image uploaded")
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secure_filename(file.filename)}"
    path = MEDIA_ROOT / filename
    file.save(path)
    return jsonify({"ok": True, "image_path": f"{MEDIA_URL}/{filename}"})


@app.post("/api/pins")
def api_create_pin():
    denied = login_required_json()
    if denied:
        return denied
    data = request.get_json(force=True, silent=True) or request.form
    title = str(data.get("title") or "").strip()
    description = str(data.get("description") or "").strip()
    link = str(data.get("link") or "https://www.creditdoc.co").strip()
    board_id = str(data.get("board_id") or "").strip()
    scheduled_for = str(data.get("scheduled_for") or "").strip() or None
    image_path = str(data.get("image_path") or "").strip()
    alt_text = str(data.get("alt_text") or "").strip()
    if not title or not description or not link:
        return json_error("Title, description and link are required")
    phrase = f"ui-{secrets.token_hex(8)}"
    with db() as conn:
        cur = conn.execute(
            """
            INSERT INTO pinterest_pin_queue
                (phrase, pillar, title, description, alt_text, image_path, link, status, scheduled_for, board_id, created_by, queued_at)
            VALUES (?, 'ui-demo', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                phrase,
                title,
                description,
                alt_text,
                image_path,
                link,
                "scheduled" if scheduled_for else "image_ok",
                scheduled_for,
                board_id,
                session.get("username"),
                now_utc(),
            ),
        )
    return jsonify({"ok": True, "id": cur.lastrowid})


def build_pin_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = {
        "board_id": row["board_id"],
        "title": row["title"],
        "description": row["description"],
        "link": row["link"] or "https://www.creditdoc.co",
    }
    if row["alt_text"]:
        payload["alt_text"] = row["alt_text"]
    image_path = row["image_path"] or ""
    if image_path.startswith("http"):
        payload["media_source"] = {"source_type": "image_url", "url": image_path}
    elif image_path.startswith("/"):
        payload["media_source"] = {"source_type": "image_url", "url": f"https://www.creditdoc.co{image_path}"}
    else:
        payload["media_source"] = {
            "source_type": "image_url",
            "url": "https://www.creditdoc.co/og-default.png",
        }
    return payload


def post_queue_row(pin_id: int) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM pinterest_pin_queue WHERE id=?", (pin_id,)).fetchone()
        if not row:
            raise RuntimeError(f"Pin queue row {pin_id} not found")
        conn.execute("UPDATE pinterest_pin_queue SET status='posting', rejection_reason=NULL WHERE id=?", (pin_id,))
    try:
        result = oauth.api_post("/pins", build_pin_payload(row))
        with db() as conn:
            conn.execute(
                "UPDATE pinterest_pin_queue SET status='posted', pin_id=?, posted_at=?, rejection_reason=NULL WHERE id=?",
                (result.get("id"), now_utc(), pin_id),
            )
        return result
    except Exception as exc:
        with db() as conn:
            conn.execute(
                "UPDATE pinterest_pin_queue SET status='failed', rejection_reason=? WHERE id=?",
                (str(exc), pin_id),
            )
        raise


@app.post("/api/pins/<int:pin_id>/post-now")
def api_post_now(pin_id: int):
    denied = login_required_json()
    if denied:
        return denied
    try:
        return jsonify({"ok": True, "result": post_queue_row(pin_id)})
    except Exception as exc:
        return json_error(str(exc), 502)


@app.get("/api/pins")
def api_list_pins():
    denied = login_required_json()
    if denied:
        return denied
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, link, status, scheduled_for, board_id, pin_id, rejection_reason, queued_at, posted_at
            FROM pinterest_pin_queue
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()
    return jsonify({"ok": True, "pins": [dict(r) for r in rows]})


@app.post("/api/pins/<int:pin_id>/cancel")
def api_cancel_pin(pin_id: int):
    denied = login_required_json()
    if denied:
        return denied
    with db() as conn:
        conn.execute("UPDATE pinterest_pin_queue SET status='cancelled' WHERE id=? AND status='scheduled'", (pin_id,))
    return jsonify({"ok": True})
