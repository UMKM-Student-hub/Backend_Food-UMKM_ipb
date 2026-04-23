from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user_schema import UserRegisterRequest, UserResponse
from app.services.user_service import UserService
from app.repositories.impl.user_repository import UserRepositoryImpl

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepositoryImpl(db)
    return UserService(repo)

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegisterRequest,
    service: UserService = Depends(get_user_service)
):
    user = await service.register_user(request=request)
    return UserResponse.from_domain(user)