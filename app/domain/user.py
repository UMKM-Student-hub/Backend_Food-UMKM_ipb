from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum
import re
from app.core.exceptions import BusinessRuleViolationError

class UserRole(str, Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"

@dataclass
class User:
    name: str
    email: str
    password_hash: str
    role: UserRole
    phone: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def is_valid_email(self) -> bool:
        """Memvalidasi format email dasar."""
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, self.email) is not None

    def has_role(self, target_role: UserRole) -> bool:
        """Mengecek apakah user memiliki role tertentu."""
        return self.role == target_role

    def validate_before_save(self) -> None:
        if not self.is_valid_email():
            raise BusinessRuleViolationError("Format email tidak valid.")