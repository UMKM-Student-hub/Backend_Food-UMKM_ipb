from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewCreateRequest(BaseModel):
    order_id: int = Field(..., ge=1)
    menu_item_id: int = Field(..., ge=1)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    order_id: int
    buyer_id: int
    menu_item_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    buyer_name: Optional[str] = None
    menu_name: Optional[str] = None

    @staticmethod
    def from_domain(review) -> "ReviewResponse":
        return ReviewResponse(
            id=review.id,
            order_id=review.order_id,
            buyer_id=review.buyer_id,
            menu_item_id=review.menu_item_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            buyer_name=getattr(review, 'buyer_name', None),
            menu_name=getattr(review, 'menu_name', None)
        )