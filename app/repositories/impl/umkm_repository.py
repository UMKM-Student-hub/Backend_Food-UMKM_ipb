import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.umkm import UMKM
from app.orm_models.umkm import UMKMORM

class UMKMRepositoryImpl(IUMKMRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: UMKMORM) -> UMKM:
        """Parse operating_hours dari TEXT (JSON) → dict."""
        operating_hours = None
        if orm.operating_hours:
            try:
                operating_hours = json.loads(orm.operating_hours)
            except json.JSONDecodeError:
                operating_hours = None

        return UMKM(
            id=orm.id,
            owner_id=orm.owner_id,
            name=orm.name,
            description=orm.description,
            location=orm.location,
            operating_hours=operating_hours,
            created_at=orm.created_at,
        )

    def _serialize_hours(self, operating_hours: Optional[dict]) -> Optional[str]:
        """Encode dict → JSON string untuk disimpan ke DB."""
        if operating_hours is None:
            return None
        return json.dumps(operating_hours, ensure_ascii=False)

    async def find_by_id(self, umkm_id: int) -> Optional[UMKM]:
        result = await self.session.execute(
            select(UMKMORM).where(UMKMORM.id == umkm_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def find_by_owner(self, owner_id: int) -> Optional[UMKM]:
        result = await self.session.execute(
            select(UMKMORM).where(UMKMORM.owner_id == owner_id)
        )
        orm = result.scalars().first()
        return self._to_domain(orm) if orm else None

    async def find_all(self) -> List[UMKM]:
        result = await self.session.execute(select(UMKMORM))
        return [self._to_domain(orm) for orm in result.scalars()]

    async def save(self, umkm: UMKM) -> UMKM:
        new_orm = UMKMORM(
            owner_id=umkm.owner_id,
            name=umkm.name,
            description=umkm.description,
            location=umkm.location,
            operating_hours=self._serialize_hours(umkm.operating_hours),
        )
        self.session.add(new_orm)
        await self.session.commit()
        await self.session.refresh(new_orm)
        return self._to_domain(new_orm)

    async def update(self, umkm: UMKM) -> UMKM:
        result = await self.session.execute(
            select(UMKMORM).where(UMKMORM.id == umkm.id)
        )
        orm = result.scalar_one_or_none()
        if not orm:
            return umkm

        orm.name = umkm.name
        orm.description = umkm.description
        orm.location = umkm.location
        orm.operating_hours = self._serialize_hours(umkm.operating_hours)

        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)