from pydantic import BaseModel, Field, validator
from typing import Optional, Dict

class DayScheduleUpdate(BaseModel):
    is_active: bool = False
    open: Optional[str] = None
    close: Optional[str] = None

    @validator("open", "close", pre=True, always=True)
    def validate_time_format(cls, v, values):
        if v is None:
            return v
        try:
            parts = v.split(":")
            assert len(parts) == 2
            h, m = int(parts[0]), int(parts[1])
            assert 0 <= h <= 23
            assert 0 <= m <= 59
        except (AssertionError, ValueError):
            raise ValueError("Format jam harus HH:MM (contoh: 08:00 atau 17:30)")
        return v

    @validator("close", always=True)
    def close_after_open(cls, close_v, values):
        open_v = values.get("open")
        if values.get("is_active") and open_v and close_v:
            oh, om = map(int, open_v.split(":"))
            ch, cm = map(int, close_v.split(":"))
            if (ch * 60 + cm) <= (oh * 60 + om):
                raise ValueError("Jam tutup harus setelah jam buka")
        return close_v

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

class OperatingHoursUpdate(BaseModel):
    monday:    DayScheduleUpdate
    tuesday:   DayScheduleUpdate
    wednesday: DayScheduleUpdate
    thursday:  DayScheduleUpdate
    friday:    DayScheduleUpdate
    saturday:  DayScheduleUpdate
    sunday:    DayScheduleUpdate

    def to_dict(self) -> dict:
        return {day: getattr(self, day).dict() for day in DAYS}

class UMKMCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    location: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None


class UMKMResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    location: str
    description: Optional[str]
    is_open: bool
    operating_hours: Optional[dict]

    @staticmethod
    def from_domain(umkm) -> "UMKMResponse":
        return UMKMResponse(
            id=umkm.id,
            owner_id=umkm.owner_id,
            name=umkm.name,
            location=umkm.location,
            description=umkm.description,
            is_open=umkm.is_open,
            operating_hours=umkm.operating_hours,
        )