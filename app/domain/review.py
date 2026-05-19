from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from app.core.exceptions import BusinessRuleViolationError

@dataclass
class Review:
    order_id: int
    buyer_id: int
    menu_item_id: int
    rating: int
    comment: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def validate(self) -> None:
        if not (1 <= self.rating <= 5):
            raise BusinessRuleViolationError("Rating wajib diisi dengan nilai antara 1 hingga 5.")
        
        if self.comment and len(self.comment) > 500:
            raise BusinessRuleViolationError("Komentar ulasan terlalu panjang (maksimal 500 karakter).")