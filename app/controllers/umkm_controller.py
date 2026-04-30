from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.umkm_schema import UMKMCreateRequest, UMKMResponse
from app.services.umkm_service import UMKMService
from app.core.dependencies import get_current_user_id
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl

router = APIRouter(prefix="/umkm", tags=["UMKM"])

def get_umkm_service(db: AsyncSession = Depends(get_db)) -> UMKMService:
    repo = UMKMRepositoryImpl(db)
    return UMKMService(repo)

@router.post("/", response_model=UMKMResponse)
async def create_umkm(
    request: UMKMCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: UMKMService = Depends(get_umkm_service)
):
    umkm = await service.register_umkm(owner_id=current_user_id, request=request)
    return UMKMResponse.from_domain(umkm)

@router.patch("/{id}/toggle-status", response_model=UMKMResponse)
async def toggle_umkm_status(
    id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: UMKMService = Depends(get_umkm_service)
):
    umkm = await service.toggle_status(umkm_id=id, requester_id=current_user_id)
    return UMKMResponse.from_domain(umkm)