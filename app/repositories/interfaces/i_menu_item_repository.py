from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.menu_item import MenuItem

class IMenuItemRepository(ABC):
    @abstractmethod
    async def find_by_id(self, item_id: int) -> Optional[MenuItem]:
        pass

    @abstractmethod
    async def find_by_umkm(self, umkm_id: int) -> List[MenuItem]:
        pass

    @abstractmethod
    async def search(self, keyword: Optional[str] = None, category: Optional[str] = None) -> List[MenuItem]:
        pass

    @abstractmethod
    async def save(self, item: MenuItem) -> MenuItem:
        pass

    @abstractmethod
    async def update(self, item: MenuItem) -> MenuItem:
        pass