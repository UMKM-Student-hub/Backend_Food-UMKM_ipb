from fastapi import APIRouter, Depends, HTTPException, Query, status, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user_token, require_seller
from app.schemas.order_schema import OrderResponse
from app.services.order_service import OrderService
from app.repositories.impl.order_repository import OrderRepositoryImpl
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.core.exceptions import BusinessRuleViolationError, NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    order_repo = OrderRepositoryImpl(db)
    menu_repo = MenuItemRepositoryImpl(db)
    umkm_repo = UMKMRepositoryImpl(db)
    promo_repo = PromotionRepositoryImpl(db)
    return OrderService(order_repo, menu_repo, umkm_repo, promo_repo)

async def require_buyer(payload: dict = Depends(get_current_user_token)) -> dict:
    if payload.get("role") != "BUYER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Hanya akun pembeli yang dapat melakukan pesanan."
        )
    return payload

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    umkm_id: int = Form(...),
    items: str = Form(...),
    payment_method: str = Form(...),
    notes: str = Form(""),
    pickup_schedule: str = Form(None),
    payment_proof: UploadFile = File(None),
    buyer_payload: dict = Depends(require_buyer),
    service: OrderService = Depends(get_order_service)
):
    try:
        buyer_id = int(buyer_payload.get("sub"))
        order = await service.place_order(
            buyer_id=buyer_id,
            umkm_id=umkm_id,
            items_json=items,
            payment_method=payment_method,
            notes=notes,
            pickup_schedule=pickup_schedule,
            payment_proof=payment_proof
        )
        return OrderResponse.from_domain(order)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/my", response_model=List[OrderResponse])
async def get_my_orders(
    buyer_payload: dict = Depends(require_buyer),
    service: OrderService = Depends(get_order_service)
):
    buyer_id = int(buyer_payload.get("sub"))
    orders = await service.get_buyer_orders(buyer_id=buyer_id)
    return [OrderResponse.from_domain(o) for o in orders]

@router.patch("/{order_id}/done", response_model=OrderResponse)
async def mark_order_done(
    order_id: int,
    buyer_payload: dict = Depends(require_buyer),
    service: OrderService = Depends(get_order_service)
):
    try:
        buyer_id = int(buyer_payload.get("sub"))
        order = await service.mark_order_done(order_id=order_id, buyer_id=buyer_id)
        return OrderResponse.from_domain(order)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/incoming", response_model=List[OrderResponse])
async def get_incoming_orders(
    seller_payload: dict = Depends(require_seller),
    service: OrderService = Depends(get_order_service)
):
    owner_id = int(seller_payload.get("sub"))
    orders = await service.get_umkm_orders(owner_id=owner_id)
    return [OrderResponse.from_domain(o) for o in orders]

@router.patch("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: int,
    seller_payload: dict = Depends(require_seller),
    service: OrderService = Depends(get_order_service)
):
    try:
        owner_id = int(seller_payload.get("sub"))
        order = await service.confirm_order(order_id=order_id, owner_id=owner_id)
        return OrderResponse.from_domain(order)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch("/{order_id}/reject", response_model=OrderResponse)
async def reject_order(
    order_id: int,
    reason: str = Query(..., min_length=5),
    seller_payload: dict = Depends(require_seller),
    service: OrderService = Depends(get_order_service)
):
    try:
        owner_id = int(seller_payload.get("sub"))
        order = await service.reject_order(order_id=order_id, owner_id=owner_id, reason=reason)
        return OrderResponse.from_domain(order)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch("/{order_id}/ready", response_model=OrderResponse)
async def mark_order_ready(
    order_id: int,
    seller_payload: dict = Depends(require_seller),
    service: OrderService = Depends(get_order_service)
):
    try:
        owner_id = int(seller_payload.get("sub"))
        order = await service.mark_order_ready(order_id=order_id, owner_id=owner_id)
        return OrderResponse.from_domain(order)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))