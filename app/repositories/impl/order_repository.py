from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.repositories.interfaces.i_order_repository import IOrderRepository
from app.domain.order import Order, OrderItem, OrderStatus
from app.orm_models.order import OrderORM, OrderItemORM

class OrderRepositoryImpl(IOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, orm: OrderORM) -> Order:
        domain_items = []
        if hasattr(orm, 'items') and orm.items is not None:
            for item_orm in orm.items:
                domain_items.append(OrderItem(
                    id=item_orm.id,
                    menu_item_id=item_orm.menu_item_id,
                    menu_name=item_orm.menu_name,
                    unit_price=item_orm.unit_price,
                    quantity=item_orm.quantity,
                    notes=item_orm.notes or ""
                ))
        
        return Order(
            id=orm.id,
            buyer_id=orm.buyer_id,
            umkm_id=orm.umkm_id,
            notes=orm.notes,
            status=OrderStatus(orm.status),
            pickup_schedule=orm.pickup_schedule,
            queue_number=orm.queue_number,
            total_price=orm.total_price,
            payment_method=orm.payment_method,
            payment_proof_url=orm.payment_proof_url,
            created_at=orm.created_at,
            items=domain_items
        )

    async def save(self, order: Order) -> Order:
        new_order_orm = OrderORM(
            buyer_id=order.buyer_id,
            umkm_id=order.umkm_id,
            notes=order.notes,
            status=order.status.value,
            pickup_schedule=order.pickup_schedule,
            total_price=order.total_price,
            payment_method=order.payment_method,
            payment_proof_url=order.payment_proof_url
        )
        self.session.add(new_order_orm)
        await self.session.flush()

        for item in order.items:
            item_orm = OrderItemORM(
                order_id=new_order_orm.id,
                menu_item_id=item.menu_item_id,
                menu_name=item.menu_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                notes=item.notes
            )
            self.session.add(item_orm)

        await self.session.commit()
        return await self.find_by_id(new_order_orm.id)

    async def find_by_id(self, order_id: int) -> Optional[Order]:
        stmt = select(OrderORM).options(selectinload(OrderORM.items)).where(OrderORM.id == order_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def find_by_buyer(self, buyer_id: int) -> List[Order]:
        stmt = select(OrderORM).options(selectinload(OrderORM.items)).where(OrderORM.buyer_id == buyer_id).order_by(OrderORM.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def find_by_umkm(self, umkm_id: int) -> List[Order]:
        stmt = select(OrderORM).options(selectinload(OrderORM.items)).where(OrderORM.umkm_id == umkm_id).order_by(OrderORM.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def update_status(self, order: Order) -> Order:
        stmt = select(OrderORM).where(OrderORM.id == order.id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one()
        
        orm.status = order.status.value
        orm.rejection_reason = order.rejection_reason
        
        await self.session.commit()
        return await self.find_by_id(orm.id)