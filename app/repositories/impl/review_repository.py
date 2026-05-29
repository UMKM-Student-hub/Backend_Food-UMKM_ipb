from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, func
from app.repositories.interfaces.i_review_repository import IReviewRepository
from app.domain.review import Review
from app.orm_models.review import ReviewORM
from app.orm_models.menu_item import MenuItemORM
from app.orm_models.user import UserORM

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

    async def exists_by_order_item(self, order_id: int, menu_item_id: int) -> bool:
        stmt = select(exists().where(ReviewORM.order_id == order_id).where(ReviewORM.menu_item_id == menu_item_id))
        result = await self.session.execute(stmt)
        return bool(result.scalar())

    async def find_by_menu_item(self, menu_item_id: int) -> List[Review]:
        stmt = select(ReviewORM).where(ReviewORM.menu_item_id == menu_item_id).order_by(ReviewORM.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]

    async def find_by_umkm(self, umkm_id: int) -> List[Review]:
        stmt = (
            select(ReviewORM, UserORM.name, MenuItemORM.name)
            .join(UserORM, ReviewORM.buyer_id == UserORM.id)
            .join(MenuItemORM, ReviewORM.menu_item_id == MenuItemORM.id)
            .where(MenuItemORM.umkm_id == umkm_id)
            .order_by(ReviewORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        
        domain_reviews = []
        for row in result.all():
            orm = row[0]
            domain_review = self._to_domain(orm)
            setattr(domain_review, 'buyer_name', row[1])
            setattr(domain_review, 'menu_name', row[2])
            domain_reviews.append(domain_review)
            
        return domain_reviews
    
    async def calculate_average_rating(self, menu_item_id: int) -> float:
        stmt = select(func.avg(ReviewORM.rating)).where(ReviewORM.menu_item_id == menu_item_id)
        result = await self.session.execute(stmt)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    async def find_by_buyer(self, buyer_id: int) -> List[Review]:
        stmt = select(ReviewORM).where(ReviewORM.buyer_id == buyer_id).order_by(ReviewORM.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars()]