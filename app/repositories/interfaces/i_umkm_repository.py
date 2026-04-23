from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.umkm import UMKM

class IUMKMRepository(ABC):
    @abstractmethod
    async def find_by_id(self, umkm_id: int) -> Optional[UMKM]:
        pass

    @abstractmethod
    async def find_by_owner(self, owner_id: int) -> Optional[UMKM]:
        pass

    @abstractmethod
    async def save(self, umkm: UMKM) -> UMKM:
        pass

    @abstractmethod
    async def update(self, umkm: UMKM) -> UMKM:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[UMKM]:
        pass