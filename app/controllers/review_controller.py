from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.review_schema import ReviewCreateRequest, ReviewResponse
from app.services.review_service import ReviewService
from app.repositories.impl.review_repository import ReviewRepositoryImpl
from app.repositories.impl.order_repository import OrderRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.core.exceptions import BusinessRuleViolationError, NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/reviews", tags=["Rating & Review"])

def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    review_repo = ReviewRepositoryImpl(db)
    order_repo = OrderRepositoryImpl(db)
    umkm_repo = UMKMRepositoryImpl(db)
    return ReviewService(review_repo=review_repo, order_repo=order_repo, umkm_repo=umkm_repo)

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    request: ReviewCreateRequest,
    buyer_id: int = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service)
):
    try:
        review = await service.submit_review(buyer_id=buyer_id, request=request)
        return ReviewResponse.from_domain(review)
    except (BusinessRuleViolationError, PermissionDeniedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/product/{menu_item_id}", response_model=List[ReviewResponse])
async def get_product_reviews(
    menu_item_id: int,
    service: ReviewService = Depends(get_review_service)
):
    reviews = await service.get_product_reviews(menu_item_id)
    return [ReviewResponse.from_domain(r) for r in reviews]

@router.get("/umkm/my", response_model=List[ReviewResponse])
async def get_my_umkm_reviews(
    owner_id: int = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service)
):
    reviews = await service.get_umkm_reviews(owner_id)
    return [ReviewResponse.from_domain(r) for r in reviews]