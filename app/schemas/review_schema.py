from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewCreateRequest(BaseModel):
    order_id: int = Field(..., description="ID Pesanan yang sudah selesai")
    menu_item_id: int = Field(..., description="ID Menu yang dipesan")
    rating: int = Field(..., ge=1, le=5, description="Rating bintang 1-5")
    comment: Optional[str] = Field(None, description="Komentar opsional dari pembeli")

class ReviewResponse(BaseModel):
    id: int
    order_id: int
    buyer_id: int
    menu_item_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    @staticmethod
    def from_domain(review) -> "ReviewResponse":
        return ReviewResponse(
            id=review.id,
            order_id=review.order_id,
            buyer_id=review.buyer_id,
            menu_item_id=review.menu_item_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at
        )