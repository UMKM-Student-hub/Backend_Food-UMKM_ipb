from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import Optional
from decimal import Decimal
from app.domain.promotion import DiscountType

class PromoCreateRequest(BaseModel):
    menu_item_id: int
    name: str = Field(..., min_length=3, max_length=100)
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def validate_dates_and_discount(self) -> 'PromoCreateRequest':
        if self.end_date < self.start_date:
            raise ValueError("Tanggal berakhir tidak boleh lebih awal dari tanggal mulai.")
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value >= 100:
            raise ValueError("Diskon persentase harus kurang dari 100%.")
        return self

class PromoResponse(BaseModel):
    id: int
    umkm_id: int
    menu_item_id: int
    name: str
    discount_type: DiscountType
    discount_value: Decimal
    start_date: date
    end_date: date
    is_active: bool

    @staticmethod
    def from_domain(promo) -> "PromoResponse":
        return PromoResponse(
            id=promo.id,
            umkm_id=promo.umkm_id,
            menu_item_id=promo.menu_item_id,
            name=promo.name,
            discount_type=promo.discount_type,
            discount_value=promo.discount_value,
            start_date=promo.start_date,
            end_date=promo.end_date,
            is_active=promo.is_active
        )