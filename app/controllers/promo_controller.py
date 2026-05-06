# app/controllers/promo_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import require_seller
from app.schemas.promo_schema import PromoCreateRequest, PromoResponse
from app.services.promo_service import PromoService
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.core.exceptions import BusinessRuleViolationError, NotFoundError

router = APIRouter(prefix="/promos", tags=["Promotions"])

def get_promo_service(db: AsyncSession = Depends(get_db)) -> PromoService:
    """Dependency Injection merakit Repository dan Service"""
    promo_repo = PromotionRepositoryImpl(db)
    menu_repo = MenuItemRepositoryImpl(db)
    return PromoService(promo_repo, menu_repo)

@router.get("/active", response_model=List[PromoResponse])
async def get_active_promos(service: PromoService = Depends(get_promo_service)):
    """
    Menampilkan daftar promo yang sedang aktif hari ini.
    (Bisa diakses oleh Guest / Pembeli yang belum login)
    """
    promos = await service.list_active_promos()
    return [PromoResponse.from_domain(p) for p in promos]

@router.get("/my", response_model=List[PromoResponse])
async def get_my_promos(
    seller_payload: dict = Depends(require_seller),
    service: PromoService = Depends(get_promo_service)
):
    """Penjual: Melihat daftar promo yang pernah dibuat (KHUSUS PENJUAL)."""
    owner_id = int(seller_payload.get("sub"))
    promos = await service.get_promos_by_umkm(owner_id=owner_id)
    return [PromoResponse.from_domain(p) for p in promos]

@router.post("/", response_model=PromoResponse, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    request: PromoCreateRequest,
    seller_payload: dict = Depends(require_seller),
    service: PromoService = Depends(get_promo_service)
):
    """Penjual: Mendaftarkan diskon produk baru (KHUSUS PENJUAL)."""
    try:
        owner_id = int(seller_payload.get("sub"))
        promo = await service.create_promo(owner_id=owner_id, request=request)
        return PromoResponse.from_domain(promo)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{promo_id}/deactivate", response_model=PromoResponse)
async def deactivate_promotion(
    promo_id: int,
    seller_payload: dict = Depends(require_seller),
    service: PromoService = Depends(get_promo_service)
):
    """Penjual: Mematikan promo secara paksa (KHUSUS PENJUAL)."""
    try:
        owner_id = int(seller_payload.get("sub"))
        promo = await service.deactivate_promo(promo_id=promo_id, owner_id=owner_id)
        return PromoResponse.from_domain(promo)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))