from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.repositories.impl.user_repository import UserRepositoryImpl
from app.core.exceptions import BusinessRuleViolationError, NotFoundError

router = APIRouter(prefix="/auth", tags=["Autentikasi"])

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    user_repo = UserRepositoryImpl(db)
    return AuthService(user_repo)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest, 
    service: AuthService = Depends(get_auth_service)
):
    """Mendaftarkan pengguna baru (Pembeli atau Penjual)."""
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
    """Proses Login untuk mendapatkan token akses (Bearer Token)."""
    try:
        return await service.login(request)
    except (NotFoundError, BusinessRuleViolationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email atau password salah."
        )
        
@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service)
):
    """Mengambil data profil user yang sedang login."""
    user = await service.get_current_user(user_id)
    return UserResponse.from_domain(user)