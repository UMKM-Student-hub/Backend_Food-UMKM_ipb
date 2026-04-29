from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.order_schema import OrderCreateRequest, OrderResponse
from app.services.order_service import OrderService
from app.repositories.impl.order_repository import OrderRepositoryImpl
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    """Menginisialisasi OrderService dengan semua repository yang dibutuhkan."""
    order_repo = OrderRepositoryImpl(db)
    menu_repo = MenuItemRepositoryImpl(db)
    umkm_repo = UMKMRepositoryImpl(db)
    promo_repo = PromotionRepositoryImpl(db)
    return OrderService(order_repo, menu_repo, umkm_repo, promo_repo)

def get_current_user_id(x_user_id: int = Header(..., description="Simulasi User ID yang sedang login")) -> int:
    """Dependency untuk mengambil User ID dari Header secara tersentralisasi."""
    return x_user_id

@router.post("/", response_model=OrderResponse)
async def create_order(
    request: OrderCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Pembeli membuat pesanan pre-order baru."""
    order = await service.place_order(buyer_id=current_user_id, request=request)
    return OrderResponse.from_domain(order)

@router.get("/my", response_model=List[OrderResponse])
async def get_my_orders(
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Pembeli melihat riwayat semua pesanannya."""
    orders = await service.get_buyer_orders(buyer_id=current_user_id)
    return [OrderResponse.from_domain(o) for o in orders]

@router.patch("/{order_id}/done", response_model=OrderResponse)
async def mark_order_done(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Pembeli menandai bahwa pesanan sudah diambil dan selesai."""
    order = await service.mark_order_done(order_id=order_id, buyer_id=current_user_id)
    return OrderResponse.from_domain(order)

@router.get("/incoming", response_model=List[OrderResponse])
async def get_incoming_orders(
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Penjual melihat daftar pesanan masuk ke tokonya."""
    orders = await service.get_umkm_orders(owner_id=current_user_id)
    return [OrderResponse.from_domain(o) for o in orders]

@router.patch("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Penjual mengkonfirmasi pesanan pembeli."""
    order = await service.confirm_order(order_id=order_id, owner_id=current_user_id)
    return OrderResponse.from_domain(order)

@router.patch("/{order_id}/reject", response_model=OrderResponse)
async def reject_order(
    order_id: int,
    reason: str = Query(..., min_length=5, description="Alasan penolakan wajib diisi"),
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Penjual menolak pesanan pembeli dengan alasan tertentu."""
    order = await service.reject_order(order_id=order_id, owner_id=current_user_id, reason=reason)
    return OrderResponse.from_domain(order)

@router.patch("/{order_id}/ready", response_model=OrderResponse)
async def mark_order_ready(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service)
):
    """Penjual menandai pesanan telah siap untuk diambil."""
    order = await service.mark_order_ready(order_id=order_id, owner_id=current_user_id)
    return OrderResponse.from_domain(order)