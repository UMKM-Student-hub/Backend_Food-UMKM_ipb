from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.domain.umkm import UMKM

class UMKMCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None

class UMKMResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    is_open: bool
    created_at: datetime

    @staticmethod
    def from_domain(umkm: UMKM) -> "UMKMResponse":
        return UMKMResponse(
            id=umkm.id,
            owner_id=umkm.owner_id,
            name=umkm.name,
            description=umkm.description,
            location=umkm.location,
            is_open=umkm.is_open,
            created_at=umkm.created_at
        )