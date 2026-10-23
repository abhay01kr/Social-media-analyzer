from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, example="Jane Doe")
    email: str = Field(..., example="jane.doe@example.com")
    password: str = Field(..., min_length=6, example="password123")

class LoginRequest(BaseModel):
    email: str = Field(..., example="jane.doe@example.com")
    password: str = Field(..., min_length=1, example="password123")

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

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: str
