from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from services.auth_service import auth_service
from database.auth_db import get_user_by_id, update_user_profile

router = APIRouter(tags=["Authentication & User Management"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

# Schemas
class SignupRequest(BaseModel):
    full_name: str = Field(..., example="Jane Doe")
    email: str = Field(..., example="jane.doe@example.com")
    password: str = Field(..., min_length=6, example="password123")

class LoginRequest(BaseModel):
    email: str = Field(..., example="jane.doe@example.com")
    password: str = Field(..., example="password123")

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., example="jane.doe@example.com")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., example="reset-token-here")
    new_password: str = Field(..., min_length=6, example="newSecretPass123")

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., example="currentPass123")
    new_password: str = Field(..., min_length=6, example="newSecretPass123")

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

# JWT Dependency
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = auth_service.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload["sub"]
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    # Remove password_hash from returned object
    user.pop("password_hash", None)
    return user

# ==================== ENDPOINTS (Member 1) ====================

@router.post("/signup", status_code=status.HTTP_201_CREATED)
@router.post("/api/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    """Register a new user account with hashed password and return access token."""
    try:
        result = auth_service.register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name
        )
        return {
            "status": "success",
            "message": "User registered successfully.",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration error: {str(e)}")

@router.post("/login")
@router.post("/api/login")
def login(payload: LoginRequest):
    """Authenticate user with email and password, returning JWT access token."""
    try:
        result = auth_service.authenticate_user(
            email=payload.email,
            password=payload.password
        )
        return {
            "status": "success",
            "message": "Login successful.",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login error: {str(e)}")

@router.get("/profile")
@router.get("/api/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    """Fetch profile of currently authenticated user via JWT."""
    return {
        "status": "success",
        "user": current_user
    }

@router.put("/profile")
@router.put("/api/profile")
def update_profile(payload: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update profile details (name, bio, avatar, user preferences)."""
    updated = update_user_profile(
        user_id=current_user["id"],
        full_name=payload.full_name,
        bio=payload.bio,
        avatar_url=payload.avatar_url,
        settings=payload.settings
    )
    if updated:
        updated.pop("password_hash", None)
    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "user": updated
    }

@router.post("/forgot-password")
@router.post("/api/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    """Request password reset link/token."""
    result = auth_service.request_password_reset(payload.email)
    return result

@router.post("/reset-password")
@router.post("/api/reset-password")
def reset_password(payload: ResetPasswordRequest):
    """Consume reset token and update to new password."""
    try:
        auth_service.reset_password(payload.token, payload.new_password)
        return {
            "status": "success",
            "message": "Password has been successfully reset. You may now log in with your new password."
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/change-password")
@router.post("/api/change-password")
def change_password(payload: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Allow logged in user to change password by verifying old password."""
    try:
        auth_service.change_password(current_user["id"], payload.old_password, payload.new_password)
        return {
            "status": "success",
            "message": "Password changed successfully."
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
