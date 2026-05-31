from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from app.core.exceptions import BusinessRuleViolationError

try:
    import pytz
    _WIB = pytz.timezone("Asia/Jakarta")
    def _now_wib() -> datetime:
        return datetime.now(_WIB)
except ImportError:
    from datetime import timezone, timedelta
    _WIB = timezone(timedelta(hours=7))
    def _now_wib() -> datetime:
        return datetime.now(_WIB)

@dataclass
class UMKM:
    owner_id: int
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    operating_hours: Optional[dict] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    @property
    def is_open(self) -> bool:
        """
        Hitung apakah kantin buka SEKARANG berdasarkan jadwal operating_hours.
        Timezone: WIB (Asia/Jakarta, UTC+7).
        """
        if not self.operating_hours:
            return False

        now = _now_wib()
        day_name = now.strftime("%A").lower()
        day_schedule = self.operating_hours.get(day_name)

        if not day_schedule or not day_schedule.get("is_active", False):
            return False

        open_str = day_schedule.get("open")
        close_str = day_schedule.get("close")
        if not open_str or not close_str:
            return False

        try:
            open_h, open_m = map(int, open_str.split(":"))
            close_h, close_m = map(int, close_str.split(":"))
            current_mins = now.hour * 60 + now.minute
            open_mins = open_h * 60 + open_m
            close_mins = close_h * 60 + close_m
            return open_mins <= current_mins < close_mins
        except (ValueError, AttributeError):
            return False

    def can_accept_order(self) -> bool:
        """Mengecek apakah toko bisa menerima pesanan (otomatis dari jadwal)."""
        return self.is_open

    def is_owned_by(self, user_id: int) -> bool:
        return self.owner_id == user_id