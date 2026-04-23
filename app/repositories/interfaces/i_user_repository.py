from abc import ABC, abstractmethod
from typing import Optional
from app.domain.user import User

class IUserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass