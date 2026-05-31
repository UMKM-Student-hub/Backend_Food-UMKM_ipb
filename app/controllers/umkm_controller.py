from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user_id, require_seller
from app.schemas.umkm_schema import UMKMCreateRequest, UMKMResponse, OperatingHoursUpdate
from app.services.umkm_service import UMKMService
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.core.exceptions import NotFoundError, BusinessRuleViolationError

router = APIRouter(prefix="/umkm", tags=["UMKM Profile"])

def get_umkm_service(db: AsyncSession = Depends(get_db)) -> UMKMService:
    return UMKMService(umkm_repo=UMKMRepositoryImpl(db))

@router.post("/", response_model=UMKMResponse, status_code=status.HTTP_201_CREATED)
async def create_umkm(
    request: UMKMCreateRequest,
    owner_id: int = Depends(get_current_user_id),
    service: UMKMService = Depends(get_umkm_service),
):
    try:
        umkm = await service.create_umkm(owner_id, request)
        return UMKMResponse.from_domain(umkm)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/me", response_model=UMKMResponse)
async def get_my_store(
    current_user_id: int = Depends(get_current_user_id),
    service: UMKMService = Depends(get_umkm_service),
):
    try:
        umkm = await service.get_my_store(owner_id=current_user_id)
        return UMKMResponse.from_domain(umkm)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/me/operating-hours", response_model=UMKMResponse)
async def update_operating_hours(
    request: OperatingHoursUpdate,
    current_user_id: int = Depends(get_current_user_id),
    service: UMKMService = Depends(get_umkm_service),
):
    """
    Penjual mengatur jam & hari operasional kantin.
    Status buka/tutup akan dihitung otomatis dari jadwal ini.
    """
    try:
        umkm = await service.update_operating_hours(current_user_id, request)
        return UMKMResponse.from_domain(umkm)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{umkm_id}", response_model=UMKMResponse)
async def get_umkm_profile(
    umkm_id: int,
    service: UMKMService = Depends(get_umkm_service),
):
    try:
        umkm = await service.get_umkm_by_id(umkm_id)
        return UMKMResponse.from_domain(umkm)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/", response_model=List[UMKMResponse])
async def list_all_umkm(service: UMKMService = Depends(get_umkm_service)):
    umkms = await service.list_all_umkm()
    return [UMKMResponse.from_domain(u) for u in umkms]