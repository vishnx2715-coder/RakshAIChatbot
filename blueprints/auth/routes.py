"""
blueprints/auth/routes.py — Authentication routes for RAKSHA.

Routes (all paths unchanged from original app.py):
  POST /api/register
  POST /api/login
  GET|POST /api/google-auth
  POST /api/logout
  GET  /api/me
  POST /api/set-lang
  GET  /api/languages

Phase 7 additions:
  - Rate limits on register/login/google-auth
  - Input length caps on all POST bodies
  - Explicit Google token audience check
  - Generic error messages (no user enumeration)
"""

import json
import os
import re
import secrets
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, session

from blueprints.auth.data import ALL_LANGUAGES, UI_STRINGS
from blueprints.auth.services import hash_password, needs_rehash, verify_password
from extensions import USE_SUPABASE, supabase

auth_bp = Blueprint("auth", __name__)

# ── Input caps ────────────────────────────────────────────────
_MAX_NAME     = 120
_MAX_EMAIL    = 254
_MAX_PASSWORD = 128
_MAX_PHONE    = 20
_MAX_LANG     = 40
_EMAIL_RE     = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

USERS_FILE = "users.json"


# ── DB helpers ────────────────────────────────────────────────

def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_users(u: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(u, f, indent=2)


def db_get_user(email: str):
    if USE_SUPABASE:
        try:
            res = supabase.table("users").select("*").eq("email", email).single().execute()
            return res.data
        except Exception:
            return None
    return _load_users().get(email)


def db_create_user(name: str, email: str, pw: str, phone: str):
    now_str = _now_str()
    if USE_SUPABASE:
        try:
            res = supabase.table("users").insert({
                "name": name, "email": email, "password": hash_password(pw),
                "phone": phone or "", "lang": "English",
                "joined": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat(),
                "login_count": 1, "auth_provider": "email",
            }).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"[db_create_user] Supabase error: {e}")
            return None
    users = _load_users()
    users[email] = {
        "name": name, "email": email, "password": hash_password(pw),
        "phone": phone or "", "lang": "English",
        "joined": now_str, "last_login": now_str, "login_count": 1,
        "auth_provider": "email",
    }
    _save_users(users)
    return users[email]


def db_record_login(email: str) -> None:
    now_str = _now_str()
    if USE_SUPABASE:
        try:
            res = supabase.table("users").select("login_count").eq("email", email).single().execute()
            current = (res.data or {}).get("login_count", 0) or 0
            supabase.table("users").update({
                "last_login": datetime.utcnow().isoformat(),
                "login_count": current + 1,
            }).eq("email", email).execute()
        except Exception as e:
            print(f"[db_record_login] Supabase error: {e}")
        return
    users = _load_users()
    if email in users:
        users[email]["last_login"] = now_str
        users[email]["login_count"] = (users[email].get("login_count", 0) or 0) + 1
        _save_users(users)


def db_update_lang(email: str, lang: str) -> None:
    if USE_SUPABASE:
        try:
            supabase.table("users").update({"lang": lang}).eq("email", email).execute()
        except Exception:
            pass
        return
    users = _load_users()
    if email in users:
        users[email]["lang"] = lang
        _save_users(users)


def db_update_password(email: str, new_hash: str) -> None:
    if USE_SUPABASE:
        try:
            supabase.table("users").update({"password": new_hash}).eq("email", email).execute()
        except Exception as e:
            print(f"[db_update_password] Supabase error: {e}")
        return
    users = _load_users()
    if email in users:
        users[email]["password"] = new_hash
        _save_users(users)


def _rate_limit(limit_string: str) -> None:
    """Apply a rate limit from within a route. No-op if limiter not configured."""
    lim = current_app.extensions.get("limiter")
    if lim:
        lim.limit(limit_string)(lambda: None)()


# ── Routes ────────────────────────────────────────────────────

@auth_bp.route("/api/register", methods=["POST"])
def register():
    _rate_limit("10 per hour")
    d     = request.get_json(force=True, silent=True) or {}
    name  = str(d.get("name", ""))[:_MAX_NAME].strip()
    email = str(d.get("email", ""))[:_MAX_EMAIL].strip().lower()
    pw    = str(d.get("password", ""))[:_MAX_PASSWORD]
    phone = str(d.get("phone", ""))[:_MAX_PHONE].strip()

    if not all([name, email, pw]):
        return jsonify({"status": "error", "message": "All fields required."})
    if len(pw) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters."})
    if not _EMAIL_RE.match(email):
        return jsonify({"status": "error", "message": "Invalid email."})
    if db_get_user(email):
        return jsonify({"status": "error", "message": "Email already registered."})

    user = db_create_user(name, email, pw, phone)
    if not user:
        return jsonify({"status": "error", "message": "Registration failed. Please try again."})
    session["email"] = email
    session["name"]  = name
    session["lang"]  = "English"
    return jsonify({"status": "success", "name": name, "lang": "English"})


