from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.domain.order import OrderStatus

class OrderItemRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = ""

class OrderCreateRequest(BaseModel):
    umkm_id: int
    items: List[OrderItemRequest]
    notes: Optional[str] = ""
    pickup_schedule: datetime

class OrderItemResponse(BaseModel):
    menu_item_id: int
    menu_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    notes: str

    @staticmethod
    def from_domain(item) -> "OrderItemResponse":
        return OrderItemResponse(
            menu_item_id=item.menu_item_id,
            menu_name=item.menu_name,
            unit_price=item.unit_price,
            quantity=item.quantity,
            subtotal=item.calculate_subtotal(),
            notes=item.notes or ""
        )

class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    umkm_id: int
    status: OrderStatus
    total_price: Decimal
    payment_method: str
    payment_proof_url: Optional[str]
    items: List[OrderItemResponse]
    notes: str
    pickup_schedule: Optional[datetime]
    queue_number: Optional[str]
    rejection_reason: Optional[str]
    created_at: datetime

    @staticmethod
    def from_domain(order) -> "OrderResponse":
        return OrderResponse(
            id=order.id,
            buyer_id=order.buyer_id,
            umkm_id=order.umkm_id,
            status=order.status,
            total_price=order.total_price,
            payment_method=order.payment_method,
            payment_proof_url=order.payment_proof_url,
            items=[OrderItemResponse.from_domain(item) for item in order.items],
            notes=order.notes,
            pickup_schedule=order.pickup_schedule,
            queue_number=order.queue_number,
            rejection_reason=order.rejection_reason,
            created_at=order.created_at
        )