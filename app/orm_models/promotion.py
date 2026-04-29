from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Numeric, Enum as SQLEnum, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.domain.promotion import DiscountType

class PromotionORM(Base):
    __tablename__ = "promotions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    umkm_id: Mapped[int] = mapped_column(ForeignKey("umkm.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType), nullable=False)
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint('end_date >= start_date', name='valid_date_range'),
        CheckConstraint(
            "discount_type != 'PERCENTAGE' OR discount_value < 100", 
            name='valid_percentage'
        ),
    )