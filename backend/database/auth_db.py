import sqlite3
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                avatar_url TEXT,
                bio TEXT,
                settings TEXT,
                reset_token TEXT,
                reset_token_expires TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()

def create_user(
    email: str,
    password_hash: str,
    full_name: str,
    avatar_url: Optional[str] = None,
    bio: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    init_auth_db()
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    default_settings = {
        "notifications": True,
        "email_alerts": True,
        "dark_mode": False
    }
    if settings:
        default_settings.update(settings)

    clean_email = email.strip().lower()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, avatar_url, bio, settings, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                clean_email,
                password_hash,
                full_name.strip(),
                avatar_url or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
                bio or "Social Media Analyst",
                json.dumps(default_settings),
                now,
                now
            )
        )
        conn.commit()

    return get_user_by_id(user_id)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    init_auth_db()
    clean_email = email.strip().lower()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (clean_email,)).fetchone()
        if not row:
            return None
        return dict(row)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    init_auth_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("settings"):
            try:
                data["settings"] = json.loads(data["settings"])
            except Exception:
                data["settings"] = {}
        return data

def update_user_profile(
    user_id: str,
    full_name: Optional[str] = None,
    bio: Optional[str] = None,
    avatar_url: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    init_auth_db()
    user = get_user_by_id(user_id)
    if not user:
        return None

    now = datetime.now(timezone.utc).isoformat()
    new_name = full_name.strip() if full_name is not None else user["full_name"]
    new_bio = bio if bio is not None else user.get("bio", "")
    new_avatar = avatar_url if avatar_url is not None else user.get("avatar_url", "")
    
    current_settings = user.get("settings", {})
    if settings:
        current_settings.update(settings)

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET full_name = ?, bio = ?, avatar_url = ?, settings = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_name, new_bio, new_avatar, json.dumps(current_settings), now, user_id)
        )
        conn.commit()

    return get_user_by_id(user_id)

def set_password_reset_token(email: str, token: str, expires_minutes: int = 30) -> bool:
    init_auth_db()
    clean_email = email.strip().lower()
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(minutes=expires_minutes)).isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET reset_token = ?, reset_token_expires = ?
            WHERE email = ?
            """,
            (token, expires, clean_email)
        )
        conn.commit()
        return cursor.rowcount > 0

def verify_and_consume_reset_token(token: str, new_password_hash: str) -> bool:
    init_auth_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, reset_token_expires FROM users WHERE reset_token = ?
            """,
            (token,)
        ).fetchone()

        if not row:
            return False

        if row["reset_token_expires"] < now_iso:
            return False  # Expired

        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL, updated_at = ?
            WHERE id = ?
            """,
            (new_password_hash, now_iso, row["id"])
        )
        conn.commit()
        return True

def update_password(user_id: str, new_password_hash: str) -> bool:
    init_auth_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_password_hash, now_iso, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
