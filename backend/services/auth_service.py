import secrets
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from database.auth_db import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_profile,
    set_password_reset_token,
    verify_and_consume_reset_token,
    update_password
)

class AuthService:
    """
    Core Authentication & User Management Service (Member 1).
    Handles password hashing with bcrypt, JWT token issuing/verifying,
    profile management, and forgot password tokens.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "iat": now,
            "exp": expire,
            "sub": str(data.get("sub", ""))
        })
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    def register_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        clean_email = email.strip().lower()
        if not clean_email or "@" not in clean_email:
            raise ValueError("Please provide a valid email address.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if not full_name or not full_name.strip():
            raise ValueError("Full name is required.")

        existing = get_user_by_email(clean_email)
        if existing:
            raise ValueError("An account with this email address already exists.")

        pwd_hash = self.hash_password(password)
        user = create_user(clean_email, pwd_hash, full_name.strip())

        token = self.create_access_token({
            "sub": user["id"],
            "email": user["email"],
            "name": user["full_name"]
        })

        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "avatar_url": user.get("avatar_url"),
                "bio": user.get("bio"),
                "settings": user.get("settings", {})
            },
            "access_token": token,
            "token_type": "bearer"
        }

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        clean_email = email.strip().lower()
        user = get_user_by_email(clean_email)
        if not user:
            raise ValueError("Invalid email or password.")

        if not self.verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password.")

        token = self.create_access_token({
            "sub": user["id"],
            "email": user["email"],
            "name": user["full_name"]
        })

        full_user = get_user_by_id(user["id"])

        return {
            "user": {
                "id": full_user["id"],
                "email": full_user["email"],
                "full_name": full_user["full_name"],
                "avatar_url": full_user.get("avatar_url"),
                "bio": full_user.get("bio"),
                "settings": full_user.get("settings", {})
            },
            "access_token": token,
            "token_type": "bearer"
        }

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        clean_email = email.strip().lower()
        user = get_user_by_email(clean_email)
        # Even if user doesn't exist, we don't leak user enumeration in production
        if not user:
            return {
                "status": "success",
                "message": "If this email is registered, password reset instructions have been dispatched.",
                "reset_token": None
            }

        reset_token = secrets.token_urlsafe(32)
        set_password_reset_token(clean_email, reset_token, expires_minutes=30)

        return {
            "status": "success",
            "message": "Password reset token generated successfully. (In production, sent via email).",
            "reset_token": reset_token
        }

    def reset_password(self, token: str, new_password: str) -> bool:
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long.")
        new_pwd_hash = self.hash_password(new_password)
        success = verify_and_consume_reset_token(token, new_pwd_hash)
        if not success:
            raise ValueError("Invalid or expired password reset token.")
        return True

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        user = get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if not self.verify_password(old_password, user["password_hash"]):
            raise ValueError("Incorrect current password.")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters.")
        
        new_hash = self.hash_password(new_password)
        return update_password(user_id, new_hash)

auth_service = AuthService()
