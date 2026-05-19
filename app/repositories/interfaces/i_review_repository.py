from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.review import Review

class IReviewRepository(ABC):
    @abstractmethod
    async def save(self, review: Review) -> Review:
        pass

    @abstractmethod
    async def exists_by_order_item(self, order_id: int, menu_item_id: int) -> bool:
        pass

    @abstractmethod
    async def find_by_menu_item(self, menu_item_id: int) -> List[Review]:
        pass

    @abstractmethod
    async def find_by_umkm(self, umkm_id: int) -> List[Review]:
        pass

    @abstractmethod
    async def calculate_average_rating(self, menu_item_id: int) -> float:
        pass