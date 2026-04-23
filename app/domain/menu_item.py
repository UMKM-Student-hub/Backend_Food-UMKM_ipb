from dataclasses import dataclass
from typing import Optional
from enum import Enum
from decimal import Decimal
from datetime import datetime
from app.core.exceptions import BusinessRuleViolationError

class ProductCategory(str, Enum):
    MAKANAN = "MAKANAN"
    MINUMAN = "MINUMAN"
    JAJANAN = "JAJANAN"

@dataclass
class MenuItem:
    umkm_id: int
    name: str
    price: Decimal
    stock: int
    category: ProductCategory
    description: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def is_available(self, required_qty: int = 1) -> bool:
        """Mengecek apakah produk aktif dan stoknya mencukupi."""
        return self.is_active and self.stock >= required_qty

    def reduce_stock(self, qty: int) -> None:
        """Mengurangi stok saat ada pesanan masuk."""
        if qty <= 0:
            raise BusinessRuleViolationError("Jumlah pesanan harus lebih dari 0.")
        if not self.is_available(qty):
            raise BusinessRuleViolationError(f"Stok '{self.name}' tidak mencukupi. Sisa stok: {self.stock}")
        self.stock -= qty

    def restore_stock(self, qty: int) -> None:
        """Mengembalikan stok jika pesanan dibatalkan/ditolak."""
        if qty > 0:
            self.stock += qty

    def deactivate_product(self) -> None:
        """Soft delete produk agar tidak bisa dipesan lagi."""
        self.is_active = False
        
    def activate_product(self) -> None:
        """Mengaktifkan kembali produk."""
        self.is_active = True