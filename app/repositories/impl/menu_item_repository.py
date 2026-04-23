from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.domain.menu_item import MenuItem
from app.orm_models.menu_item import MenuItemORM

class MenuItemRepositoryImpl(IMenuItemRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: MenuItemORM) -> MenuItem:
        return MenuItem(
            id=orm.id,
            umkm_id=orm.umkm_id,
            name=orm.name,
            description=orm.description,
            price=orm.price,
            stock=orm.stock,
            photo_url=orm.photo_url,
            category=orm.category,
            is_active=orm.is_active,
            created_at=orm.created_at
        )

    async def find_by_id(self, item_id: int) -> Optional[MenuItem]:
        result = await self.session.execute(select(MenuItemORM).where(MenuItemORM.id == item_id))
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def find_by_umkm(self, umkm_id: int) -> List[MenuItem]:
        # Hanya kembalikan produk yang aktif (sesuai dokumen C.1 poin 3 - Soft Delete)
        stmt = select(MenuItemORM).where(MenuItemORM.umkm_id == umkm_id, MenuItemORM.is_active == True)
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def search(self, keyword: Optional[str] = None, category: Optional[str] = None) -> List[MenuItem]:
        stmt = select(MenuItemORM).where(MenuItemORM.is_active == True)
        
        if keyword:
            stmt = stmt.where(MenuItemORM.name.ilike(f"%{keyword}%"))
        if category:
            stmt = stmt.where(MenuItemORM.category.ilike(f"%{category}%"))
            
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def save(self, item: MenuItem) -> MenuItem:
        new_orm = MenuItemORM(
            umkm_id=item.umkm_id,
            name=item.name,
            description=item.description,
            price=item.price,
            stock=item.stock,
            photo_url=item.photo_url,
            category=item.category,
            is_active=item.is_active
        )
        self.session.add(new_orm)
        await self.session.commit()
        await self.session.refresh(new_orm)
        return self._to_domain(new_orm)

    async def update(self, item: MenuItem) -> MenuItem:
        result = await self.session.execute(select(MenuItemORM).where(MenuItemORM.id == item.id))
        orm = result.scalar_one()
        
        orm.name = item.name
        orm.description = item.description
        orm.price = item.price
        orm.stock = item.stock
        orm.photo_url = item.photo_url
        orm.category = item.category
        orm.is_active = item.is_active
        
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)