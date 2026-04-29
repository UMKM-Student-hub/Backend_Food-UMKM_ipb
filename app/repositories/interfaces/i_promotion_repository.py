from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.promotion import Promotion

class IPromotionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, promo_id: int) -> Optional[Promotion]: pass

    @abstractmethod
    async def find_active(self) -> List[Promotion]: pass

    @abstractmethod
    async def find_by_umkm(self, umkm_id: int) -> List[Promotion]: pass

    @abstractmethod
    async def save(self, promo: Promotion) -> Promotion: pass

    @abstractmethod
    async def update(self, promo: Promotion) -> Promotion: pass