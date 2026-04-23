from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.domain.user import User, UserRole

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    role: UserRole

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    created_at: datetime

    @staticmethod
    def from_domain(user: User) -> "UserResponse":
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            created_at=user.created_at
        )