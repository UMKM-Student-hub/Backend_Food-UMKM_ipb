from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.promo_schema import PromoCreateRequest, PromoResponse
from app.services.promo_service import PromoService
from app.core.dependencies import get_current_user_id
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl

router = APIRouter(prefix="/promos", tags=["Promotions"])

def get_promo_service(db: AsyncSession = Depends(get_db)) -> PromoService:
    promo_repo = PromotionRepositoryImpl(db)
    menu_repo = MenuItemRepositoryImpl(db)
    return PromoService(promo_repo, menu_repo)

@router.get("/active", response_model=List[PromoResponse])
async def get_active_promos(service: PromoService = Depends(get_promo_service)):
    """Pembeli: Melihat daftar promo yang sedang aktif hari ini."""
    promos = await service.list_active_promos()
    return [PromoResponse.from_domain(p) for p in promos]

@router.get("/my", response_model=List[PromoResponse])
async def get_my_promos(
    current_user_id: int = Depends(get_current_user_id),
    service: PromoService = Depends(get_promo_service)
):
    """Penjual: Melihat daftar promo yang pernah dibuat."""
    promos = await service.get_promos_by_umkm(owner_id=current_user_id)
    return [PromoResponse.from_domain(p) for p in promos]

@router.post("/", response_model=PromoResponse)
async def create_promotion(
    request: PromoCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: PromoService = Depends(get_promo_service)
):
    """Penjual: Mendaftarkan diskon produk baru."""
    promo = await service.create_promo(owner_id=current_user_id, request=request)
    return PromoResponse.from_domain(promo)

@router.patch("/{promo_id}/deactivate", response_model=PromoResponse)
async def deactivate_promotion(
    promo_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: PromoService = Depends(get_promo_service)
):
    """Penjual: Mematikan promo secara paksa."""
    promo = await service.deactivate_promo(promo_id=promo_id, owner_id=current_user_id)
    return PromoResponse.from_domain(promo)