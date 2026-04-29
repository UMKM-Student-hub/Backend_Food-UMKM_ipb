from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, func
from app.repositories.interfaces.i_review_repository import IReviewRepository
from app.domain.review import Review
from app.orm_models.review import ReviewORM
from app.orm_models.menu_item import MenuItemORM

class ReviewRepositoryImpl(IReviewRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: ReviewORM) -> Review:
        return Review(
            id=orm.id,
            order_id=orm.order_id,
            buyer_id=orm.buyer_id,
            menu_item_id=orm.menu_item_id,
            rating=orm.rating,
            comment=orm.comment,
            created_at=orm.created_at
        )

    async def save(self, review: Review) -> Review:
        orm = ReviewORM(
            order_id=review.order_id,
            buyer_id=review.buyer_id,
            menu_item_id=review.menu_item_id,
            rating=review.rating,
            comment=review.comment
        )
        self.session.add(orm)
        await self.session.commit() 
        
        await self.session.refresh(orm) 
        
        return self._to_domain(orm)

    async def exists_by_order_id(self, order_id: int) -> bool:
        """Mengecek apakah pesanan ini sudah pernah diulas."""
        stmt = select(exists().where(ReviewORM.order_id == order_id))
        result = await self.session.execute(stmt)
        return result.scalar()

    async def find_by_menu_item(self, menu_item_id: int) -> List[Review]:
        """US-R02: Mengambil ulasan per produk, diurutkan dari yang terbaru."""
        stmt = select(ReviewORM).where(ReviewORM.menu_item_id == menu_item_id).order_by(ReviewORM.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]

    async def find_by_umkm(self, umkm_id: int) -> List[Review]:
        """US-R03: Mengambil ulasan per UMKM menggunakan operasi JOIN."""
        stmt = (
            select(ReviewORM)
            .join(MenuItemORM, ReviewORM.menu_item_id == MenuItemORM.id)
            .where(MenuItemORM.umkm_id == umkm_id)
            .order_by(ReviewORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]
    
    async def calculate_average_rating(self, menu_item_id: int) -> float:
        """Menghitung rata-rata rating produk langsung di level database."""
        stmt = select(func.avg(ReviewORM.rating)).where(ReviewORM.menu_item_id == menu_item_id)
        result = await self.session.execute(stmt)
        average = result.scalar()
        return float(average) if average else 0.0