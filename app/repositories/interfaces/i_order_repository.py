from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.order import Order

class IOrderRepository(ABC):
    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Menyimpan pesanan baru beserta detail itemnya."""
        pass

    @abstractmethod
    async def find_by_id(self, order_id: int) -> Optional[Order]:
        """Mencari pesanan spesifik berdasarkan ID."""
        pass

    @abstractmethod
    async def find_by_buyer(self, buyer_id: int) -> List[Order]:
        """Melihat riwayat pesanan milik pembeli tertentu."""
        pass

    @abstractmethod
    async def find_by_umkm(self, umkm_id: int) -> List[Order]:
        """Melihat daftar pesanan masuk untuk UMKM tertentu."""
        pass

    @abstractmethod
    async def update_status(self, order: Order) -> Order:
        """Memperbarui status pesanan (Confirm, Reject, Ready, Done)."""
        pass