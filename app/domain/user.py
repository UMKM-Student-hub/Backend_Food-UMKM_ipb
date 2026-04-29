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

    def validate(self) -> None:
        """Memvalidasi aturan bisnis untuk User (US-A01)."""
        if not self.is_valid_email(self.email):
            raise BusinessRuleViolationError("Format email tidak valid.")
        if len(self.name) < 3:
            raise BusinessRuleViolationError("Nama pengguna minimal 3 karakter.")

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Pengecekan Regex untuk format email."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))

    def has_role(self, expected_role: UserRole) -> bool:
        return self.role == expected_role