from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import require_seller
from app.schemas.promo_schema import PromoResponse
from app.services.promo_service import PromoService
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.core.exceptions import BusinessRuleViolationError, NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/promos", tags=["Promotions"])

def get_promo_service(db: AsyncSession = Depends(get_db)) -> PromoService:
    promo_repo = PromotionRepositoryImpl(db)
    menu_repo = MenuItemRepositoryImpl(db)
    umkm_repo = UMKMRepositoryImpl(db)
    return PromoService(promo_repo, menu_repo, umkm_repo)

@router.get("/active", response_model=List[PromoResponse])
async def get_active_promos(service: PromoService = Depends(get_promo_service)):
    promos = await service.list_active_promos()
    return [PromoResponse.from_domain(p) for p in promos]

@router.get("/my", response_model=List[PromoResponse])
async def get_my_promotions(
    seller_payload: dict = Depends(require_seller),
    service: PromoService = Depends(get_promo_service)
):
    try:
        owner_id = int(seller_payload.get("sub"))
        promos = await service.get_promos_by_umkm(owner_id)
        return [PromoResponse.from_domain(p) for p in promos]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/", response_model=PromoResponse, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    menu_item_id: int = Form(...),
    name: str = Form(...),
    discount_type: str = Form(...),
    discount_value: Decimal = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    photo: Optional[UploadFile] = File(None),
    seller_payload: dict = Depends(require_seller),
    service: PromoService = Depends(get_promo_service)
):
    try:
        owner_id = int(seller_payload.get("sub"))
        promo = await service.create_promo_with_file(
            owner_id=owner_id,
            menu_item_id=menu_item_id,
            name=name,
            discount_type=discount_type,
            discount_value=discount_value,
            start_date=start_date,
            end_date=end_date,
            photo=photo
        )
        return PromoResponse.from_domain(promo)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{promo_id}/deactivate", response_model=PromoResponse)
async def deactivate_promotion(
    promo_id: int,
    seller_payload: dict = Depends(require_seller),
    service: PromoService = Depends(get_promo_service)
):
    try:
        owner_id = int(seller_payload.get("sub"))
        promo = await service.deactivate_promo(promo_id=promo_id, owner_id=owner_id)
        return PromoResponse.from_domain(promo)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))