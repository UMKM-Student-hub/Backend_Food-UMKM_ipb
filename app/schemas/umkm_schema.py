from pydantic import BaseModel, Field
from typing import Optional

class UMKMCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    location: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None

class UMKMStatusUpdate(BaseModel):
    is_open: bool

class UMKMResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    location: str
    description: Optional[str]
    is_open: bool

    @staticmethod
    def from_domain(umkm) -> "UMKMResponse":
        return UMKMResponse(
            id=umkm.id,
            owner_id=umkm.owner_id,
            name=umkm.name,
            location=umkm.location,
            description=umkm.description,
            is_open=bool(getattr(umkm, 'is_open', False))
        )