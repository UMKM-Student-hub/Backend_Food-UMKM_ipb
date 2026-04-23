from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum
from app.core.exceptions import BusinessRuleViolationError

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

@dataclass
class OrderItem:
    menu_item_id: int
    menu_name: str
    unit_price: Decimal
    quantity: int
    notes: str = ""
    id: Optional[int] = None

    def calculate_subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

@dataclass
class Order:
    buyer_id: int
    umkm_id: int
    total_price: Decimal
    items: List[OrderItem] = field(default_factory=list)
    notes: str = ""
    status: OrderStatus = OrderStatus.PENDING
    pickup_schedule: Optional[datetime] = None
    queue_number: Optional[str] = None
    rejection_reason: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def confirm(self) -> None:
        if self.status != OrderStatus.PENDING:
            raise BusinessRuleViolationError(f"Pesanan tidak bisa dikonfirmasi dari status {self.status}")
        self.status = OrderStatus.CONFIRMED

    def reject(self, reason: str) -> None:
        if self.status != OrderStatus.PENDING:
            raise BusinessRuleViolationError("Hanya pesanan PENDING yang bisa ditolak.")
        if not reason:
            raise BusinessRuleViolationError("Alasan penolakan wajib diisi.")
        self.status = OrderStatus.CANCELLED
        self.rejection_reason = reason

    def mark_ready(self) -> None:
        if self.status != OrderStatus.CONFIRMED:
            raise BusinessRuleViolationError("Pesanan harus dikonfirmasi terlebih dahulu sebelum siap diambil.")
        self.status = OrderStatus.READY

    def mark_done(self) -> None:
        if self.status != OrderStatus.READY:
            raise BusinessRuleViolationError("Pesanan harus siap diambil sebelum bisa ditandai selesai.")
        self.status = OrderStatus.DONE