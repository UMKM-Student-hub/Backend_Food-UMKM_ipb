from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from app.domain.menu_item import ProductCategory
from datetime import datetime
from app.domain.menu_item import MenuItem

class MenuItemCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, description="Harga harus lebih besar dari 0")
    stock: int = Field(default=0, ge=0, description="Stok tidak boleh minus")
    category: ProductCategory
    photo_url: Optional[str] = None
    category: Optional[str] = None

class MenuItemResponse(BaseModel):
    id: int
    umkm_id: int
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    photo_url: Optional[str]
    category: ProductCategory
    is_active: bool
    created_at: datetime

    @staticmethod
    def from_domain(item: MenuItem) -> "MenuItemResponse":
        return MenuItemResponse(
            id=item.id,
            umkm_id=item.umkm_id,
            name=item.name,
            description=item.description,
            price=item.price,
            stock=item.stock,
            photo_url=item.photo_url,
            category=item.category,
            is_active=item.is_active,
            created_at=item.created_at
        )