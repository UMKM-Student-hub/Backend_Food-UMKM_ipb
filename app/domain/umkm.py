from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from app.core.exceptions import BusinessRuleViolationError

@dataclass
class UMKM:
    owner_id: int
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    is_open: bool = False
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def can_accept_order(self) -> bool:
        """Mengecek apakah toko bisa menerima pesanan."""
        return self.is_open

    def open_store(self) -> None:
        """Membuka toko dengan guard validation."""
        if self.is_open:
            raise BusinessRuleViolationError("Toko sudah BUKA.")
        self.is_open = True

    def close_store(self) -> None:
        """Menutup toko."""
        if not self.is_open:
            raise BusinessRuleViolationError("Toko sudah TUTUP.")
        self.is_open = False

    def is_owned_by(self, user_id: int) -> bool:
        """Memvalidasi kepemilikan toko."""
        return self.owner_id == user_id