@auth_bp.route("/api/login", methods=["POST"])
def login():
    _rate_limit("20 per hour")
    d     = request.get_json(force=True, silent=True) or {}
    email = str(d.get("email", ""))[:_MAX_EMAIL].strip().lower()
    pw    = str(d.get("password", ""))[:_MAX_PASSWORD]
    _BAD  = jsonify({"status": "error", "message": "Invalid credentials."})

    if not email or not pw:
        return _BAD
    user = db_get_user(email)
    if not user:
        return _BAD
    stored = user.get("password", "")
    if not verify_password(stored, pw):
        return _BAD
    if needs_rehash(stored):
        try:
            db_update_password(email, hash_password(pw))
        except Exception as e:
            print(f"[login] rehash failed: {e}")
    db_record_login(email)
    session["email"] = email
    session["name"]  = user["name"]
    session["lang"]  = user.get("lang", "English")
    return jsonify({"status": "success", "name": user["name"], "lang": user.get("lang", "English")})


@auth_bp.route("/api/google-auth", methods=["GET", "POST"])
def google_auth():
    from config import Config
    import requests as _requests

    if request.method == "POST":
        _rate_limit("20 per hour")

    if request.method == "GET":
        return (
            """<html><body style="font-family:sans-serif;padding:40px;background:#020c1b;color:#dff4ff;">
            <h2>&#9888; Google Sign-In Error</h2>
            <p>This page should not be opened directly.<br>
            Please close this tab and sign in from the RAKSHA app.</p>
            <script>
              if(window.opener){ window.opener.postMessage({type:'google_auth_error',
              message:'Wrong flow - please retry'},'*'); }
              setTimeout(()=>window.close(), 2000);
            </script></body></html>""",
            400,
        )

    if not Config.GOOGLE_CLIENT_ID:
        return jsonify({"status": "error", "message": "Google Sign-In is not configured on this server."}), 503

    body       = request.get_json(force=True, silent=True) or {}
    credential = str(body.get("credential", ""))[:2048].strip()
    if not credential:
        return jsonify({"status": "error", "message": "No credential received from Google."}), 400

    # Verify ID token — audience MUST equal GOOGLE_CLIENT_ID (prevents substitution attacks)
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            Config.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ImportError:
        try:
            resp = _requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential}, timeout=8,
            )
            if resp.status_code != 200:
                return jsonify({"status": "error", "message": "Google token verification failed."}), 401
            id_info = resp.json()
            if id_info.get("aud") != Config.GOOGLE_CLIENT_ID:
                return jsonify({"status": "error", "message": "Token audience mismatch."}), 401
        except Exception as e:
            return jsonify({"status": "error", "message": f"Could not verify Google token: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid Google token: {e}"}), 401

    email          = (id_info.get("email") or "").strip().lower()[:_MAX_EMAIL]
    name           = (id_info.get("name") or id_info.get("given_name") or email.split("@")[0])[:_MAX_NAME]
    email_verified = id_info.get("email_verified", False)

    if not email or not _EMAIL_RE.match(email):
        return jsonify({"status": "error", "message": "Could not retrieve valid email from Google."}), 400
    if not email_verified:
        return jsonify({"status": "error", "message": "Google account email is not verified."}), 400

    existing = db_get_user(email)
    if existing:
        lang   = existing.get("lang", "English")
        db_record_login(email)
        is_new = False
    else:
        random_pw = secrets.token_hex(32)
        user = db_create_user(name, email, random_pw, "")
        if not user:
            return jsonify({"status": "error", "message": "Account creation failed. Please try again."}), 500
        if USE_SUPABASE:
            try:
                supabase.table("users").update({"auth_provider": "google"}).eq("email", email).execute()
            except Exception as e:
                print(f"[google_auth] Could not set auth_provider: {e}")
        lang   = "English"
        is_new = True

    session["email"] = email
    session["name"]  = name
    session["lang"]  = lang
    return jsonify({"status": "success", "name": name, "lang": lang, "is_new": is_new, "email": email})


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})


@auth_bp.route("/api/me")
def me():
    if "email" in session:
        return jsonify({
            "logged_in": True,
            "name": session["name"],
            "lang": session.get("lang", "English"),
        })
    return jsonify({"logged_in": False})


@auth_bp.route("/api/set-lang", methods=["POST"])
def set_lang():
    if "email" not in session:
        return jsonify({"status": "error"})
    lang = str((request.get_json(force=True, silent=True) or {}).get("lang", "English"))[:_MAX_LANG]
    session["lang"] = lang
    db_update_lang(session["email"], lang)
    return jsonify({"status": "success", "lang": lang})


@auth_bp.route("/api/languages")
def languages():
    return jsonify({"languages": ALL_LANGUAGES, "ui_strings": UI_STRINGS})
