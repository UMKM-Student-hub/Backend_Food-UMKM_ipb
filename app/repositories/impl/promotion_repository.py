from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.repositories.interfaces.i_promotion_repository import IPromotionRepository
from app.domain.promotion import Promotion, DiscountType
from app.orm_models.promotion import PromotionORM

class PromotionRepositoryImpl(IPromotionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: PromotionORM) -> Promotion:
        return Promotion(
            id=orm.id,
            umkm_id=orm.umkm_id,
            menu_item_id=orm.menu_item_id,
            name=orm.name,
            discount_type=orm.discount_type,
            discount_value=orm.discount_value,
            start_date=orm.start_date,
            end_date=orm.end_date,
            is_active=orm.is_active
        )

    async def find_by_id(self, promo_id: int) -> Optional[Promotion]:
        stmt = select(PromotionORM).where(PromotionORM.id == promo_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_opt()
        return self._to_domain(orm) if orm else None

    async def find_active(self) -> List[Promotion]:
        """Query untuk mendapatkan promo yang sedang berlangsung hari ini."""
        today = date.today()
        stmt = select(PromotionORM).where(
            PromotionORM.is_active == True,
            PromotionORM.start_date <= today,
            PromotionORM.end_date >= today
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]
    
    async def find_active_by_menu_item(self, menu_item_id: int) -> List[Promotion]:
        today = date.today()
        stmt = select(PromotionORM).where(
            PromotionORM.menu_item_id == menu_item_id,
            PromotionORM.is_active == True,
            PromotionORM.start_date <= today,
            PromotionORM.end_date >= today
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]

    async def find_by_umkm(self, umkm_id: int) -> List[Promotion]:
        stmt = select(PromotionORM).where(PromotionORM.umkm_id == umkm_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]

    async def save(self, promo: Promotion) -> Promotion:
        orm = PromotionORM(
            umkm_id=promo.umkm_id,
            menu_item_id=promo.menu_item_id,
            name=promo.name,
            discount_type=promo.discount_type,
            discount_value=promo.discount_value,
            start_date=promo.start_date,
            end_date=promo.end_date,
            is_active=promo.is_active
        )
        self.session.add(orm)
        
        await self.session.flush()
        await self.session.commit()
        
        promo.id = orm.id
        return promo

    async def update(self, promo: Promotion) -> Promotion:
        stmt = select(PromotionORM).where(PromotionORM.id == promo.id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one()

        orm.is_active = promo.is_active
        
        await self.session.commit() 
        return promo