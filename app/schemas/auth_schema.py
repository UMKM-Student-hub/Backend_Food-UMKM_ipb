from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.domain.user import UserRole

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: str = Field(..., max_length=20)
    role: UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    @staticmethod
    def from_domain(user) -> "UserResponse":
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role
        )

class ProfileResponse(BaseModel):
    umkmName: str
    email: str
    ownerName: str
    phone: str
    location: str

class ProfileUpdateRequest(BaseModel):
    umkmName: Optional[str] = None
    ownerName: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None