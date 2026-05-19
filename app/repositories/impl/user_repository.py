from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.repositories.interfaces.i_user_repository import IUserRepository
from app.domain.user import User, UserRole
from app.orm_models.user import UserORM

class UserRepositoryImpl(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: UserORM) -> User:
        return User(
            id=orm.id,
            name=orm.name,
            email=orm.email,
            password_hash=orm.password_hash,
            phone=orm.phone,
            role=UserRole(orm.role),
            created_at=orm.created_at
        )

    async def find_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none() 
        return self._to_domain(orm) if orm else None

    async def find_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserORM).where(UserORM.email == email)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none() 
        return self._to_domain(orm) if orm else None
    
    async def save(self, user: User) -> User:
        new_orm = UserORM(
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
            phone=user.phone,
            role=user.role.value
        )
        self.session.add(new_orm)
        await self.session.commit()
        await self.session.refresh(new_orm)
        return self._to_domain(new_orm)

    async def update(self, user: User) -> User:
        stmt = select(UserORM).where(UserORM.id == user.id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()

        if orm:
            orm.name = user.name
            orm.phone = user.phone
            await self.session.commit()
            await self.session.refresh(orm)
            return self._to_domain(orm)
            
        return user