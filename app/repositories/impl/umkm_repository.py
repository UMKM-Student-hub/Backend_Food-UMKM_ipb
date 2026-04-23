from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.umkm import UMKM
from app.orm_models.umkm import UMKMORM

class UMKMRepositoryImpl(IUMKMRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: UMKMORM) -> UMKM:
        return UMKM(
            id=orm.id,
            owner_id=orm.owner_id,
            name=orm.name,
            description=orm.description,
            location=orm.location,
            is_open=orm.is_open,
            created_at=orm.created_at
        )

    async def find_by_id(self, umkm_id: int) -> Optional[UMKM]:
        result = await self.session.execute(select(UMKMORM).where(UMKMORM.id == umkm_id))
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def find_by_owner(self, owner_id: int) -> Optional[UMKM]:
        result = await self.session.execute(select(UMKMORM).where(UMKMORM.owner_id == owner_id))
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, umkm: UMKM) -> UMKM:
        new_orm = UMKMORM(
            owner_id=umkm.owner_id,
            name=umkm.name,
            description=umkm.description,
            location=umkm.location,
            is_open=umkm.is_open
        )
        self.session.add(new_orm)
        await self.session.commit()
        await self.session.refresh(new_orm)
        return self._to_domain(new_orm)

    async def update(self, umkm: UMKM) -> UMKM:
        result = await self.session.execute(select(UMKMORM).where(UMKMORM.id == umkm.id))
        orm = result.scalar_one()
        
        orm.name = umkm.name
        orm.description = umkm.description
        orm.location = umkm.location
        orm.is_open = umkm.is_open
        
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def find_all(self) -> List[UMKM]:
        result = await self.session.execute(select(UMKMORM))
        return [self._to_domain(orm) for orm in result.scalars().all()]