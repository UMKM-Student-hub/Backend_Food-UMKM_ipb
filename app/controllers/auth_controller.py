from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ProfileResponse, ProfileUpdateRequest, UserUpdateRequest
from app.services.auth_service import AuthService
from app.repositories.impl.user_repository import UserRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.core.exceptions import BusinessRuleViolationError, NotFoundError

router = APIRouter(prefix="/auth", tags=["Autentikasi"])

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    user_repo = UserRepositoryImpl(db)
    umkm_repo = UMKMRepositoryImpl(db)
    return AuthService(user_repo, umkm_repo)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest, 
    service: AuthService = Depends(get_auth_service)
):
    try:
        user = await service.register(request)
        return UserResponse.from_domain(user)
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, 
    service: AuthService = Depends(get_auth_service)
):
    try:
        return await service.login(request)
    except (NotFoundError, BusinessRuleViolationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email atau password salah."
        )
        
@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
):
    user = await service.get_current_user(user_id)
    return UserResponse.from_domain(user)

@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
):
    update_data = request.model_dump(exclude_unset=True)
    user = await service.update_user_profile(user_id, update_data)
    return UserResponse.from_domain(user)

@router.get("/me/profile", response_model=ProfileResponse)
async def get_my_profile(
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
):
    return await service.get_seller_profile(user_id)

@router.patch("/me/profile", response_model=ProfileResponse)
async def update_my_profile(
    request: ProfileUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
):
    update_data = request.model_dump(exclude_unset=True)
    return await service.update_seller_profile(user_id, update_data)