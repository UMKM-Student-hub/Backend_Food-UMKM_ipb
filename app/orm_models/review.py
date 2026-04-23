from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, SmallInteger
from sqlalchemy.sql import func
from app.core.database import Base

class ReviewORM(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False, index=True)
    rating = Column(SmallInteger, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)