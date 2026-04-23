from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class OrderORM(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    umkm_id = Column(Integer, ForeignKey("umkm.id"), nullable=False, index=True)
    notes = Column(Text, default="", nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    rejection_reason = Column(Text, nullable=True)
    pickup_schedule = Column(DateTime(timezone=True), nullable=True)
    queue_number = Column(String(20), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    items = relationship("OrderItemORM", cascade="all, delete-orphan")
class OrderItemORM(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    menu_name = Column(String(100), nullable=False) 
    unit_price = Column(Numeric(10, 2), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=True)