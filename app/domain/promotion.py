from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional
from decimal import Decimal
from app.core.exceptions import BusinessRuleViolationError

class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    NOMINAL = "NOMINAL"

@dataclass
class Promotion:
    umkm_id: int
    menu_item_id: int
    name: str
    discount_type: DiscountType
    discount_value: Decimal
    start_date: date
    end_date: date
    is_active: bool = True
    id: Optional[int] = None

    def validate(self) -> None:
        """Memvalidasi aturan bisnis promosi (US-P03)."""
        if self.end_date < self.start_date:
            raise BusinessRuleViolationError("Tanggal berakhir tidak boleh lebih awal dari tanggal mulai.")
        if self.discount_value <= 0:
            raise BusinessRuleViolationError("Nilai diskon harus lebih dari 0.")
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value >= 100:
            raise BusinessRuleViolationError("Diskon persentase harus di bawah 100%.")

    def is_expired(self, current_date: date) -> bool:
        """Mengecek apakah promo sudah kedaluwarsa."""
        return current_date > self.end_date

    def is_currently_active(self, current_date: date) -> bool:
        """Mengecek apakah promo sedang berjalan dan aktif."""
        return self.is_active and self.start_date <= current_date <= self.end_date

    def deactivate(self) -> None:
        """Menonaktifkan promo secara manual (US-P04)."""
        self.is_active = False
        
    def calculate_discounted_price(self, original_price: Decimal) -> Decimal:
        """Menghitung harga setelah diskon (persentase atau nominal)."""
        if self.discount_type == DiscountType.PERCENTAGE:
            discount_amount = original_price * (self.discount_value / Decimal('100'))
            final_price = original_price - discount_amount
        else:
            final_price = original_price - self.discount_value
            
        return max(Decimal('0'), final_price)