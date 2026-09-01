from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full display name")
    password_hash: str = Field(..., description="Hashed password with salt")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class SignupRequest(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    full_name: str = Field(..., min_length=2, description="Candidate or Interviewer full name")

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user_id: str
    email: str
    full_name: str

class UserProfile(BaseModel):
    user_id: str
    email: str
    full_name: str
    created_at: datetime
